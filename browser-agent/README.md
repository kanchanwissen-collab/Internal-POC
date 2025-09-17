# Browser Use Serverless

A serverless browser automation service with 10 parallel sessions.

## Quick Start with Docker Compose

1. **Clone and setup environment:**
   ```bash
   git clone <your-repo>
   cd browser-use-serverless
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the service:**
   - API Docs: http://localhost:8080/docs
   - Health Check: http://localhost:8080/api/health

## API Usage

### Create a Session
```bash
curl -X POST http://localhost:8080/api/sessions
```

### List Sessions  
```bash
curl http://localhost:8080/api/sessions
```

### Create an Agent
```bash
curl -X POST http://localhost:8080/api/agents \
  -H "Content-Type: application/json" \
  -d '{"task": "Navigate to google.com", "session_id": "session_00"}'
```

### Access VNC
- Session 00: http://localhost:8080/sessions/session_00/vnc/vnc.html
- Session 01: http://localhost:8080/sessions/session_01/vnc/vnc.html
- ... and so on

## Session Configuration

- **10 parallel sessions**: session_00 to session_09
- **VNC ports**: 6080-6089 (internal)
- **Web ports**: 5080-5089 (noVNC)
- **Display numbers**: 101-110

## Environment Variables

- `GOOGLE_API_KEY`: Required for Gemini LLM
- `VNC_BASE_URL`: Base URL for VNC connections (default: http://localhost:8080)