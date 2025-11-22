import uuid
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai.types import Content, Part
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from master_agent.agent import root_agent

# Session and Runner
APP_NAME = "master_agent_app"
USER_ID="test_user"
SESSION_ID="test_session"

# Global session and runner instances
global_session = None
global_runner = None

# Initialize FastAPI app
app = FastAPI(title="Master Agent API", description="API for Master Agent interactions")  

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    debug_info: str = ""

async def setup_session_and_runner():
    print("DEBUG: Starting setup_session_and_runner()")
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)  # type: ignore
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service, memory_service=memory_service)
    print("DEBUG: Completed setup_session_and_runner()")
    return session, runner

async def reset_session():
    """Reset the global session and runner - useful for debugging or manual resets"""
    print("Starting reset_session()")
    global global_session, global_runner
    global_session = None
    global_runner = None
    print("Session and runner reset")

# Agent Interaction
async def call_agent_async(query, isnewproject: bool):
    print(f"DEBUG: Starting call_agent_async() with isnewproject={isnewproject}")
    global global_session, global_runner
    
    print("DEBUG: Creating Content object")
    content = Content(role='user', parts=[Part(text=query)])
    print(f"DEBUG: Content created successfully")

    # Print first 100 characters of the prompt for debugging
    print(f"Prompt (first 100 chars): {query[:100]}...")

    # Only setup new session and runner if it's a new project or if they don't exist
    if (
    isnewproject
    or global_session is None
    or global_runner is None
    or getattr(global_session, "is_closed", lambda: False)()
    ):
        print(f"Creating new session and runner (isnewproject: {isnewproject})")
        global_session, global_runner = await setup_session_and_runner()
        print("DEBUG: New session and runner created successfully")
    else:
        print("Reusing existing session and runner")

    print("DEBUG: About to call global_runner.run_async()")
    try:
        events = global_runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)
    except Exception as e:
        if "Session terminated" in str(e):
            print("?? MCP session terminated — reinitializing...")
            global_session, global_runner = await setup_session_and_runner()
            events = global_runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)
        else:
            raise
    print("DEBUG: global_runner.run_async() returned events generator")

    final_response_content = "Final response not yet received."
    debug_events = []
    
    print("DEBUG: Starting event processing loop")
    event_count = 0
    
    async for event in events:
        event_count += 1
        print(f"DEBUG: Processing event #{event_count}")
        
        if function_calls := event.get_function_calls():
            tool_name = function_calls[0].name
            debug_info = f"_Using tool {tool_name}..._"
            print(debug_info)
            debug_events.append(debug_info)
        elif event.actions and event.actions.transfer_to_agent:
            personality_name = event.actions.transfer_to_agent
            debug_info = f"_Delegating to agent: {personality_name}..._"
            print(debug_info)
            debug_events.append(debug_info)
        elif event.is_final_response() and event.content and event.content.parts:
            final_response_content = event.content.parts[0].text

        # For debugging, print the raw type and content to the console
        print(f"DEBUG: Full Event: {event}")
    
    print(f"DEBUG: Event processing loop completed. Processed {event_count} events")
    print("## Final Message")
    print(final_response_content)

    try:
        completed_session = await global_runner.session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        await global_runner.memory_service.add_session_to_memory(completed_session) #type: ignore
        print("DEBUG: Session added to memory successfully")
    except Exception as e:
        print(f"?? Skipped adding to memory: {e}")

    return final_response_content, "\n".join(debug_events)
    
# FastAPI endpoints
@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest,isnewproject: bool = False):
    """
    Process a query through the master agent and return the response.
    """
    print(f"DEBUG: Received API request - query length: {len(request.query)}, isnewproject: {isnewproject}")
    try:
        print("DEBUG: About to call call_agent_async()")
        response, debug_info = await call_agent_async(request.query, isnewproject)
        print(f"DEBUG: call_agent_async() completed successfully")
        print(f"DEBUG: Response length: {len(response) if response else 0}")
        return QueryResponse(response=response, debug_info=debug_info) #type:ignore
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception in process_query: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        print(f"DEBUG: Exception args: {e.args}")
        print(f"DEBUG: Request query length: {len(request.query) if request.query else 0}")
        print(f"DEBUG: isnewproject parameter: {isnewproject}")
        print(f"DEBUG: Global session exists: {global_session is not None}")
        print(f"DEBUG: Global runner exists: {global_runner is not None}")
        print(f"DEBUG: Full traceback:")
        print(traceback.format_exc())
        print("DEBUG: End of exception details")
        return QueryResponse(response=f"Error processing query: {str(e)}", debug_info=f"Exception type: {type(e).__name__}")    


@app.get("/")
async def root():
    """
    Health check endpoint.
    """
    print("DEBUG: Health check endpoint called")
    return {"message": "Master Agent API is running!", "status": "healthy"}

@app.post("/reset-session")
async def reset_session_endpoint():
    """
    Reset the current session and memory - useful for starting fresh.
    """
    print("DEBUG: Reset session endpoint called")
    await reset_session()
    print("DEBUG: Reset session endpoint completed")
    return {"message": "Session reset successfully", "status": "success"}

@app.on_event("startup")
async def startup_event():
    global global_session, global_runner
    print("?? Initializing persistent MCP session and runner...")
    global_session, global_runner = await setup_session_and_runner()
    print("? Persistent session and runner ready.")

@app.on_event("shutdown")
async def shutdown_event():
    global global_session
    if global_session:
        await global_session.close()
        print("?? MCP session closed.")

# Run the query (for testing when running directly)
if __name__ == "__main__":
    print("DEBUG: Starting main execution")
    # Test query when running the file directly
    import asyncio
    
    # Uncomment the lines below to test with a sample query
    # query = "Generate sample email to wish Diwali celebration"
    # response, debug = asyncio.run(call_agent_async(query))
    # print(f"Response: {response}")
    
    # Start FastAPI server
    import os
    port = int(os.getenv("PORT", 8082))
    print(f"DEBUG: About to start FastAPI server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

