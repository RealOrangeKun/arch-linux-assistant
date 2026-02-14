# Arch Linux Assistant 🐧

A web-based AI chat tool for Arch Linux users, powered by Ollama and FastAPI.

## Features

- 🤖 Real-time streaming AI responses
- 📝 Markdown rendering with syntax highlighting
- 💻 Code block copy functionality
- 🎨 Dark theme optimized for terminal users
- 🔒 Local AI inference (privacy-first)

## Prerequisites

**For Docker (Recommended):**
- Docker & Docker Compose

**For Local Development:**
- Python 3.8+
- Node.js 18+
- [Ollama](https://ollama.ai/) installed and running

### Install Ollama

```bash
# On Arch Linux
sudo pacman -S ollama

# Or install manually from ollama.ai
curl -fsSL https://ollama.ai/install.sh | sh
```

### Pull a model

```bash
ollama pull llama3.2
```

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Running the Application

### Option 1: Docker (Recommended)

```bash
# Start all services (Ollama + Backend + Frontend)
docker-compose up -d

# Pull the AI model (first time only)
docker exec arch-assistant-ollama ollama pull llama3.2

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Access the app**: http://localhost:3000

### Option 2: Local Development

#### Start Ollama (if not already running)

```bash
ollama serve
ollama pull llama3.2
```

#### Start Backend (Terminal 1)

```bash
cd backend
source venv/bin/activate
python main.py
```

Backend runs on: http://localhost:8000

#### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Frontend runs on: http://localhost:5173

## Usage

1. Open http://localhost:5173 in your browser
2. Start chatting with the AI about Arch Linux!
3. Ask questions about:
   - Package management (pacman, AUR)
   - System configuration
   - Troubleshooting
   - Command explanations

## API Endpoints

- `GET /` - Health check
- `GET /health` - Check Ollama connection
- `POST /api/chat` - Send messages (streaming response)

## Tech Stack

**Backend:**
- FastAPI
- Python 3.8+
- Ollama API

**Frontend:**
- React 18
- Vite
- react-markdown
- Prism.js

## License

MIT
