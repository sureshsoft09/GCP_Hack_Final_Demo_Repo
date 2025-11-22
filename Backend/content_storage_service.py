import os
from typing import Dict, Any, Optional
from datetime import datetime


class ContentStorageService:
    """Service for managing extracted content storage."""
    
    def __init__(self):
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        # In-memory storage for extracted content (in production, use a database)
        self.extracted_content_store: Dict[str, Dict[str, Any]] = {}
    
    def generate_content_key(self, project_name: str, project_id: str) -> str:
        """Generate a unique key for storing content."""
        return f"{project_name}_{project_id}"
    
    def store_content(
        self, 
        project_name: str, 
        project_id: str, 
        extracted_content: str, 
        processed_files: list
    ) -> None:
        """Store extracted content and metadata."""
        content_key = self.generate_content_key(project_name, project_id)
        
        current_time = datetime.now().isoformat()
        self.extracted_content_store[content_key] = {
            "extracted_content": extracted_content,
            "project_name": project_name,
            "project_id": project_id,
            "created_at": current_time,
            "last_updated": current_time,
            "uploaded_at": current_time,  # Keep for backwards compatibility
            "files": processed_files,
            "content_length": len(extracted_content),
            "file_count": len(processed_files)
        }
        
        if self.debug:
            print(f"Stored content for project {project_name} ({project_id}) - {len(extracted_content)} characters")
    
    def get_content(self, project_name: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored content."""
        content_key = self.generate_content_key(project_name, project_id)
        
        if self.debug:
            print(f"Looking for content with key: {content_key}")
            print(f"Available keys: {list(self.extracted_content_store.keys())}")
        
        return self.extracted_content_store.get(content_key)
    
    def update_review_timestamp(self, project_name: str, project_id: str) -> bool:
        """Update the review timestamp for a project."""
        content_key = self.generate_content_key(project_name, project_id)
        
        if content_key in self.extracted_content_store:
            current_time = datetime.now().isoformat()
            self.extracted_content_store[content_key]["last_reviewed"] = current_time
            self.extracted_content_store[content_key]["last_updated"] = current_time
            return True
        return False
    
    def get_all_projects(self) -> Dict[str, Dict[str, Any]]:
        """Get all stored projects."""
        return self.extracted_content_store
    
    def get_projects_by_id(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        """Get projects matching a specific project ID."""
        return {k: v for k, v in self.extracted_content_store.items() if project_id in k}
    
    def delete_content(self, project_name: str, project_id: str) -> bool:
        """Delete stored content."""
        content_key = self.generate_content_key(project_name, project_id)
        
        if content_key in self.extracted_content_store:
            del self.extracted_content_store[content_key]
            if self.debug:
                print(f"Deleted content for project {project_name} ({project_id})")
            return True
        return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_projects = len(self.extracted_content_store)
        total_files = sum(item.get("file_count", 0) for item in self.extracted_content_store.values())
        total_content_length = sum(item.get("content_length", 0) for item in self.extracted_content_store.values())
        
        return {
            "total_projects": total_projects,
            "total_files": total_files,
            "total_content_length": total_content_length,
            "projects": list(self.extracted_content_store.keys())
        }


# Create a singleton instance
content_storage_service = ContentStorageService()
