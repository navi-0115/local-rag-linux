# Webapp Setup Guide

This guide provides two options for setting up and running the webapp: using Docker or manual setup.

## Option 1: Manual Setup

### Prerequisites

- Git
- Python 3.8+
- pip

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
ollama run gemma3:4b
```

4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

5. Start Backend Server (in one terminal)

```bash
cd backend
uvicorn api:app --reload --port 8000
```

6. Start Frontend (in another terminal)

```bash
cd frontend
streamlit run app.py
```

7. Access the Webapp

- Backend API: http://localhost:8000
- Frontend (Streamlit): http://localhost:8501

## Option 2: Docker Setup

### Prerequisites

- Git
- Docker
- Docker Compose

### Setup Instructions

1. Clone the Repository

```bash
git clone https://github.com/navi-0115/local-rag-linux.git
cd local-rag-linux
```

2. Build and Start Services

```bash
docker compose up --build
```

3. Access the Webapp

- Backend API: http://localhost:8000
- Frontend (Streamlit): http://localhost:8501

4. Stop Services

```bash
docker compose down
```

## Troubleshooting

- Ensure no other services are running on ports 8000 or 8501
- For Docker issues:
  ```bash
  docker compose build --no-cache
  ```
- For manual setup issues:
  - Check if Ollama is running: `ollama list`
  - Verify Python dependencies: `pip list`
  - Check port availability: `lsof -i :8000` and `lsof -i :8501`

## Project Structure

```
├── backend/
├── frontend/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```
