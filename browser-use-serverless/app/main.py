from fastapi import FastAPI
from routers import sessions, agents

app = FastAPI(title="Browser Use Serverless API", version="1.0.0")

# Include routers
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(agents.router, prefix="/api/v1", tags=["Agents"])

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Browser Use Serverless API is running"}

@app.get("/")
async def root():
    return {"message": "Browser Use Serverless API", "docs": "/docs"}
