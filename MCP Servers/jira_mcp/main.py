import asyncio
import logging
import os
from typing import List, Dict, Any

from fastmcp import FastMCP

from typing import Any
import httpx
from pydantic import BaseModel
import os
from jira import JIRA
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("jira")

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "HS25SKL")

# Validate required environment variables
if not JIRA_BASE_URL:
    raise ValueError("JIRA_BASE_URL environment variable is required")
if not JIRA_EMAIL:
    raise ValueError("JIRA_EMAIL environment variable is required")
if not JIRA_API_TOKEN:
    raise ValueError("JIRA_API_TOKEN environment variable is required")

JIRA_HEADERS = {
    "Authorization": f"Basic {JIRA_EMAIL}:{JIRA_API_TOKEN}",
    "Content-Type": "application/json"
}
auth_jira = JIRA(server=JIRA_BASE_URL, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))

class IssueCreateRequest(BaseModel):
    project_key: str = JIRA_PROJECT_KEY
    summary: str
    description: str
    issue_type: str = "Bug"

async def make_jira_request(method: str, url: str, **kwargs) -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, headers=JIRA_HEADERS, timeout=30.0, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

@mcp.tool()
async def get_issues() -> dict[str, Any] | str:
    """Get all JIRA issues."""
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    data = await make_jira_request("GET", url)
    if not data:
        return "Unable to fetch issues."
    return data

#@mcp.tool()
async def create_issue(project_key: str = JIRA_PROJECT_KEY, summary: str = "", description: str = "", issue_type: str = "Task") -> dict[str, Any] | str:
    """Create a new JIRA issue."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        }
    }
    issue = auth_jira.create_issue(fields=payload["fields"])
    if not issue:
        return "Unable to create issue."
    # Convert Issue object to dict (using .raw or extracting fields)
    return issue.raw if hasattr(issue, "raw") else {"key": getattr(issue, "key", None)}

@mcp.tool()
async def batch_create_issues(jira_issues: List[Dict[str, Any]], project_key: str = JIRA_PROJECT_KEY):
    created = []
    failed = []
    
    for idx, issue in enumerate(jira_issues):
        try:

            payload = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": issue["summary"],
                    "description": issue["description"],
                    "issuetype": {"name": issue["issue_type"]}
                }
            }
                        
            result = auth_jira.create_issue(fields=payload["fields"])

            created.append({
                "index": idx,
                "jira_issue_id": result.id
            })
        except Exception as e:
            failed.append({
                "index": idx,
                "error": str(e)
            })
            asyncio.sleep(2)  # retry spacing to avoid 429 throttling

    return {"created": created, "failed": failed}

@mcp.tool()
async def search_issues(jql: str) -> dict[str, Any] | str:
    """Search JIRA issues using JQL."""
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {"jql": jql}
    data = await make_jira_request("GET", url, params=params)
    if not data:
        return "Unable to search issues."
    return data

@mcp.tool()
async def create_issue_in_project(project_key: str = JIRA_PROJECT_KEY, summary: str = "", description: str = "", issue_type: str = "Task") -> dict[str, Any] | str:
    """Create a new issue in a specific JIRA project.

    Args:
        project_key: The key of the JIRA project (e.g., 'ABC')
        summary: The summary/title of the issue
        description: The description/details of the issue
        issue_type: The type of the issue (e.g., 'Task', 'Bug')
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        }
    }
    data = await make_jira_request("POST", url, json=payload)
    if not data:
        return f"Unable to create issue in project {project_key}."
    return data

@mcp.tool()
async def get_issues_from_project(project_key: str = JIRA_PROJECT_KEY) -> dict[str, Any] | str:
    """Get all JIRA issues from a specific project.
    Args:
        project_key: The key of the JIRA project (e.g., 'ABC')
    """
    jql = f"project={project_key}"
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {"jql": jql}
    data = await make_jira_request("GET", url, params=params)
    if not data:
        return f"Unable to fetch issues from project {project_key}."
    return data

@mcp.tool()
async def search_issues_in_project(project_key: str = JIRA_PROJECT_KEY, jql_query: str = "") -> dict[str, Any] | str:
    """Search JIRA issues in a specific project using JQL.
    Args:
        project_key: The key of the JIRA project (e.g., 'ABC')
        jql_query: Additional JQL query string (e.g., 'status=Open')
    """
    jql = f"project={project_key} AND {jql_query}" if jql_query else f"project={project_key}"
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {"jql": jql}
    data = await make_jira_request("GET", url, params=params)
    if not data:
        return f"Unable to search issues in project {project_key}."
    return data

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port,
        )
    )
