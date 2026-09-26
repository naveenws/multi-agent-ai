# Adaptive Multi-Agent AI Orchestration System

## 1. Project Overview
This project is an advanced, production-quality **Adaptive Multi-Agent AI Orchestration System** designed for a 3rd-year Artificial Intelligence & Data Science academic project. It features dynamic agent selection, automatic fallback mechanisms upon failure or poor performance, automated evaluation (Critic Agent), and final response synthesis.

## 2. Problem Statement
Single-agent AI systems often fail on complex tasks that require multiple domains of reasoning (e.g., coding, data analysis, and factual research) or suffer from hallucinations without self-correction mechanisms. A single LLM call is brittle, lacks verification, and cannot seamlessly adapt if it provides a sub-par answer.

## 3. Objectives
- Dynamically classify user intent and break it down into requirements.
- Select the most appropriate specialized agent based on capabilities and historical performance scores.
- Evaluate the agent's output automatically.
- Provide a robust fallback mechanism to re-route requests to an alternative agent if the primary agent fails or produces low-quality output.
- Synthesize all outputs into a single cohesive response.
- Provide a visual trace and analytics dashboard.

## 4. Features
- **Task Analyzer**: Uses LLMs to classify complex tasks into required capabilities.
- **Dynamic Selection Engine**: Ranks agents using a weighted formula (capabilities, historical quality, latency, etc.).
- **Multiple Specialized Agents**: Research Agent, Data Analysis Agent, Coding Agent, Critic Agent, Synthesis Agent.
- **Evaluator/Critic**: Automatically scores responses (0.0 to 1.0) and triggers fallbacks for scores < 0.75.
- **Full Traceability**: React frontend visualizes every step (Analysis -> Selection -> Execution -> Evaluation -> Fallback -> Synthesis).
- **Dashboard**: Live analytics of agent success rates and latencies.

## 5. Architecture
User -> React Frontend -> FastAPI Backend -> Orchestrator (Analyzer -> Planner -> Selector -> Executor loop (with Evaluator/Fallback) -> Synthesizer) -> Final Response

## 6. Technology Stack
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Lucide React
- **Backend**: Python, FastAPI, Pydantic, async/await
- **Database**: SQLModel with SQLite for local development (PostgreSQL ready via `DATABASE_URL`)
- **AI Integration**: Google Gemini API via official SDK, OpenAI support included (abstracted LLM Provider).

## 7. Installation & Running Locally

### Prerequisites
- Python 3.9+
- Node.js 18+

### Backend Setup
1. Open terminal and navigate to `backend/`
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install fastapi uvicorn sqlmodel aiosqlite pydantic pydantic-settings python-dotenv google-genai openai anthropic python-multipart httpx
   ```
4. Create a `.env` file in the `backend/` directory based on `.env.example` and add your API keys (e.g., `GEMINI_API_KEY=your_key`).
5. Run the server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Frontend Setup
1. Open terminal and navigate to `frontend/`
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
4. Open your browser to `http://localhost:5173`.

## 8. Agent Architecture & Selection Algorithm
The `AgentSelector` scores agents using the formula:
`Score = (Capability Match * 0.40) + (Quality Score * 0.25) + (Success Rate * 0.20) + (Priority * 0.10) - (Latency * 0.03) - (Cost * 0.02)`

## 9. Fallback & Evaluation Mechanism
The `CriticAgent` evaluates the selected agent's response in a strict JSON format. If `needs_retry` is true or `quality_score < 0.75`, the system records an `AgentFailure` in the database, adds the current agent to an exclusion list, selects the next best agent, and retries the execution.

## 10. Database
The system uses `SQLModel` to store `Task`, `AgentExecution`, `Evaluation`, and `AgentFailure` to provide deep analytics and persistent trace history.
