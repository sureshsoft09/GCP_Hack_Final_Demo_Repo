import os
import uuid
import tempfile
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
import httpx
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables FIRST before importing services
load_dotenv()

# Import our custom services AFTER loading environment variables
from upload_and_extract_service import upload_extract_service
from content_storage_service import content_storage_service
from firestore_service import firestore_service

# Firestore integration - Now handled by firestore_service
try:
    from google.cloud import firestore
    from google.oauth2 import service_account
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    print("Warning: Firestore libraries not available. Install with: pip install google-cloud-firestore")

# Environment variables with Cloud Run friendly defaults
AGENTS_API_URL = os.getenv("AGENTS_API_URL", "http://localhost:8082/query")
RESET_AGENT_SESSION_API_URL = os.getenv("RESET_AGENT_SESSION_API_URL","http://localhost:8082/reset-session")
TIMEOUT = float(os.getenv("AGENTS_API_TIMEOUT", "600"))
PORT = int(os.getenv("PORT", "8083"))  # Cloud Run sets PORT environment variable
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

app = FastAPI(
    title="MedAssure AI - Backend", 
    description="Backend API that forwards requests to the Agents API",
    version="1.0.0",
    debug=DEBUG
)

# Add CORS middleware
# Configure CORS for both development and production
cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if ENVIRONMENT == "production":
    # Add production frontend URLs if needed
    cors_origins.extend([
        "https://gen-lang-client-0182599221.web.app",
          "https://medassureaitool.web.app"  # Update with actual frontend URL
        "*"  # Allow all origins for now - restrict this in production
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if ENVIRONMENT == "development" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str
    metadata: Optional[dict] = None

class ReviewRequest(BaseModel):
    project_id: str
    project_name: str
    extracted_content: Optional[str] = None

class UploadResponse(BaseModel):
    success: bool
    message: str
    project_id: str
    files_processed: List[dict]
    extracted_content: str

class AgentResponse(BaseModel):
    response: str
    debug_info: Optional[str] = ""

class TestCase(BaseModel):
    id: str
    title: str
    description: str
    test_steps: List[str]
    expected_result: str
    test_data: Optional[dict] = None
    priority: str = "Medium"
    tags: List[str] = []
    model_explanation: Optional[str] = None

class UseCase(BaseModel):
    id: str
    title: str
    description: str
    test_cases: List[TestCase] = []
    model_explanation: Optional[str] = None

class Feature(BaseModel):
    id: str
    title: str
    description: str
    use_cases: List[UseCase] = []
    model_explanation: Optional[str] = None

class Epic(BaseModel):
    id: str
    title: str
    description: str
    features: List[Feature] = []
    model_explanation: Optional[str] = None

class ProjectHierarchy(BaseModel):
    project_id: str
    project_name: str
    description: Optional[str] = None
    epics: List[Epic] = []
    created_at: Optional[str] = None
    last_updated: Optional[str] = None
    total_test_cases: int = 0
    model_explanation: Optional[str] = None

class ProjectCreationRequest(BaseModel):
    project_name: str
    description: Optional[str] = None
    jira_project_key: str
    notification_email: str

class ProjectCreationResponse(BaseModel):
    project_id: str
    project_name: str
    description: Optional[str] = None
    jira_project_key: str
    notification_email: str
    created_at: str

async def call_agents_api(prompt: str) -> AgentResponse:
    payload = {"query": prompt}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            r = await client.post(AGENTS_API_URL, json=payload)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error contacting Agents API: {exc}")

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Agents API returned {r.status_code}: {r.text}")

    data = r.json()
    return AgentResponse(response=data.get("response", ""), debug_info=data.get("debug_info", ""))

async def reset_agent_session():
    """Reset the agent session to start fresh."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            r = await client.post(RESET_AGENT_SESSION_API_URL)
            if DEBUG:
                print(f"Agent session reset response: {r.status_code}")
            return r.status_code == 200
        except httpx.RequestError as exc:
            if DEBUG:
                print(f"Error resetting agent session: {exc}")
            return False

@app.post("/upload_requirement_file", response_model=UploadResponse)
async def upload_requirement_file(
    project_name: str = Form(...),
    project_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Upload requirement files, extract text, and store in cloud storage."""
    
    try:
        # Process files using the upload service
        result = await upload_extract_service.process_files(files, project_name, project_id)
        
        # Store the extracted content using the storage service
        content_storage_service.store_content(
            project_name=project_name,
            project_id=project_id,
            extracted_content=result["extracted_content"],
            processed_files=result["processed_files"]
        )
        
        if DEBUG:
            print(f"Processed {result['total_files']} files for project {project_name} ({project_id})")
        
        return UploadResponse(
            success=True,
            message=f"Successfully processed {result['total_files']} files",
            project_id=project_id,
            files_processed=result["processed_files"],
            extracted_content=result["extracted_content"]
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        if DEBUG:
            print(f"Unexpected error in upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during file processing: {str(e)}"
        )

@app.post("/review_requirement_specifications", response_model=AgentResponse)
async def review_requirement_specifications(req: ReviewRequest):
    """Review requirement specifications using the agent with extracted content."""
    
    # Retrieve stored extracted content using the storage service
    stored_data = content_storage_service.get_content(req.project_name, req.project_id)
    
    if not stored_data:
        raise HTTPException(
            status_code=404, 
            detail=f"No extracted content found for project {req.project_name} (ID: {req.project_id}). Please upload files first."
        )
    
    extracted_content = stored_data.get("extracted_content", "")
    if not extracted_content:
        raise HTTPException(
            status_code=400, 
            detail="No text content was extracted from the uploaded files."
        )
    
    if DEBUG:
        print(f"Processing review for project {req.project_name} with {len(extracted_content)} characters of content")
    
    # Reset agent session to start fresh for this requirement review
    session_reset = await reset_agent_session()
    if DEBUG:
        print(f"Agent session reset: {'successful' if session_reset else 'failed'}")
    
    # Build a comprehensive prompt for the agent
    prompt = f"""
    Please review and analyze the following requirement specifications for project '{req.project_name}':

    pass this to requirement_reviewer_agent not any other tools.

    EXTRACTED CONTENT:
    {extracted_content}

    """
    
    # Update the stored data with review timestamp using the storage service
    content_storage_service.update_review_timestamp(req.project_name, req.project_id)
    
    return await call_agents_api(prompt)

@app.post("/generate_test_cases", response_model=AgentResponse)
async def generate_test_cases(req: PromptRequest):
    """Generate test cases using the previously reviewed and approved requirement details."""
    prompt = f"""
    Generate complete test cases using the previously validated and approved requirement details available in memory. 
    Follow the standard MedAssureAI process and use the connected sub-agents (test_generator_agent) 
    to generate test cases in a structured format.

    User instruction: {req.prompt}
    """
    response = await call_agents_api(prompt)

    print("DEBUG: Received response from agent")
    print(f"Response (first 1000 chars): {response.response[:1000]}...")

    prompt_pushdata = """
    
   Push all generated artifacts (Epics → Features → Use Cases → Test Cases) to Jira in bulk, retrieve Jira issue IDs, map them back into the artifacts, and then write the entire hierarchy to Firestore using a single bulk write operation.

    ---
    master_agent to
        → Takes generated artifacts (epics/features/use cases/test cases)
        → Builds a batch_create_issues payload (list)
        → Calls MCP Jira tool once
        → Gets all created Jira issue IDs back
        → Maps IDs to the artifacts
        → Stores the enriched results to Firestore through bulk_write_epics_structure

When calling any MCP function tool:
    - The final message must contain **only** valid JSON arguments for the function
    - No Python code, no comments, no variable setup, no explanation
    - All reasoning must be done internally

#### Workflow Instructions

    ## 1. Jira Synchronization (Batch)

        1. Read the list of generated artifacts (epics, features, use cases, test cases).
        2. Construct a single batch Jira MCP call, not individual per-item calls, to avoid 429 throttling:

        {
        "operation": "batch_create_issues",
        "jira_project_key": "{{JIRA_PROJECT_KEY}}",
        "jira_issues": [
            {
            "issue_type": "...",
            "summary": "...",
            "description": "..."
            }
        ]
        }

        3. Execute the Jira MCP tool.

        4. Receive the batch response containing:

            jira_issue_id for each created issue

            Index-based matching to artifacts

        5. For each artifact:

            Add jira_issue_id

            Set jira_status = "pushed"

    ## 2. Firestore Bulk Write

        After Jira IDs are mapped into their corresponding artifacts:
      
        Construct a combined Firestore MCP call such as:

        {
        "operation": "bulk_write_epics_structure",
        "project_id": "{{FIRESTORE_PROJECT_ID}}",
        "epics": [
            {...}
            {...}
        ]
        }

        Rules:

        ✔ Write the entire nested hierarchy in one MCP call, not item-by-item.
        ✔ Use the Firestore project ID passed into the input ({{FIRESTORE_PROJECT_ID}}).
        ✔ If the Firestore project does not exist:
        
    3. Post-Write Validation

    After Firestore bulk-write:
    - Return success status and summary


    """
    response_FirestoreJira_status = await call_agents_api(prompt_pushdata)

    print("DEBUG: Received response from agent after pushing data to Firestore and Jira")
    print(f"Response (first 1000 chars): {response_FirestoreJira_status.response[:1000]}...")

    return response_FirestoreJira_status


@app.post("/enhance_test_cases_chat", response_model=AgentResponse)
async def enhance_test_cases_chat(req: PromptRequest):
    """Enhance existing test cases."""

    print(f"DEBUG: Starting enhance_test_cases_chat() - User Prompt - {req.prompt}")

    prompt = f"""
        This is a clarification for any specific use case or test case request from the user.
        The user has provided additional information or clarifications for the test cases/ use cases previously generated.
        master_agent should forward it to the enhance_testcase_agent not to any other tools. 
        
        Context:
        - Type: Enhance Clarification Interaction
        - Intent: Provide clarification, or confirm requirements as complete to change/ enhance existing test case/ use case and store it into Firestore and Jira.
        - User message: {req.prompt}    
        """
    response = await call_agents_api(prompt)
    print("DEBUG: Received response from agent")
    print(f"Response: {response}")

    return response


@app.post("/migration_test_cases", response_model=AgentResponse)
async def migration_test_cases(req: PromptRequest):
    """Produce migration-specific test cases or guidance."""
    prompt = f"Generate migration test cases for: {req.prompt}"
    response = await call_agents_api(prompt)
    
    return response


@app.post("/requirement_clarification_chat", response_model=AgentResponse)
async def req_clarification_chat_with_agent(req: PromptRequest):
    """
    Handles clarification or follow-up conversation with the master_agent.
    This endpoint passes user responses or confirmations (e.g., clarification answers, 
    'use as complete', 'consider final') to the master_agent, which routes them to 
    requirement_reviewer_agent for contextual update.
    """
    prompt = f"""
    This is a clarification continuation request from the user for requirement review.
    The user has provided additional information or confirmation regarding previously
    identified ambiguous or missing requirements. It should be forwarded to the requirement_reviewer_agent not to any other tools. 

    Context:
    - Type: Clarification Interaction
    - Intent: Resolve pending ambiguities, provide clarification, or confirm requirements as complete.
    - User message: {req.prompt}
    
    """
    return await call_agents_api(prompt)

@app.post("/reset_agentsession")
async def reset_agent_session_endpoint():
    """Reset the agent session to start fresh."""
    try:
        success = await reset_agent_session()
        if success:
            return {"message": "Agent session reset successfully", "success": True}
        else:
            return {"message": "Failed to reset agent session", "success": False}
    except Exception as e:
        if DEBUG:
            print(f"Error in reset_agentsession endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting agent session: {str(e)}")

##Firestore Integration Endpoints

@app.get("/projects")
async def get_storage_projects():
    """Get all stored projects for dashboard."""
    try:
        # Get all projects from storage service
        storage_stats = content_storage_service.get_storage_stats()
        all_projects = content_storage_service.get_all_projects()
        
        # Format projects for dashboard
        projects = []
        for project_key, project_data in all_projects.items():
            project_name, project_id = project_key.split('_', 1)
            projects.append({
                "id": project_id,
                "name": project_name,
                "created_at": project_data.get('created_at'),
                "last_updated": project_data.get('last_updated'),
                "files_count": len(project_data.get('files', [])),
                "content_length": len(project_data.get('extracted_content', '')),
                "status": "active"
            })
        
        return {"projects": projects, "total": len(projects)}
    except Exception as e:
        return {"projects": [], "total": 0}

@app.get("/analytics/overview")
async def get_analytics_overview():
    """Get analytics overview for dashboard."""
    try:
        storage_stats = content_storage_service.get_storage_stats()
        firestore_stats = firestore_service.get_project_statistics()
        
        # Combine both storage and Firestore statistics
        return {
            "totalProjects": storage_stats.get("total_projects", 0) + firestore_stats.get("total_projects", 0),
            "totalTestCases": firestore_stats.get("total_test_cases", 0),
            "completedTests": int(firestore_stats.get("total_test_cases", 0) * 0.8),  # Estimate 80% completed
            "pendingTests": int(firestore_stats.get("total_test_cases", 0) * 0.2),    # Estimate 20% pending
        }
    except Exception as e:
        if DEBUG:
            print(f"Error fetching analytics overview: {e}")
        return {
            "totalProjects": 0,
            "totalTestCases": 0,
            "completedTests": 0,
            "pendingTests": 0,
        }

@app.get("/analytics/recent-activity")
async def get_recent_activity():
    """Get recent activity for dashboard."""
    try:
        all_projects = content_storage_service.get_all_projects()
        activities = []
        
        for project_key, project_data in all_projects.items():
            project_name, project_id = project_key.split('_', 1)
            
            # Add file upload activity
            for file_info in project_data.get('files', []):
                activities.append({
                    "id": f"upload_{project_id}_{len(activities)}",
                    "type": "upload",
                    "description": f"Uploaded {file_info.get('filename', 'file')} to {project_name}",
                    "timestamp": project_data.get('created_at', datetime.now().isoformat()),
                    "project": project_name
                })
            
            # Add review activity if reviewed
            if project_data.get('last_reviewed'):
                activities.append({
                    "id": f"review_{project_id}",
                    "type": "review",
                    "description": f"Reviewed requirements for {project_name}",
                    "timestamp": project_data.get('last_reviewed'),
                    "project": project_name
                })
        
        # Sort by timestamp, most recent first
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return activities[:10]  # Return last 10 activities
    except Exception as e:
        return []

@app.get("/project/{project_id}")
async def get_project_info(project_id: str):
    """Get stored project information."""
    matching_projects = content_storage_service.get_projects_by_id(project_id)
    
    if not matching_projects:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    
    return {"projects": matching_projects}

# Firestore Integration Endpoints

def convert_firestore_to_hierarchy(firestore_data: dict) -> ProjectHierarchy:
    """Convert Firestore document to ProjectHierarchy model."""
    try:
        # Extract basic project info
        project_id = firestore_data.get("project_id", "")
        project_name = firestore_data.get("project_name", "")
        description = firestore_data.get("description", "")
        created_at = firestore_data.get("created_at", "")
        last_updated = firestore_data.get("last_updated", "")
        model_explanation = firestore_data.get("model_explanation", "")
        
        # Process epics
        epics = []
        total_test_cases = 0
        
        for epic_data in firestore_data.get("epics", []):
            features = []
            
            for feature_data in epic_data.get("features", []):
                use_cases = []
                
                for use_case_data in feature_data.get("use_cases", []):
                    test_cases = []
                    
                    for test_case_data in use_case_data.get("test_cases", []):
                        test_case = TestCase(
                            id=test_case_data.get("id", ""),
                            title=test_case_data.get("title", ""),
                            description=test_case_data.get("description", ""),
                            test_steps=test_case_data.get("test_steps", []),
                            expected_result=test_case_data.get("expected_result", ""),
                            test_data=test_case_data.get("test_data"),
                            priority=test_case_data.get("priority", "Medium"),
                            tags=test_case_data.get("tags", []),
                            model_explanation=test_case_data.get("model_explanation", "")
                        )
                        test_cases.append(test_case)
                        total_test_cases += 1
                    
                    use_case = UseCase(
                        id=use_case_data.get("id", ""),
                        title=use_case_data.get("title", ""),
                        description=use_case_data.get("description", ""),
                        test_cases=test_cases,
                        model_explanation=use_case_data.get("model_explanation", "")
                    )
                    use_cases.append(use_case)
                
                feature = Feature(
                    id=feature_data.get("id", ""),
                    title=feature_data.get("title", ""),
                    description=feature_data.get("description", ""),
                    use_cases=use_cases,
                    model_explanation=feature_data.get("model_explanation", "")
                )
                features.append(feature)
            
            epic = Epic(
                id=epic_data.get("id", ""),
                title=epic_data.get("title", ""),
                description=epic_data.get("description", ""),
                features=features,
                model_explanation=epic_data.get("model_explanation", "")
            )
            epics.append(epic)
        
        return ProjectHierarchy(
            project_id=project_id,
            project_name=project_name,
            description=description,
            epics=epics,
            created_at=created_at,
            last_updated=last_updated,
            total_test_cases=total_test_cases,
            model_explanation=model_explanation
        )
    
    except Exception as e:
        if DEBUG:
            print(f"Error converting Firestore data: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing project data: {str(e)}")

@app.get("/firestore/projects", response_model=List[Dict[str, Any]])
async def get_firestore_projects():
    """Get all projects from Firestore."""
    try:
        projects = await firestore_service.get_all_projects()
        return projects
    except Exception as e:
        if DEBUG:
            print(f"Error fetching Firestore projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

@app.get("/firestore/projects/{project_id}/hierarchy", response_model=ProjectHierarchy)
async def get_firestore_project_hierarchy(project_id: str):
    """Get complete project hierarchy from Firestore."""
    try:
        project_data = firestore_service.get_project_by_id(project_id)
        
        if not project_data:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Convert to hierarchical structure
        hierarchy = convert_firestore_to_hierarchy(project_data)
        return hierarchy
    except HTTPException:
        raise
    except Exception as e:
        if DEBUG:
            print(f"Error fetching project hierarchy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch project hierarchy: {str(e)}")

@app.get("/firestore/projects/{project_id}/model-explanation")
async def get_model_explanation(
    project_id: str,
    item_type: str = Query(..., description="Type: project, epic, feature, use_case, test_case"),
    item_id: str = Query(..., description="ID of the specific item")
):
    """Get model explanation for a specific item in the project hierarchy."""
    try:
        explanation = await firestore_service.get_model_explanation(project_id, item_type, item_id)
        
        if explanation is None:
            raise HTTPException(status_code=404, detail=f"{item_type} with ID {item_id} not found")
        
        return {"model_explanation": explanation or "No explanation available"}
    except HTTPException:
        raise
    except Exception as e:
        if DEBUG:
            print(f"Error fetching model explanation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch model explanation: {str(e)}")

@app.get("/firestore/projects/{project_id}/export-data")
async def get_firestore_project_export_data(project_id: str):
    """Get project data formatted for export."""
    try:
        project_data = firestore_service.get_project_by_id(project_id)
        
        if not project_data:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Convert to hierarchical structure for processing
        hierarchy = convert_firestore_to_hierarchy(project_data)
        
        # Format data for export service
        export_data = {
            "project": {
                "id": hierarchy.project_id,
                "name": hierarchy.project_name,
                "description": hierarchy.description or "",
                "created_at": hierarchy.created_at,
                "last_updated": hierarchy.last_updated,
                "total_test_cases": hierarchy.total_test_cases,
                "model_explanation": hierarchy.model_explanation or ""
            },
            "epics": []
        }
        
        for epic in hierarchy.epics:
            epic_data = {
                "id": epic.id,
                "title": epic.title,
                "description": epic.description,
                "model_explanation": epic.model_explanation or "",
                "features": []
            }
            
            for feature in epic.features:
                feature_data = {
                    "id": feature.id,
                    "title": feature.title,
                    "description": feature.description,
                    "model_explanation": feature.model_explanation or "",
                    "use_cases": []
                }
                
                for use_case in feature.use_cases:
                    use_case_data = {
                        "id": use_case.id,
                        "title": use_case.title,
                        "description": use_case.description,
                        "model_explanation": use_case.model_explanation or "",
                        "test_cases": []
                    }
                    
                    for test_case in use_case.test_cases:
                        test_case_data = {
                            "id": test_case.id,
                            "title": test_case.title,
                            "description": test_case.description,
                            "test_steps": test_case.test_steps,
                            "expected_result": test_case.expected_result,
                            "test_data": test_case.test_data,
                            "priority": test_case.priority,
                            "tags": test_case.tags,
                            "model_explanation": test_case.model_explanation or ""
                        }
                        use_case_data["test_cases"].append(test_case_data)
                    
                    feature_data["use_cases"].append(use_case_data)
                
                epic_data["features"].append(feature_data)
            
            export_data["epics"].append(epic_data)
        
        return export_data
    except HTTPException:
        raise
    except Exception as e:
        if DEBUG:
            print(f"Error preparing export data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to prepare export data: {str(e)}")

@app.post("/firestore/projects")
async def create_firestore_project(project_data: Dict[str, Any]):
    """Create a new project in Firestore."""
    try:
        project_id = await firestore_service.create_project(project_data)
        return {"project_id": project_id, "message": "Project created successfully"}
    except Exception as e:
        if DEBUG:
            print(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.put("/firestore/projects/{project_id}")
async def update_firestore_project(project_id: str, project_data: Dict[str, Any]):
    """Update an existing project in Firestore."""
    try:
        success = await firestore_service.update_project(project_id, project_data)
        if success:
            return {"message": "Project updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    except HTTPException:
        raise
    except Exception as e:
        if DEBUG:
            print(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@app.delete("/firestore/projects/{project_id}")
async def delete_firestore_project(project_id: str):
    """Delete a project from Firestore."""
    try:
        success = await firestore_service.delete_project(project_id)
        if success:
            return {"message": "Project deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    except HTTPException:
        raise
    except Exception as e:
        if DEBUG:
            print(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

@app.get("/firestore/statistics")
async def get_firestore_statistics():
    """Get overall Firestore statistics."""
    try:
        stats = await firestore_service.get_project_statistics()
        return stats
    except Exception as e:
        if DEBUG:
            print(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")

# ================================
# ENHANCED FIRESTORE PROJECT ENDPOINTS
# ================================

@app.post("/api/generate-project-id", response_model=ProjectCreationResponse)
async def generate_project_id(req: ProjectCreationRequest):
    """Generate a unique project ID and create project metadata"""
    import random
    import string
    
    try:
        # Get all existing projects to check for ID conflicts
        existing_projects = firestore_service.get_all_projects()
        existing_ids = {project.get('project_id', '') for project in existing_projects}
        
        # Generate unique project ID in format Pro_XXXXXXXX (8 digits)
        max_attempts = 100
        project_id = None
        
        for _ in range(max_attempts):
            # Generate 8-digit alphanumeric code
            random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            candidate_id = f"Pro_{random_code}"
            
            if candidate_id not in existing_ids:
                project_id = candidate_id
                break
        
        if not project_id:
            raise HTTPException(status_code=500, detail="Failed to generate unique project ID after multiple attempts")
        
        if DEBUG:
            print(f"✅ Generated new project ID: {project_id}")
            print(f"📁 Project Name: {req.project_name}")
            print(f"🔑 Jira Key: {req.jira_project_key}")
            print(f"📧 Notification Email: {req.notification_email}")
        
        # Create project metadata
        project_metadata = {
            "project_id": project_id,
            "project_name": req.project_name,
            "description": req.description or "",
            "jira_project_key": req.jira_project_key,
            "notification_email": req.notification_email,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "status": "created",
            "epics": []
        }
        
        # Store initial project metadata in Firestore
        created_project_id = firestore_service.create_project(project_metadata)
        
        if not created_project_id:
            raise HTTPException(status_code=500, detail="Failed to create project in database")
        
        if DEBUG:
            print(f"💾 Project stored in Firestore with ID: {created_project_id}")
            print(f"🎉 Project creation completed successfully!")
        
        return ProjectCreationResponse(
            project_id=project_id,
            project_name=req.project_name,
            description=req.description,
            jira_project_key=req.jira_project_key,
            notification_email=req.notification_email,
            created_at=project_metadata["created_at"]
        )
        
    except Exception as e:
        if DEBUG:
            print(f"Error generating project ID: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate project ID: {str(e)}")

@app.get("/api/projects")
async def get_all_projects():
    """Get all projects from Firestore"""
    try:
        projects = firestore_service.get_all_projects()
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")

@app.get("/api/projects/{project_id}")
async def get_project_by_id(project_id: str):
    """Get a specific project by ID"""
    try:
        project = firestore_service.get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"project": project}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching project: {str(e)}")

@app.get("/api/projects/{project_id}/hierarchy")
async def get_project_hierarchy(project_id: str):
    """Get complete project hierarchy"""
    try:
        project_data = firestore_service.get_project_by_id(project_id)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Return the project data with hierarchy structure
        return {"hierarchy": project_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching project hierarchy: {str(e)}")

@app.get("/api/projects/{project_id}/model-explanation")
async def get_model_explanation(project_id: str, item_type: str = Query(...), item_id: str = Query(...)):
    """Get model explanation for a specific item"""
    try:
        explanation = firestore_service.get_model_explanation(project_id, item_type, item_id)
        if explanation is None:
            raise HTTPException(status_code=404, detail="Item not found or no explanation available")
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching model explanation: {str(e)}")

@app.post("/api/projects/{project_id}/search")
async def search_test_cases(project_id: str, search_data: dict):
    """Search test cases within a project"""
    try:
        search_term = search_data.get("search_term", "")
        if not search_term:
            raise HTTPException(status_code=400, detail="Search term is required")
        
        results = firestore_service.search_test_cases(project_id, search_term)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching test cases: {str(e)}")

# ================================
# HIERARCHY MANAGEMENT ENDPOINTS
# ================================

@app.post("/api/projects/{project_id}/epics")
async def add_epic_to_project(project_id: str, epic_data: dict):
    """Add an epic to a project"""
    try:
        success = firestore_service.add_epic_to_project(project_id, epic_data)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Epic added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding epic: {str(e)}")

@app.post("/api/projects/{project_id}/epics/{epic_id}/features")
async def add_feature_to_epic(project_id: str, epic_id: str, feature_data: dict):
    """Add a feature to an epic"""
    try:
        success = firestore_service.add_feature_to_epic(project_id, epic_id, feature_data)
        if not success:
            raise HTTPException(status_code=404, detail="Project or epic not found")
        return {"message": "Feature added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding feature: {str(e)}")

@app.post("/api/projects/{project_id}/epics/{epic_id}/features/{feature_id}/use-cases")
async def add_use_case_to_feature(project_id: str, epic_id: str, feature_id: str, use_case_data: dict):
    """Add a use case to a feature"""
    try:
        success = firestore_service.add_use_case_to_feature(project_id, epic_id, feature_id, use_case_data)
        if not success:
            raise HTTPException(status_code=404, detail="Project, epic, or feature not found")
        return {"message": "Use case added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding use case: {str(e)}")

@app.post("/api/projects/{project_id}/epics/{epic_id}/features/{feature_id}/use-cases/{use_case_id}/test-cases")
async def add_test_case_to_use_case(project_id: str, epic_id: str, feature_id: str, use_case_id: str, test_case_data: dict):
    """Add a test case to a use case"""
    try:
        success = firestore_service.add_test_case_to_use_case(project_id, epic_id, feature_id, use_case_id, test_case_data)
        if not success:
            raise HTTPException(status_code=404, detail="Project, epic, feature, or use case not found")
        return {"message": "Test case added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding test case: {str(e)}")

@app.post("/api/projects/{project_id}/bulk-create")
async def bulk_create_structure(project_id: str, structure_data: dict):
    """Bulk create project structure from hierarchical data"""
    try:
        result = firestore_service.bulk_create_from_structure(project_id, structure_data)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error bulk creating structure: {str(e)}")

# ================================
# EXPORT ENDPOINTS
# ================================

@app.get("/api/projects/{project_id}/export-data")
async def get_project_export_data(project_id: str):
    """Get project data formatted for export (used by frontend export service)"""
    try:
        # Get project data
        project_data = firestore_service.get_project_by_id(project_id)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"project": project_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting export data: {str(e)}")

@app.get("/health")
async def health():
    storage_stats = content_storage_service.get_storage_stats()
    service_config = upload_extract_service
    firestore_status = firestore_service.is_available()
    
    return {
        "status": "ok", 
        "agents_api_url": AGENTS_API_URL,
        "environment": ENVIRONMENT,
        "debug": DEBUG,
        "firestore_available": firestore_status,
        "google_cloud_bucket": service_config.google_cloud_bucket,
        "max_file_size_mb": service_config.max_file_size / 1024 / 1024,
        "allowed_file_types": service_config.allowed_file_types,
        "stored_projects": storage_stats["total_projects"],
        "total_files": storage_stats["total_files"],
        "total_content_length": storage_stats["total_content_length"]
    }

@app.get("/")
async def root():
    """Root endpoint for Cloud Run health checks."""
    return {"message": "MedAssure AI Backend is running!", "status": "healthy"}

# Main execution for Cloud Run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

