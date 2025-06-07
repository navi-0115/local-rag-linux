# Webapp Setup using Docker & Docker Compose

This guide will help you set up and run the webapp using Docker and Docker Compose.

## Prerequisites

- Git
- Docker
- Docker Compose

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/navi-0115/local-rag-linux.git
cd local-rag-linux
```

### 2. Build and Start the Services

From the project root directory, run:

```bash
docker compose up --build
```

This command will build and start both the backend and frontend containers as defined in your docker-compose.yml and Dockerfile.

### 3. Access the Webapp locally

- Backend API: http://localhost:8000
- Frontend (Streamlit): http://localhost:8501

### 4. Stopping the Services

Press `Ctrl+C` in the terminal running Docker Compose, then:

```bash
docker compose down
```

This will stop and remove all running containers for this project.

### 5. (Optional) Rebuild on Code Changes

If you make changes to the source code, rebuild the images with:

```bash
docker compose up --build
```

## Troubleshooting

- Ensure no other services are running on ports 8000 or 8501.
- If you encounter issues, try rebuilding without cache:
  ```bash
  docker compose build --no-cache
  ```

## Project Structure

```
├── backend/
├── frontend/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```
