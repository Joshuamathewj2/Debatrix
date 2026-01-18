# Debatrix MVP - AI-Powered Debate & Critical Thinking

Debatrix is a structured debate system where you challenge an AI ("Critical Debater") on complex topics. The AI takes a firm stance, uses RAG-retrieved evidence, and maintains logical discipline.

## 🚀 Features
- **Rigorous AI Persona**: Sharp, evidence-backed arguments with a clear stance.
- **RAG Integration**: AI relies on retrieved documents for claims.
- **Structured Response**: Section-wise streaming (Position, Arguments, Counter, Question).
- **Futuristic UI**: High-contrast, dark mode interface with glassmorphism effects.
- **Streaming Stability**: Frontend state machine for jitter-free real-time responses.

## 🛠 Tech Stack
- **Frontend**: Next.js 14, Tailwind CSS, TypeScript.
- **Backend**: FastAPI, Python 3.10+.
- **LLM**: Anthropic Claude 3.5 Sonnet.

## 📂 Project Structure
```
/backend
  ├── main.py            # API Entry point
  ├── debate_engine.py   # Orchestration & stance-drift checks
  ├── prompts.py         # Modular prompt templates
  ├── rag.py             # Mock RAG pipeline with metadata
  ├── llm.py             # Claude API integration
  └── requirements.txt
/frontend
  ├── app/page.tsx       # Debate UI & State Machine
  ├── lib/parser.ts      # AI Stream Parser
  └── app/globals.css    # Design System
```

## 🏗 Setup & Run

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```
- Create a `.env` file in `/backend` and add your `ANTHROPIC_API_KEY`.
- Run the server: `python main.py` (Starts on port 8000).

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Open [http://localhost:3000](http://localhost:3000).

## 🔮 Future Phases (TODOs)
- [ ] **Fallacy Detection**: Highlight logical fallacies in user arguments.
- [ ] **Persona Switching**: Choose between different debater characters (e.g., Socratic, Aggressive).
- [ ] **Real Vector DB**: Replace mock RAG with Pinecone or Weaviate.
- [ ] **Debate Scoring**: AI scores the user's reasoning at the end of a session.

## ⚖️ License
MIT
