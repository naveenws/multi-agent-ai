import json
import time
from typing import Dict, Any, Optional, List
from app.orchestrator.analyzer import TaskAnalyzer
from app.orchestrator.selector import AgentSelector
from app.orchestrator.registry import agent_registry
from app.agents.base import BaseAgent
from app.database.db import get_session
from sqlmodel import select
from app.models.core import Task, Agent, AgentExecution, Evaluation, AgentFailure

def is_quota_error(error_str: str) -> bool:
    e = error_str.lower()
    return any(x in e for x in ["429", "quota", "resource_exhausted", "rate limit", "rate_limit", "api key"])

class TaskExecutor:
    def __init__(self):
        self.analyzer = TaskAnalyzer()
        self.selector = AgentSelector()
        
    def _get_agent_from_db(self, name: str) -> Optional[BaseAgent]:
        from app.database.db import get_session
        from sqlmodel import select
        from app.models.core import Agent
        from app.agents.dynamic import DynamicAgent
        
        with next(get_session()) as session:
            db_agent = session.exec(select(Agent).where(Agent.name == name)).first()
            if db_agent:
                return DynamicAgent(
                    name=db_agent.name,
                    capabilities=[c.capability_name for c in db_agent.capabilities],
                    provider_name=db_agent.provider,
                    model_name=db_agent.model,
                    credential_id=db_agent.credential_id
                )
        return None

    async def _run_with_fallback(self, agent_name: str, required_caps: List[str], execute_func, trace: list, excluded_providers: list) -> str:
        """Helper to run an agent function with fallback for Quota/API errors."""
        excluded_agents = []
        attempts = 0
        max_attempts = 3
        
        current_agent = self._get_agent_from_db(agent_name)
        if current_agent and hasattr(current_agent, "provider_name") and current_agent.provider_name in excluded_providers:
            current_agent = None

        if not current_agent:
            current_agent = self.selector.select_agent(required_caps, excluded_providers=excluded_providers)
            if not current_agent:
                return "Error: No agents available."

        while attempts < max_attempts:
            attempts += 1
            try:
                result = await execute_func(current_agent)
                return result
            except Exception as e:
                error_str = str(e)
                trace.append({"step": f"Fallback ({current_agent.name})", "status": "failed", "error": error_str})
                
                excluded_agents.append(current_agent.name)
                if hasattr(current_agent, "provider_name") and is_quota_error(error_str):
                    if current_agent.provider_name not in excluded_providers:
                        excluded_providers.append(current_agent.provider_name)
                        
                next_agent = self.selector.select_agent(required_caps, excluded_agents=excluded_agents, excluded_providers=excluded_providers)
                if not next_agent:
                    return f"Error executing {agent_name}: {error_str} (No alternative agents available)"
                current_agent = next_agent
        return "Error: Max fallback attempts reached."

    async def execute_task(self, original_prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes the full orchestration pipeline.
        Returns the final response and execution trace.
        """
        trace = []
        excluded_providers = []
        
        # 1. Analyze Task
        trace.append({"step": "Analysis", "status": "running"})
        try:
            analysis_result = await self.analyzer.analyze(original_prompt)
        except Exception as e:
            if is_quota_error(str(e)):
                # If Gemini default provider hits quota in analyzer, just use a fallback dict 
                # and exclude Gemini from the rest of the orchestration!
                excluded_providers.append("Gemini")
            analysis_result = {
                "task_type": "General",
                "complexity": "low",
                "required_capabilities": ["information gathering"],
                "requires_multiple_agents": False,
                "requires_verification": False,
                "error": f"Failed to parse LLM analysis: {str(e)}"
            }
        trace[-1].update({"status": "completed", "result": analysis_result})
        
        required_caps = analysis_result.get("required_capabilities", [])
        
        # 2. Select Primary Agent
        trace.append({"step": "Agent Selection", "status": "running"})
        primary_agent = self.selector.select_agent(required_caps, excluded_providers=excluded_providers)
        if not primary_agent:
            # Fallback to general agent
            primary_agent = self._get_agent_from_db("Research Agent") or agent_registry.get_agent("Research Agent")
        
        if primary_agent:
            trace[-1].update({"status": "completed", "selected_agent": primary_agent.name})
        else:
            trace[-1].update({"status": "failed", "error": "No agents available"})
            return {"final_answer": "System Error: No valid agents available to execute this task.", "trace": trace}
            
        # 3. Execution & Evaluation Loop
        max_attempts = 3
        attempts = 0
        current_agent = primary_agent
        excluded_agents = []
        final_agent_response = None
        
        with next(get_session()) as session:
            db_task = session.exec(select(Task).where(Task.original_prompt == original_prompt)).first()
            task_id = db_task.id if db_task else 1
            
            while attempts < max_attempts:
                attempts += 1
                trace.append({"step": f"Execution ({current_agent.name})", "status": "running", "attempt": attempts})
                
                db_agent = session.exec(select(Agent).where(Agent.name == current_agent.name)).first()
                agent_id = db_agent.id if db_agent else 1
                
                db_exec = AgentExecution(task_id=task_id, agent_id=agent_id, prompt=original_prompt, status="started")
                session.add(db_exec)
                session.commit()
                session.refresh(db_exec)
                
                start_time = time.time()
                try:
                    agent_response = await current_agent.execute(original_prompt, context)
                    latency = time.time() - start_time
                    trace[-1].update({"status": "completed", "latency": latency})
                    
                    db_exec.status = "completed"
                    db_exec.response = agent_response
                    db_exec.latency = latency
                    session.add(db_exec)
                    
                    # Evaluate - using _run_with_fallback
                    trace.append({"step": "Evaluation", "status": "running"})
                    
                    async def run_critic(critic):
                        eval_context = {"original_task": original_prompt, "agent_response": agent_response}
                        return await critic.execute(original_prompt, eval_context)
                        
                    eval_json = await self._run_with_fallback("Critic Agent", ["reasoning", "evaluation"], run_critic, trace, excluded_providers)
                    
                    try:
                        evaluation = json.loads(eval_json)
                    except json.JSONDecodeError:
                        evaluation = {"quality_score": 0.0, "needs_retry": True, "error": "Failed to parse eval", "completeness_score": 0, "relevance_score": 0, "confidence": 0, "has_major_errors": True}
                        
                    trace[-1].update({"status": "completed", "evaluation": evaluation})
                    
                    db_eval = Evaluation(
                        execution_id=db_exec.id,
                        quality_score=evaluation.get("quality_score", 0.0),
                        completeness_score=evaluation.get("completeness_score", 0.0),
                        relevance_score=evaluation.get("relevance_score", 0.0),
                        confidence=evaluation.get("confidence", 0.0),
                        has_major_errors=evaluation.get("has_major_errors", False),
                        needs_retry=evaluation.get("needs_retry", False),
                        issues=json.dumps(evaluation.get("issues", []))
                    )
                    session.add(db_eval)
                    session.commit()
                    
                    if evaluation.get("needs_retry", False) or evaluation.get("quality_score", 0.0) < 0.75:
                        db_fail = AgentFailure(execution_id=db_exec.id, error_message="Low evaluation score", is_fallback_triggered=True)
                        session.add(db_fail)
                        session.commit()
                        
                        excluded_agents.append(current_agent.name)
                        trace.append({"step": "Fallback", "status": "running", "reason": "Low evaluation score"})
                        next_agent = self.selector.select_agent(required_caps, excluded_agents=excluded_agents, excluded_providers=excluded_providers)
                        if not next_agent:
                            trace[-1].update({"status": "failed", "error": "No alternative agents available"})
                            final_agent_response = agent_response 
                            break
                        
                        current_agent = next_agent
                        trace[-1].update({"status": "completed", "next_agent": current_agent.name})
                        continue
                    else:
                        final_agent_response = agent_response
                        break
                        
                except Exception as e:
                    error_str = str(e)
                    latency = time.time() - start_time
                    trace[-1].update({"status": "failed", "error": error_str, "latency": latency})
                    
                    db_exec.status = "failed"
                    db_exec.latency = latency
                    session.add(db_exec)
                    db_fail = AgentFailure(execution_id=db_exec.id, error_message=error_str, is_fallback_triggered=True)
                    session.add(db_fail)
                    session.commit()
                    
                    excluded_agents.append(current_agent.name)
                    if hasattr(current_agent, "provider_name") and is_quota_error(error_str):
                        if current_agent.provider_name not in excluded_providers:
                            excluded_providers.append(current_agent.provider_name)
                    
                    next_agent = self.selector.select_agent(required_caps, excluded_agents=excluded_agents, excluded_providers=excluded_providers)
                    if not next_agent:
                        final_agent_response = f"Error executing agents: {error_str}"
                        break
                    current_agent = next_agent
                    continue
                
        # 4. Synthesize
        trace.append({"step": "Synthesis", "status": "running"})
        
        async def run_synth(synth):
            synth_context = {
                "agent_outputs": [{"agent_name": current_agent.name, "output": final_agent_response}]
            }
            return await synth.execute(original_prompt, synth_context)
            
        final_answer = await self._run_with_fallback("Synthesis Agent", ["summarization", "writing"], run_synth, trace, excluded_providers)
        trace[-1].update({"status": "completed"})
        
        return {
            "final_answer": final_answer,
            "trace": trace
        }
