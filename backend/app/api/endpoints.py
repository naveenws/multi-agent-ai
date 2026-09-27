from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from typing import List, Dict, Any

from app.database.db import get_session
from app.models.core import Task, Agent, FinalResponse, AgentExecution, Evaluation, AgentFailure
from app.schemas.core import TaskCreate, TaskResponse, AgentResponse
from app.orchestrator.executor import TaskExecutor
from app.orchestrator.registry import agent_registry

router = APIRouter()
executor = TaskExecutor()

@router.post("/tasks", response_model=Dict[str, Any])
async def create_task(request: TaskCreate, session: Session = Depends(get_session)):
    # Create Task in DB
    db_task = Task(original_prompt=request.prompt, status="analyzing")
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    
    # Execute full pipeline (async)
    # Note: In a real prod environment, you'd use Celery/BackgroundTasks. 
    # For this project, we'll await it to send back the full result immediately.
    try:
        result = await executor.execute_task(request.prompt)
        
        db_task.status = "completed"
        session.add(db_task)
        
        final_response = FinalResponse(task_id=db_task.id, response_text=result["final_answer"])
        session.add(final_response)
        
        session.commit()
        
        return {
            "task_id": db_task.id,
            "final_answer": result["final_answer"],
            "trace": result["trace"]
        }
    except Exception as e:
        db_task.status = "failed"
        session.add(db_task)
        session.commit()
        raise HTTPException(status_code=500, detail=str(e))

from sqlalchemy import func

@router.get("/dashboard/statistics")
def get_statistics(session: Session = Depends(get_session)):
    total_tasks = session.exec(select(func.count(Task.id))).first()
    successful_tasks = session.exec(select(func.count(Task.id)).where(Task.status == "completed")).first()
    failed_tasks = session.exec(select(func.count(Task.id)).where(Task.status == "failed")).first()
    
    total_agent_executions = session.exec(select(func.count(AgentExecution.id))).first()
    fallback_executions = session.exec(select(func.count(AgentFailure.id)).where(AgentFailure.is_fallback_triggered == True)).first()
    
    avg_latency = session.exec(select(func.avg(AgentExecution.latency)).where(AgentExecution.latency != None)).first()
    
    evaluations = session.exec(select(Evaluation.quality_score)).all()
    avg_quality = sum(evaluations) / len(evaluations) if evaluations else 0.0
    
    success_rate = (successful_tasks / total_tasks * 100) if total_tasks and total_tasks > 0 else None
    fallback_rate = (fallback_executions / total_agent_executions * 100) if total_agent_executions and total_agent_executions > 0 else None
    
    active_agents = session.exec(select(func.count(Agent.id)).where(Agent.is_active == True)).first()

    return {
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "failed_tasks": failed_tasks,
        "success_rate": success_rate,
        "fallback_rate": fallback_rate,
        "average_latency": avg_latency,
        "average_quality": avg_quality,
        "active_agents": active_agents
    }
    
@router.get("/dashboard/recent-executions")
def get_recent_executions(session: Session = Depends(get_session)):
    # Fetch recent tasks
    tasks = session.exec(select(Task).order_by(Task.created_at.desc()).limit(10)).all()
    result = []
    for t in tasks:
        # Get agents used for this task
        executions = session.exec(select(AgentExecution).where(AgentExecution.task_id == t.id)).all()
        agent_ids = list(set([e.agent_id for e in executions]))
        
        # Get agent names
        agents_used = []
        for aid in agent_ids:
            a = session.get(Agent, aid)
            if a:
                agents_used.append(a.name)
                
        # Calculate latency for the task
        task_latency = sum([e.latency for e in executions if e.latency])
        
        # Get final quality if evaluated
        last_eval = None
        if executions:
            last_exec = executions[-1]
            last_eval = session.exec(select(Evaluation).where(Evaluation.execution_id == last_exec.id)).first()
            
        result.append({
            "id": t.id,
            "prompt": t.original_prompt,
            "type": t.task_type or "General",
            "agents_used": agents_used,
            "status": t.status,
            "latency": task_latency,
            "quality": last_eval.quality_score if last_eval else None,
            "created_at": t.created_at
        })
    return result

