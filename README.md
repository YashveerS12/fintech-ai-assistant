# 🏦 Fintech AI Assistant

AI-powered assistant for fintech domain built with LangChain, FAISS, HuggingFace & Groq LLM.

## Projects

### 1. Fintech QA Assistant
RAG-based Q&A system trained on fintech knowledge base.
Ask anything about AEPS, UPI, DMT, NPCI, RapiPay, PhonePe.

### 2. Loan MIS Assistant
Natural language to MongoDB query engine.
Ask management questions in plain English — AI converts to MongoDB query and returns business summary.

## Tech Stack
- **LangChain** — AI application framework
- **Groq LLM** — llama-3.3-70b-versatile model
- **FAISS** — Vector similarity search
- **HuggingFace** — sentence-transformers embeddings
- **MongoDB** — Loan portfolio database
- **Python** — Core language

## Setup

```bash
# clone repo
git clone https://github.com/YashveerS12/fintech-ai-assistant.git

# create virtual environment
python3 -m venv venv
source venv/bin/activate

# install dependencies
pip install langchain-groq langchain-community langchain-text-splitters
pip install faiss-cpu sentence-transformers langchain-huggingface
pip install pymongo python-dotenv
```

## Usage

Create `.env` file:
