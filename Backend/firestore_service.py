"""
Firestore Service for MedAssure AI Backend
Provides direct Firestore operations for project hierarchy management
Based on the MCP server firestore_client.py but adapted for synchronous backend use
"""

import os
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import logging
from uuid import uuid4
import re

try:
    from google.cloud import firestore
    from google.oauth2 import service_account
    from google.api_core.exceptions import NotFound, PermissionDenied, AlreadyExists
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Simplified models for backend use (without Pydantic complexity)
class ProjectStatus:
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"
    ARCHIVED = "Archived"

class JiraStatus:
    NOT_PUSHED = "Not Pushed"
    PUSHED = "Pushed"
    SYNCED = "Synced"
    FAILED = "Failed"
    PENDING = "Pending"

class FirestoreService:
    def __init__(self):
        self.client: Optional[firestore.Client] = None
        self.project_id = os.getenv("FIRESTORE_PROJECT_ID", "medassureaiproject")
        self.database_name = os.getenv("FIRESTORE_DATABASE_NAME", "medassureaifirestoredb")
        self.credentials_path = os.getenv("FIRESTORE_CREDENTIALS_PATH")
        self.projects_collection = os.getenv("FIRESTORE_PROJECTS_COLLECTION", "testcase_projects")
        
        if FIRESTORE_AVAILABLE:
            self._initialize_client()
        else:
            logger.warning("Firestore libraries not available. Install with: pip install google-cloud-firestore")

    def _initialize_client(self) -> None:
        """Initialize Firestore client with proper credentials"""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(self.credentials_path)
                self.client = firestore.Client(
                    project=self.project_id, 
                    credentials=credentials,
                    database=self.database_name
                )
                logger.info(f"Firestore client initialized with service account for project: {self.project_id}, database: {self.database_name}")
            else:
                # Use default credentials (useful in Cloud environments)
                self.client = firestore.Client(
                    project=self.project_id,
                    database=self.database_name
                )
                logger.info(f"Firestore client initialized with default credentials for project: {self.project_id}, database: {self.database_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if Firestore service is available"""
        return FIRESTORE_AVAILABLE and self.client is not None

    def _generate_id(self, prefix: str = "") -> str:
        """Generate unique ID with optional prefix"""
        return f"{prefix}{uuid4().hex[:8]}" if prefix else uuid4().hex[:8]
    
    def _update_timestamps(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update timestamps in data"""
        data['updated_at'] = datetime.utcnow()
        return data

    def _ensure_project_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure project has the required structure"""
        # Set defaults
        data.setdefault('project_name', '')
        data.setdefault('description', '')
        data.setdefault('status', ProjectStatus.ACTIVE)
        data.setdefault('compliance_frameworks', [])
        data.setdefault('epics', [])
        data.setdefault('coverage_summary', None)
        data.setdefault('jira_project_key', None)
        data.setdefault('jira_project_url', None)
        data.setdefault('created_by', None)
        data.setdefault('created_at', datetime.utcnow())
        data.setdefault('updated_at', datetime.utcnow())
        
        return data

    # ================================
    # PROJECT OPERATIONS
    # ================================

    def create_project(self, project_data: Dict[str, Any], created_by: Optional[str] = None) -> str:
        """Create a new project"""
        if not self.is_available() or self.client is None:
            raise Exception("Firestore service not available")

        try:
            # Use provided project_id if available, otherwise generate one
            project_id = project_data.get('project_id') or self._generate_id("PROJ_")
            
            # Prepare project data
            project = {
                'project_id': project_id,
                'project_name': project_data.get('project_name', ''),
                'description': project_data.get('description', ''),
                'status': ProjectStatus.ACTIVE,
                'compliance_frameworks': project_data.get('compliance_frameworks', []),
                'epics': project_data.get('epics', []),
                'coverage_summary': None,
                'jira_project_key': project_data.get('jira_project_key'),
                'jira_project_url': None,
                'notification_email': project_data.get('notification_email'),
                'created_by': created_by,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Store in Firestore
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc_ref.set(project)
            
            logger.info(f"Created project: {project_id}")
            return project_id
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects from Firestore"""
        if not self.is_available() or self.client is None:
            return []

        try:
            collection_ref = self.client.collection(self.projects_collection)
            docs = collection_ref.stream()
            
            projects = []
            for doc in docs:
                project_data = doc.to_dict()
                if project_data:
                    project_data['project_id'] = doc.id
                    
                    # Calculate totals
                    total_epics = len(project_data.get('epics', []))
                    total_features = 0
                    total_use_cases = 0
                    total_test_cases = 0
                    
                    # Count features, use cases, and test cases
                    for epic in project_data.get('epics', []):
                        for feature in epic.get('features', []):
                            total_features += 1
                            for use_case in feature.get('use_cases', []):
                                total_use_cases += 1
                                total_test_cases += len(use_case.get('test_cases', []))
                    
                    projects.append({
                        'project_id': doc.id,
                        'project_name': project_data.get('project_name', ''),
                        'description': project_data.get('description', ''),
                        'created_at': project_data.get('created_at', ''),
                        'last_updated': project_data.get('updated_at', ''),
                        'total_epics': total_epics,
                        'total_features': total_features,
                        'total_use_cases': total_use_cases,
                        'total_test_cases': total_test_cases,
                        'status': project_data.get('status', 'active')
                    })
            
            return projects
        except Exception as e:
            logger.error(f"Error fetching all projects: {e}")
            return []

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific project by ID"""
        if not self.is_available() or self.client is None:
            return None

        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if doc.exists:
                project_data = doc.to_dict()
                if project_data:
                    project_data['project_id'] = doc.id
                    return project_data
            return None
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Error fetching project {project_id}: {e}")
            return None

    def update_project(self, project_id: str, update_data: Dict[str, Any], updated_by: Optional[str] = None) -> bool:
        """Update an existing project"""
        if not self.is_available() or self.client is None:
            return False

        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            # Prepare update data
            update_data['updated_at'] = datetime.utcnow()
            if updated_by:
                update_data['updated_by'] = updated_by
            
            # Update in Firestore
            doc_ref.update(update_data)
            
            logger.info(f"Updated project: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return False

    def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        if not self.is_available() or self.client is None:
            return False

        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            # Delete the project document
            doc_ref.delete()
            
            logger.info(f"Deleted project: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            return False

    def list_projects(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List projects with optional filtering"""
        if not self.is_available() or self.client is None:
            return []

        try:
            query = self.client.collection(self.projects_collection)
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    query = query.where("status", "==", filters['status'])
                if filters.get('created_after'):
                    query = query.where("created_at", ">=", filters['created_after'])
                if filters.get('created_before'):
                    query = query.where("created_at", "<=", filters['created_before'])
            
            # Apply limit and ordering
            query = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
            
            # Execute query
            docs = query.stream()
            
            projects = []
            for doc in docs:
                project_data = doc.to_dict()
                if project_data:
                    project_data['project_id'] = doc.id
                    
                    # Apply text search filter if specified
                    if filters and filters.get('text_search'):
                        search_text = filters['text_search'].lower()
                        project_name = project_data.get('project_name', '').lower()
                        description = project_data.get('description', '').lower()
                        if search_text in project_name or search_text in description:
                            projects.append(project_data)
                    else:
                        projects.append(project_data)
            
            return projects
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return []

    def get_project_statistics(self) -> Dict[str, int]:
        """Get overall statistics for all projects"""
        if not self.is_available():
            return {
                'total_projects': 0,
                'total_epics': 0,
                'total_features': 0,
                'total_use_cases': 0,
                'total_test_cases': 0
            }

        try:
            projects = self.get_all_projects()
            
            stats = {
                'total_projects': len(projects),
                'total_epics': 0,
                'total_features': 0,
                'total_use_cases': 0,
                'total_test_cases': 0
            }
            
            for project in projects:
                project_data = self.get_project_by_id(project['project_id'])
                if project_data:
                    for epic in project_data.get('epics', []):
                        stats['total_epics'] += 1
                        for feature in epic.get('features', []):
                            stats['total_features'] += 1
                            for use_case in feature.get('use_cases', []):
                                stats['total_use_cases'] += 1
                                stats['total_test_cases'] += len(use_case.get('test_cases', []))
            
            return stats
        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            return {
                'total_projects': 0,
                'total_epics': 0,
                'total_features': 0,
                'total_use_cases': 0,
                'total_test_cases': 0
            }

    def get_model_explanation(self, project_id: str, item_type: str, item_id: str) -> Optional[str]:
        """Get model explanation for a specific item"""
        project = self.get_project_by_id(project_id)
        if not project:
            return None

        try:
            if item_type == "project":
                return project.get('model_explanation', '')
            
            elif item_type == "epic":
                for epic in project.get('epics', []):
                    if epic.get('epic_id') == item_id:
                        return epic.get('model_explanation', '')
            
            elif item_type == "feature":
                for epic in project.get('epics', []):
                    for feature in epic.get('features', []):
                        if feature.get('feature_id') == item_id:
                            return feature.get('model_explanation', '')
            
            elif item_type == "use_case":
                for epic in project.get('epics', []):
                    for feature in epic.get('features', []):
                        for use_case in feature.get('use_cases', []):
                            if use_case.get('use_case_id') == item_id:
                                return use_case.get('model_explanation', '')
            
            elif item_type == "test_case":
                for epic in project.get('epics', []):
                    for feature in epic.get('features', []):
                        for use_case in feature.get('use_cases', []):
                            for test_case in use_case.get('test_cases', []):
                                if test_case.get('test_case_id') == item_id:
                                    return test_case.get('model_explanation', '')
            
            return None
        except Exception as e:
            logger.error(f"Error getting model explanation: {e}")
            return None

    # ================================
    # UTILITY METHODS
    # ================================

    def _calculate_total_test_cases(self, project_data: Dict[str, Any]) -> int:
        """Calculate total test cases in a project"""
        total = 0
        for epic in project_data.get('epics', []):
            for feature in epic.get('features', []):
                for use_case in feature.get('use_cases', []):
                    total += len(use_case.get('test_cases', []))
        return total

    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """Search projects by name or description"""
        return self.list_projects({'text_search': query})

# Global instance
firestore_service = FirestoreService()