@router.get("/agents", response_model=List[Dict[str, Any]])
def get_db_agents(session: Session = Depends(get_session)):
    agents = session.exec(select(Agent)).all()
    result = []
    for a in agents:
        caps = [c.capability_name for c in a.capabilities]
        
        # Calculate real performance stats
        executions = session.exec(select(AgentExecution).where(AgentExecution.agent_id == a.id)).all()
        total_execs = len(executions)
        
        if total_execs == 0:
            result.append({
                "id": a.id,
                "name": a.name,
                "provider": a.provider,
                "model": a.model,
                "capabilities": caps,
                "is_active": a.is_active,
                "executions": 0,
                "success_rate": None,
                "average_latency": None,
                "quality_score": None
            })
            continue
            
        success_execs = len([e for e in executions if e.status == "completed"])
        success_rate = (success_execs / total_execs) * 100
        
        latencies = [e.latency for e in executions if e.latency is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        
        eval_scores = []
        fallback_count = 0
        for e in executions:
            ev = session.exec(select(Evaluation).where(Evaluation.execution_id == e.id)).first()
            if ev:
                eval_scores.append(ev.quality_score)
            f = session.exec(select(AgentFailure).where(AgentFailure.execution_id == e.id, AgentFailure.is_fallback_triggered == True)).first()
            if f:
                fallback_count += 1
                
        avg_quality = sum(eval_scores) / len(eval_scores) if eval_scores else None

        result.append({
            "id": a.id,
            "name": a.name,
            "provider": a.provider,
            "model": a.model,
            "capabilities": caps,
            "is_active": a.is_active,
            "executions": total_execs,
            "success_rate": success_rate,
            "average_latency": avg_latency,
            "quality_score": avg_quality,
            "fallback_count": fallback_count
        })
    return result

from app.models.core import AgentCapability, AgentCredential
from app.core.security import encrypt_credential
from app.providers.adapters import get_adapter

@router.get("/providers")
def get_supported_providers():
    return {
        "providers": [
            {
                "id": "openai",
                "name": "OpenAI",
                "requires_api_key": True,
                "requires_base_url": False
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "requires_api_key": True,
                "requires_base_url": False
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "requires_api_key": True,
                "requires_base_url": False
            },
            {
                "id": "openrouter",
                "name": "OpenRouter",
                "requires_api_key": True,
                "requires_base_url": False
            },
            {
                "id": "groq",
                "name": "Groq",
                "requires_api_key": True,
                "requires_base_url": False
            },
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "requires_api_key": False,
                "requires_base_url": True,
                "default_base_url": "http://localhost:11434"
            },
            {
                "id": "custom",
                "name": "Custom OpenAI-Compatible",
                "requires_api_key": True,
                "requires_base_url": True
            }
        ]
    }

@router.post("/providers/test")
async def test_provider_connection(data: dict):
    provider_name = data.get("provider", "")
    api_key = data.get("api_key")
    base_url = data.get("base_url")
    
    adapter = get_adapter(provider_name, api_key=api_key, base_url=base_url)
    res = await adapter.test_connection()
    return res
    
@router.post("/providers/models")
async def get_provider_models(data: dict):
    provider_name = data.get("provider", "")
    api_key = data.get("api_key")
    base_url = data.get("base_url")
    
    adapter = get_adapter(provider_name, api_key=api_key, base_url=base_url)
    models = await adapter.get_models()
    return {"models": models}

