# Webapp Setup Guide

This guide provides two options for setting up and running the webapp: using Docker or manual setup.

## Option 1: Manual Setup

### Prerequisites

- Git
- Python 3.8+
- Anaconda Environment(preffered)

### Setup Instructions

1. Clone the Repository

```bash
git clone https://github.com/navi-0115/local-rag-linux.git
cd local-rag-linux
```

2. Install Ollama

```bash
curl https://ollama.ai/install.sh | sh
```

3. Pull and Run Gemma Model

```bash
ollama pull gemma3:4b
ollama pull nomic-embed-text
```

4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

5. Start Backend Server (in one terminal)

```bash
cd backend
uvicorn api:app
```

6. Start Frontend (in another terminal)

```bash
cd frontend
streamlit run app.py
```

7. Access the Webapp

- Backend API: http://localhost:8000
- Frontend (Streamlit): http://localhost:8501
