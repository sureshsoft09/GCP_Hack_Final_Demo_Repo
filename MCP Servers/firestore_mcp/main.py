import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Union

from fastmcp import FastMCP

from typing import Any
import httpx
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("firestore")

# Import all modules for tools
from firestore_client import FirestoreClient

# Initialize Firestore client
firestore_client = FirestoreClient()


@mcp.tool()
async def create_project(
    project_name: str,
    description: str = "",
    compliance_frameworks: List[str] = [],
    jira_project_key: str = "",
    created_by: str = ""
) -> Dict[str, Any]:
    """Create a new test case project."""
    try:
        # Create project request with proper validation
        project_data = {
            "project_name": project_name,
            "description": description or "",
            "compliance_frameworks": compliance_frameworks,
            "jira_project_key": jira_project_key or "",
            "status": "Active",
            "created_by": created_by or "system"
        }
        
        project_id = firestore_client.create_project(project_data)
        
        return {
            "success": True,
            "project_id": project_id,
            "message": f"Project '{project_name}' created successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    
@mcp.tool()
async def get_all_projects() -> Dict[str, Any]:
    """Get all projects from Firestore."""
    try:
        projects = firestore_client.get_all_projects()
        return {
            "success": True,
            "projects": projects,
            "count": len(projects)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_project(project_id: str) -> Dict[str, Any]:
    """Get project by ID."""
    try:
        project = firestore_client.get_project(project_id)
        if project:
            return {
                "success": True,
                "project": project
            }
        else:
            return {
                "success": False,
                "error": "Project not found"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def update_project(
    project_id: str,
    project_name: str = "",
    description: str = "",
    status: str = "",
    compliance_frameworks: List[str] = [],
    updated_by: str = ""
) -> Dict[str, Any]:
    """Update an existing project."""
    try:
        updates = {}
        if project_name:
            updates["project_name"] = project_name
        if description:
            updates["description"] = description
        if status:
            updates["status"] = status
        if compliance_frameworks:
            updates["compliance_frameworks"] = compliance_frameworks
        if updated_by:
            updates["updated_by"] = updated_by
        
        updates["updated_at"] = firestore_client.get_current_timestamp()
        
        success = firestore_client.update_project_simple(project_id, updates)
        
        if success:
            return {
                "success": True,
                "message": f"Project {project_id} updated successfully"
            }
        else:
            return {
                "success": False,
                "error": "Project not found or update failed"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def delete_project(project_id: str) -> Dict[str, Any]:
    """Delete a project."""
    try:
        success = firestore_client.delete_project(project_id)
        if success:
            return {
                "success": True,
                "message": f"Project {project_id} deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": "Project not found"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def search_projects(
    query: str = "",
    status: str = "",
    compliance_framework: str = ""
) -> Dict[str, Any]:
    """Search projects with filters."""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if compliance_framework:
            filters["compliance_frameworks"] = compliance_framework
        
        projects = firestore_client.search_projects(query, filters)
        
        return {
            "success": True,
            "projects": projects,
            "count": len(projects)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def add_epic_to_project(
    project_id: str,
    epic_name: str,
    description: str = "",
    epic_id: str = "",
    jira_issue_id: Optional[str] = None,
    priority: Optional[str] = None,
    jira_status: Optional[str] = None
) -> Dict[str, Any]:
    """Add an epic to a project."""
    try:
        epic_data = {
            "epic_name": epic_name,
            "description": description,
            "epic_id": epic_id or f"epic_{len(firestore_client.get_project_epics(project_id)) + 1}",
            "jira_issue_id": jira_issue_id or "",
            "priority": priority or "Medium",
            "jira_status": jira_status or "Not Pushed",
            "created_at": firestore_client.get_current_timestamp()
        }
        
        epic_id = firestore_client.add_epic_to_project(project_id, epic_data)
        
        return {
            "success": True,
            "epic_id": epic_id,
            "message": f"Epic '{epic_name}' added to project {project_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_project_epics(project_id: str) -> Dict[str, Any]:
    """Get all epics for a project."""
    try:
        epics = firestore_client.get_project_epics(project_id)
        return {
            "success": True,
            "epics": epics,
            "count": len(epics)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def add_feature_to_epic(
    project_id: str,
    epic_id: str,
    feature_name: str,
    description: str = "",
    feature_id: str = "",
    jira_issue_id: Optional[str] = None,
    priority: Optional[str] = None,
    jira_status: Optional[str] = None
) -> Dict[str, Any]:
    """Add a feature to an epic."""
    try:
        feature_data = {
            "feature_name": feature_name,
            "description": description,
            "feature_id": feature_id or f"feature_{len(firestore_client.get_epic_features(project_id, epic_id)) + 1}",
            "jira_issue_id": jira_issue_id or "",
            "priority": priority or "Medium",
            "jira_status": jira_status or "Not Pushed",
            "created_at": firestore_client.get_current_timestamp()
        }
        
        feature_id = firestore_client.add_feature_to_epic(project_id, epic_id, feature_data)
        
        return {
            "success": True,
            "feature_id": feature_id,
            "message": f"Feature '{feature_name}' added to epic {epic_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_epic_features(project_id: str, epic_id: str) -> Dict[str, Any]:
    """Get all features for an epic."""
    try:
        features = firestore_client.get_epic_features(project_id, epic_id)
        return {
            "success": True,
            "features": features,
            "count": len(features)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def add_use_case_to_feature(
    project_id: str,
    epic_id: str,
    feature_id: str,
    use_case_title: str,
    description: str = "",
    acceptance_criteria: List[str] = [],
    test_scenarios_outline: List[str] = [],
    model_explanation: str = "",
    review_status: str = "Draft",
    comments: str = "",
    compliance_mapping: List[str] = [],
    use_case_id: str = "",
    jira_issue_id: Optional[str] = None,
    priority: Optional[str] = None,
    jira_status: Optional[str] = None
) -> Dict[str, Any]:
    """Add a use case to a feature."""
    try:
        use_case_data = {
            "use_case_title": use_case_title,
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "test_scenarios_outline": test_scenarios_outline,
            "model_explanation": model_explanation,
            "review_status": review_status,
            "comments": comments,
            "compliance_mapping": compliance_mapping,
            "use_case_id": use_case_id or f"uc_{len(firestore_client.get_feature_use_cases(project_id, epic_id, feature_id)) + 1}",
            "jira_issue_id": jira_issue_id or "",
            "priority": priority or "Medium",
            "jira_status": jira_status or "Not Pushed",
            "created_at": firestore_client.get_current_timestamp()
        }
        
        use_case_id = firestore_client.add_use_case_to_feature(project_id, epic_id, feature_id, use_case_data)
        
        return {
            "success": True,
            "use_case_id": use_case_id,
            "message": f"Use case '{use_case_title}' added to feature {feature_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_feature_use_cases(project_id: str, epic_id: str, feature_id: str) -> Dict[str, Any]:
    """Get all use cases for a feature."""
    try:
        use_cases = firestore_client.get_feature_use_cases(project_id, epic_id, feature_id)
        return {
            "success": True,
            "use_cases": use_cases,
            "count": len(use_cases)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def add_test_case_to_use_case(
    project_id: str,
    epic_id: str,
    feature_id: str,
    use_case_id: str,
    test_case_title: str,
    test_steps: List[str],
    expected_result: str,
    test_type: str = "Functional",
    test_case_id: str = "",
    preconditions: List[str] = [],
    compliance_mapping: List[str] = [],
    model_explanation: str = "",
    review_status: str = "Draft",
    comments: str = "",
    jira_issue_id: Optional[str] = None,
    priority: Optional[str] = None,
    jira_status: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new test case to a use case."""
    try:
        # Prepare additional fields for the enhanced firestore method
        additional_fields = {
            "preconditions": preconditions,
            "compliance_mapping": compliance_mapping,
            "model_explanation": model_explanation,
            "review_status": review_status,
            "comments": comments,
            "jira_issue_id": jira_issue_id or "",
            "priority": priority or "Medium",
            "jira_status": jira_status or "Not Pushed"
        }
        
        # Include custom test_case_id if provided
        if test_case_id:
            additional_fields["custom_test_case_id"] = test_case_id
        
        # Call the enhanced firestore method with additional fields
        generated_test_case_id = firestore_client.add_test_case_to_use_case(
            project_id, epic_id, feature_id, use_case_id,
            test_case_title, test_steps, expected_result, test_type,
            additional_fields=additional_fields
        )
        
        return {
            "success": True,
            "test_case_id": generated_test_case_id,
            "message": f"Test case '{test_case_title}' added to use case '{use_case_id}'",
            "additional_data": {
                "preconditions": preconditions,
                "compliance_mapping": compliance_mapping,
                "model_explanation": model_explanation,
                "review_status": review_status,
                "comments": comments
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_project_statistics() -> Dict[str, Any]:
    """Get overall statistics for all projects."""
    try:
        stats = firestore_client.get_project_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port,
        )
    )