@router.post("/agents")
def create_agent(agent_data: dict, session: Session = Depends(get_session)):
    credential_id = None
    
    # Store credential securely if provided
    api_key = agent_data.get("api_key")
    base_url = agent_data.get("base_url")
    if api_key or base_url:
        encrypted_key = encrypt_credential(api_key) if api_key else None
        cred = AgentCredential(encrypted_api_key=encrypted_key, base_url=base_url)
        session.add(cred)
        session.commit()
        session.refresh(cred)
        credential_id = cred.id

    db_agent = Agent(
        name=agent_data.get("name"),
        provider=agent_data.get("provider", "Gemini"),
        model=agent_data.get("model", "gemini-3.8-flash"),
        credential_id=credential_id,
        is_active=agent_data.get("is_active", True)
    )
    session.add(db_agent)
    session.commit()
    session.refresh(db_agent)
    
    for cap in agent_data.get("capabilities", []):
        db_cap = AgentCapability(agent_id=db_agent.id, capability_name=cap)
        session.add(db_cap)
    session.commit()
    
    return {"message": "Agent created successfully", "id": db_agent.id}

@router.put("/agents/{agent_id}")
def update_agent(agent_id: int, agent_data: dict, session: Session = Depends(get_session)):
    db_agent = session.get(Agent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    if "is_active" in agent_data:
        db_agent.is_active = agent_data["is_active"]
    if "name" in agent_data:
        db_agent.name = agent_data["name"]
    if "provider" in agent_data:
        db_agent.provider = agent_data["provider"]
    if "model" in agent_data:
        db_agent.model = agent_data["model"]
        
    # Update capabilities
    if "capabilities" in agent_data:
        for cap in db_agent.capabilities:
            session.delete(cap)
        for cap in agent_data["capabilities"]:
            session.add(AgentCapability(agent_id=db_agent.id, capability_name=cap))
            
    # Update credential if provided
    api_key = agent_data.get("api_key")
    base_url = agent_data.get("base_url")
    if api_key or base_url is not None:
        if db_agent.credential_id:
            cred = session.get(AgentCredential, db_agent.credential_id)
            if api_key:
                cred.encrypted_api_key = encrypt_credential(api_key)
            if base_url is not None:
                cred.base_url = base_url
            session.add(cred)
        else:
            encrypted_key = encrypt_credential(api_key) if api_key else None
            cred = AgentCredential(encrypted_api_key=encrypted_key, base_url=base_url)
            session.add(cred)
            session.commit()
            session.refresh(cred)
            db_agent.credential_id = cred.id
            
    session.add(db_agent)
    session.commit()
    return {"message": "Agent updated successfully"}

@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: int, session: Session = Depends(get_session)):
    db_agent = session.get(Agent, agent_id)
    if not db_agent:
        return {"message": "Agent already deleted"}
        
    try:
        # Delete capabilities
        for cap in db_agent.capabilities:
            session.delete(cap)
        session.flush()
            
        # Delete executions and their children (evaluations, failures)
        executions = session.exec(select(AgentExecution).where(AgentExecution.agent_id == agent_id)).all()
        
        # Step 1: Delete all dependent children first to prevent Postgres foreign key violations
        for ex in executions:
            evals = session.exec(select(Evaluation).where(Evaluation.execution_id == ex.id)).all()
            for ev in evals:
                session.delete(ev)
            fails = session.exec(select(AgentFailure).where(AgentFailure.execution_id == ex.id)).all()
            for f in fails:
                session.delete(f)
        
        session.flush() # Force physical deletion of children
        
        # Step 2: Delete executions now that their children are gone
        for ex in executions:
            session.delete(ex)
            
        session.flush() # Force physical deletion of executions
            
        credential_id_to_delete = db_agent.credential_id
        
        # Step 3: Delete the Agent itself
        session.delete(db_agent)
        session.flush() # Force Postgres to remove the agent row so it releases the foreign key on AgentCredential
        
        # Step 4: Delete the credential now that the agent doesn't reference it
        if credential_id_to_delete:
            cred = session.get(AgentCredential, credential_id_to_delete)
            if cred:
                session.delete(cred)
                
        session.commit()
        return {"message": "Agent and its history deleted permanently"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during deletion: {str(e)}")

@router.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    # Dummy file upload for now
    content = await file.read()
    text_content = content.decode('utf-8', errors='ignore')
    return {"filename": file.filename, "content": text_content[:1000] + ("..." if len(text_content) > 1000 else "")}
