# Browser Use Serverless

A serverless browser automation service with a single session and dynamic session IDs.

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
curl -X POST http://localhost:8080/api/v1/sessions
```
This will return a response like:
```json
{
  "session_id": "a1b2-c3d4-e5f6-7890",
  "vnc_url": "http://localhost:8080/sessions/a1b2-c3d4-e5f6-7890/vnc/vnc.html?autoconnect=1",
  "vnc_port": 6080,
  "web_port": 5080,
  "display_num": 101
}
```

### List Sessions  
```bash
curl http://localhost:8080/api/v1/sessions
```

### Create an Agent
```bash
curl -X POST http://localhost:8080/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"task": "Navigate to google.com", "session_id": "a1b2-c3d4-e5f6-7890", "request_id": "test-123"}'
```

### Delete a Session
```bash
curl -X DELETE http://localhost:8080/api/v1/sessions/a1b2-c3d4-e5f6-7890
```

### Access VNC
Use the `vnc_url` returned from the create session API call, which will be in the format:
- http://localhost:8080/sessions/{session_id}/vnc/vnc.html?autoconnect=1

## Session Configuration

- **Single session**: Only one session can be active at a time
- **Dynamic session ID**: 16-digit hexadecimal format (xxxx-xxxx-xxxx-xxxx)
- **VNC port**: 6080 (internal)
- **Web port**: 5080 (noVNC)
- **Display number**: 101

## Environment Variables

- `GOOGLE_API_KEY`: Required for Gemini LLM
- `VNC_BASE_URL`: Base URL for VNC connections (default: http://localhost:8080)
- `CAPSOLVER_API_KEY`: Optional API key for CapSolver extension