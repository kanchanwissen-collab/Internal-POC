from browser_use.agent.service import Agent
from fastapi import APIRouter
from pydantic import BaseModel,Field
from browser_use.llm.google.chat import ChatGoogle
import os 
from utility.constants import SESSION_ID_TO_AGENT_MAP, SESSIONS_MAP,SESSION_ID_TO_BROWSER_SESSION
class AgentCreateRequest(BaseModel):
    task:str = Field(..., description="The task for the agent")
    session_id:str = Field(..., description="The session ID to associate with the agent")
router = APIRouter()

@router.post("/agents")
async def create_agent(agent: AgentCreateRequest):
    try:
        session_id = agent.session_id
        task = agent.task
        api_key = os.getenv("GOOGLE_API_KEY","")
        if not api_key:
            return {"error": "GOOGLE_API_KEY environment variable not set"}, 500
        if not SESSIONS_MAP.get(session_id, False):
            return {"error": "Invalid or inactive session ID"}, 400
        browser_session = SESSION_ID_TO_BROWSER_SESSION.get(session_id)
        if not browser_session:
            return {"error": "No browser session found for the given session ID"}, 404
        agent:Agent = Agent(task =task , task_id=session_id,browser_session=browser_session,
                            llm = ChatGoogle(temperature=0,model="gemini-2.5-pro",api_key=api_key)

                        
                            )
        SESSION_ID_TO_AGENT_MAP[session_id] = agent
        await agent.run()
        
        return {"message": "Agent task completed successfully", "task": task, "session_id": session_id}
    except Exception as e:
        return {"error": str(e)}, 500

@router.get("/agents/{session_id}/stop")
async def stop_agent(session_id: str):
    try:
        # Here you would implement logic to stop the agent associated with the session_id
        # For example, if you have a mapping of session_id to agent instances, you could call a stop method on the agent.
        # This is a placeholder implementation.
            if not SESSIONS_MAP.get(session_id, False):
                return {"error": "Invalid or inactive session ID"}, 400
            agent = SESSION_ID_TO_AGENT_MAP.get(session_id)
            if not agent:
                return {"error": "Agent not found"}, 404
            agent.stop()
            return {"message": f"Agent for session {session_id} stopped successfully"}
    except Exception as e:
        return {"error": str(e)}, 500
@router.get("/agents/{session_id}/pause")
async def pause_agent(session_id: str):
    try:
        # Here you would implement logic to pause the agent associated with the session_id
        # This is a placeholder implementation.
            if not SESSIONS_MAP.get(session_id, False):
                return {"error": "Invalid or inactive session ID"}, 400
            agent = SESSION_ID_TO_AGENT_MAP.get(session_id)
            if not agent:
                return {"error": "Agent not found"}, 404
            agent.pause()
            return {"message": f"Agent for session {session_id} paused successfully"}
    except Exception as e:
        return {"error": str(e)}, 500
    
@router.get("/agents/{session_id}/resume")
async def resume_agent(session_id: str):
    try:
        # Here you would implement logic to resume the agent associated with the session_id
        # This is a placeholder implementation.
            if not SESSIONS_MAP.get(session_id, False):
                return {"error": "Invalid or inactive session ID"}, 400
            agent = SESSION_ID_TO_AGENT_MAP.get(session_id)
            if not agent:
                return {"error": "Agent not found"}, 404
            agent.resume()
            return {"message": f"Agent for session {session_id} resumed successfully"}
    except Exception as e:
        return {"error": str(e)}, 500
@router.get("/agents/{session_id}/status")
async def get_agent_status(session_id: str):
    try:
        # Here you would implement logic to get the status of the agent associated with the session_id
        # This is a placeholder implementation.
            if not SESSIONS_MAP.get(session_id, False):
                return {"error": "Invalid or inactive session ID"}, 400
            agent:Agent = SESSION_ID_TO_AGENT_MAP.get(session_id)
            if not agent:
                return {"error": "Agent not found"}, 404
            status = agent.state
            return {"session_id": session_id, "status": status}
    except Exception as e:
        return {"error": str(e)}, 500
