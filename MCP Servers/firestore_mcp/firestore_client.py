"""
Firestore client for Test Case Management System

This module provides comprehensive CRUD operations for managing test projects,
epics, features, use cases, and test cases in Google Cloud Firestore.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import uuid4

from google.cloud import firestore
from google.api_core.exceptions import NotFound, AlreadyExists
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import (
    Project, Epic, Feature, UseCase, TestCase,
    ProjectSummary, CreateProjectRequest, UpdateProjectRequest,
    SearchFilter, BulkOperationResult, JiraStatus, ProjectStatus
)

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Firestore client for test case management operations"""
    
    def __init__(self):
        """Initialize Firestore client"""
        self.client = firestore.Client(
            project=os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0182599221"),
            database=os.getenv("FIRESTORE_DATABASE_Name", "medassureaifirestoredb")
        )
        self.projects_collection = os.getenv("PROJECTS_COLLECTION", "testcase_projects")
        
    def _generate_id(self, prefix: str = "") -> str:
        """Generate unique ID with optional prefix"""
        return f"{prefix}{uuid4().hex[:8]}" if prefix else uuid4().hex[:8]
    
    def _update_timestamps(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update timestamps in data"""
        data['updated_at'] = datetime.utcnow()
        return data
    
    def _safe_get_project_data(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Safely get project data from Firestore"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            project_data = doc.to_dict()
            return project_data if project_data else None
            
        except Exception as e:
            logger.error(f"Error getting project data for {project_id}: {e}")
            return None
    
    def _create_project_from_dict(self, data: Optional[Dict[str, Any]], project_id: Optional[str] = None) -> Optional[Project]:
        """Create Project instance from Firestore dictionary data"""
        if not data:
            return None
        
        # Ensure required fields are present
        if project_id:
            data.setdefault('project_id', project_id)
        data.setdefault('project_name', '')
        data.setdefault('description', None)
        data.setdefault('status', ProjectStatus.ACTIVE)
        data.setdefault('coverage_summary', None)
        data.setdefault('jira_project_key', None)
        data.setdefault('jira_project_url', None)
        data.setdefault('created_by', None)
        
        return Project(**data)
    
    def get_current_timestamp(self):
        """Get current timestamp"""
        return datetime.utcnow()
    
    def update_project_simple(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project with dictionary data"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"Project {project_id} not found for update")
                return False
            
            # Update the document
            doc_ref.update(updates)
            logger.info(f"Updated project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return False
    
    # ================================
    # PROJECT OPERATIONS
    # ================================
    
    def create_project(self, project_data: Dict[str, Any]) -> str:
        """Create a new project from dictionary data"""
        try:
            project_id = self._generate_id("PROJ_")
            
            # Add metadata
            project_data["project_id"] = project_id
            project_data["created_at"] = datetime.utcnow()
            project_data["updated_at"] = datetime.utcnow()
            
            # Store in Firestore
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc_ref.set(project_data)
            
            logger.info(f"Created project: {project_id}")
            return project_id
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    async def create_project_async(self, request: CreateProjectRequest, created_by: Optional[str] = None) -> Project:
        """Create a new project"""
        try:
            project_id = self._generate_id("PROJ_")
            
            project = Project(
                project_id=project_id,
                project_name=request.project_name,
                description=request.description,
                compliance_frameworks=request.compliance_frameworks,
                jira_project_key=request.jira_project_key,
                status=ProjectStatus.ACTIVE,
                coverage_summary=None,
                jira_project_url=None,
                created_by=created_by
            )
            
            # Store in Firestore
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc_ref.set(project.dict())
            
            logger.info(f"Created project: {project_id}")
            return project
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return self._create_project_from_dict(data, project_id)
            return None
            
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            raise
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects from Firestore"""
        try:
            docs = self.client.collection(self.projects_collection).stream()
            projects = []
            
            for doc in docs:
                project_data = doc.to_dict()
                project_data['project_id'] = doc.id
                projects.append(project_data)
            
            logger.info(f"Retrieved {len(projects)} projects")
            return projects
            
        except Exception as e:
            logger.error(f"Error getting all projects: {e}")
            raise
    
    def search_projects(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search projects with text query and filters"""
        try:
            collection_ref = self.client.collection(self.projects_collection)
            
            # Start with all projects
            query_ref = collection_ref
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if value:  # Only apply non-empty filters
                        if field == "compliance_frameworks":
                            # Search in array field
                            query_ref = query_ref.where(field, "array_contains", value)
                        else:
                            # Exact match for other fields
                            query_ref = query_ref.where(field, "==", value)
            
            # Execute query
            docs = query_ref.stream()
            projects = []
            
            for doc in docs:
                project_data = doc.to_dict()
                project_data['project_id'] = doc.id
                
                # Apply text search if query provided
                if query:
                    # Search in project_name and description
                    project_name = project_data.get('project_name', '').lower()
                    description = project_data.get('description', '').lower()
                    search_query = query.lower()
                    
                    if search_query in project_name or search_query in description:
                        projects.append(project_data)
                else:
                    projects.append(project_data)
            
            logger.info(f"Search returned {len(projects)} projects")
            return projects
            
        except Exception as e:
            logger.error(f"Error searching projects: {e}")
            raise
    
    async def update_project(self, project_id: str, request: UpdateProjectRequest, updated_by: Optional[str] = None) -> Optional[Project]:
        """Update an existing project"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            # Get current data
            current_data = doc.to_dict()
            
            # Update only provided fields
            update_data = {}
            if request.project_name is not None:
                update_data['project_name'] = request.project_name
            if request.description is not None:
                update_data['description'] = request.description
            if request.status is not None:
                update_data['status'] = request.status.value
            if request.compliance_frameworks is not None:
                update_data['compliance_frameworks'] = request.compliance_frameworks
            
            # Add metadata
            update_data['updated_at'] = datetime.utcnow()
            if updated_by:
                update_data['updated_by'] = updated_by
            
            # Update in Firestore
            doc_ref.update(update_data)
            
            # Return updated project
            updated_doc = doc_ref.get()
            data = updated_doc.to_dict()
            return self._create_project_from_dict(data, project_id)
            
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            raise
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its data"""
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
            raise
    
    async def list_projects(self, filters: Optional[SearchFilter] = None, limit: int = 100) -> List[ProjectSummary]:
        """List projects with optional filtering"""
        try:
            query = self.client.collection(self.projects_collection)
            
            # Apply filters
            if filters:
                if filters.status:
                    query = query.where("status", "==", filters.status.value)
                if filters.created_after:
                    query = query.where("created_at", ">=", filters.created_after)
                if filters.created_before:
                    query = query.where("created_at", "<=", filters.created_before)
            
            # Apply limit and ordering
            query = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
            
            # Execute query
            docs = query.stream()
            
            summaries = []
            for doc in docs:
                data = doc.to_dict()
                project = Project(**data)
                
                # Calculate counts
                epic_count = len(project.epics)
                feature_count = sum(len(epic.features) for epic in project.epics)
                use_case_count = sum(len(feature.use_cases) for epic in project.epics for feature in epic.features)
                test_case_count = sum(len(use_case.test_cases) for epic in project.epics for feature in epic.features for use_case in feature.use_cases)
                
                summary = ProjectSummary(
                    project_id=project.project_id,
                    project_name=project.project_name,
                    status=project.status,
                    epic_count=epic_count,
                    feature_count=feature_count,
                    use_case_count=use_case_count,
                    test_case_count=test_case_count,
                    created_at=project.created_at,
                    updated_at=project.updated_at
                )
                
                # Apply text search filter if specified
                if filters and filters.text_search:
                    search_text = filters.text_search.lower()
                    if (search_text in project.project_name.lower() or 
                        (project.description and search_text in project.description.lower())):
                        summaries.append(summary)
                else:
                    summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            raise
    
    # ================================
    # EPIC OPERATIONS
    # ================================
    
    def get_project_epics(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all epics for a project"""
        try:
            project_data = self._safe_get_project_data(project_id)
            if not project_data:
                return []
                
            epics = project_data.get('epics', [])
            
            logger.info(f"Retrieved {len(epics)} epics for project {project_id}")
            return epics
            
        except Exception as e:
            logger.error(f"Error getting epics for project {project_id}: {e}")
            return []
    
    def add_epic_to_project(self, project_id: str, epic_data: Dict[str, Any]) -> str:
        """Add an epic to a project (simple version)"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                raise ValueError(f"Project {project_id} not found")
            
            project_data = doc.to_dict()
            if not project_data:
                raise ValueError(f"Project {project_id} has no data")
                
            epics = project_data.get('epics', [])
            
            # Generate epic ID if not provided
            if not epic_data.get('epic_id'):
                epic_data['epic_id'] = self._generate_id("EPIC_")
            
            # Add timestamps
            epic_data['created_at'] = datetime.utcnow()
            epic_data['updated_at'] = datetime.utcnow()
            
            # Add epic to list
            epics.append(epic_data)
            
            # Update project with new epic
            doc_ref.update({'epics': epics, 'updated_at': datetime.utcnow()})
            
            logger.info(f"Added epic {epic_data['epic_id']} to project {project_id}")
            return epic_data['epic_id']
            
        except Exception as e:
            logger.error(f"Error adding epic to project {project_id}: {e}")
            raise
    
    async def add_epic_to_project_async(self, project_id: str, epic: Epic) -> bool:
        """Add an epic to a project"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            project_data = doc.to_dict()
            project = self._create_project_from_dict(project_data, project_id)
            
            if not project:
                return False
            
            # Add epic
            epic.epic_id = epic.epic_id or self._generate_id("E")
            project.epics.append(epic)
            
            # Update project
            project.updated_at = datetime.utcnow()
            doc_ref.update({"epics": [epic.dict() for epic in project.epics], "updated_at": project.updated_at})
            
            logger.info(f"Added epic {epic.epic_id} to project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding epic to project {project_id}: {e}")
            raise
    
    async def update_epic(self, project_id: str, epic_id: str, updated_epic: Epic) -> bool:
        """Update an epic in a project"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            project_data = doc.to_dict()
            project = self._create_project_from_dict(project_data, project_id)
            
            if not project:
                return False
            
            # Find and update epic
            for i, epic in enumerate(project.epics):
                if epic.epic_id == epic_id:
                    updated_epic.updated_at = datetime.utcnow()
                    project.epics[i] = updated_epic
                    break
            else:
                return False
            
            # Update project
            project.updated_at = datetime.utcnow()
            doc_ref.update({"epics": [epic.dict() for epic in project.epics], "updated_at": project.updated_at})
            
            logger.info(f"Updated epic {epic_id} in project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating epic {epic_id} in project {project_id}: {e}")
            raise
    
    async def delete_epic(self, project_id: str, epic_id: str) -> bool:
        """Delete an epic from a project"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            project_data = doc.to_dict()
            project = self._create_project_from_dict(project_data, project_id)
            
            if not project:
                return False
            
            # Remove epic
            original_count = len(project.epics)
            project.epics = [epic for epic in project.epics if epic.epic_id != epic_id]
            
            if len(project.epics) == original_count:
                return False  # Epic not found
            
            # Update project
            project.updated_at = datetime.utcnow()
            doc_ref.update({"epics": [epic.dict() for epic in project.epics], "updated_at": project.updated_at})
            
            logger.info(f"Deleted epic {epic_id} from project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting epic {epic_id} from project {project_id}: {e}")
            raise
    
    async def update_epic_jira_status(self, project_id: str, epic_id: str, jira_status: JiraStatus, jira_key: Optional[str] = None) -> bool:
        """Update Jira status for an epic"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            project_data = doc.to_dict()
            project = self._create_project_from_dict(project_data, project_id)
            
            if not project:
                return False
            
            # Find and update epic
            for epic in project.epics:
                if epic.epic_id == epic_id:
                    epic.jira_status = jira_status
                    if jira_key:
                        epic.jira_epic_key = jira_key
                    if jira_status == JiraStatus.PUSHED:
                        epic.jira_pushed_at = datetime.utcnow()
                    epic.updated_at = datetime.utcnow()
                    break
            else:
                return False
            
            # Update project
            project.updated_at = datetime.utcnow()
            doc_ref.update({"epics": [epic.dict() for epic in project.epics], "updated_at": project.updated_at})
            
            logger.info(f"Updated Jira status for epic {epic_id} to {jira_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Jira status for epic {epic_id}: {e}")
            raise
    
    # ================================
    # FEATURE OPERATIONS
    # ================================
    
    def get_epic_features(self, project_id: str, epic_id: str) -> List[Dict[str, Any]]:
        """Get all features for an epic"""
        try:
            project_data = self._safe_get_project_data(project_id)
            if not project_data:
                return []
            
            epics = project_data.get('epics', [])
            
            # Find the epic
            for epic in epics:
                if epic.get('epic_id') == epic_id:
                    features = epic.get('features', [])
                    logger.info(f"Retrieved {len(features)} features for epic {epic_id}")
                    return features
            
            logger.warning(f"Epic {epic_id} not found in project {project_id}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting features for epic {epic_id}: {e}")
            return []
    
    def add_feature_to_epic(self, project_id: str, epic_id: str, feature_data: Dict[str, Any]) -> str:
        """Add a feature to an epic (simple version)"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                raise ValueError(f"Project {project_id} not found")
            
            project_data = doc.to_dict()
            if not project_data:
                raise ValueError(f"Project {project_id} has no data")
                
            epics = project_data.get('epics', [])
            
            # Find and update the epic
            epic_found = False
            for epic in epics:
                if epic.get('epic_id') == epic_id:
                    epic_found = True
                    features = epic.get('features', [])
                    
                    # Generate feature ID if not provided
                    if not feature_data.get('feature_id'):
                        feature_data['feature_id'] = self._generate_id("FEAT_")
                    
                    # Add timestamps
                    feature_data['created_at'] = datetime.utcnow()
                    feature_data['updated_at'] = datetime.utcnow()
                    
                    # Add feature to epic
                    features.append(feature_data)
                    epic['features'] = features
                    epic['updated_at'] = datetime.utcnow()
                    break
            
            if not epic_found:
                raise ValueError(f"Epic {epic_id} not found in project {project_id}")
            
            # Update project with modified epics
            doc_ref.update({'epics': epics, 'updated_at': datetime.utcnow()})
            
            logger.info(f"Added feature {feature_data['feature_id']} to epic {epic_id}")
            return feature_data['feature_id']
            
        except Exception as e:
            logger.error(f"Error adding feature to epic {epic_id}: {e}")
            raise
    
    async def add_feature_to_epic_async(self, project_id: str, epic_id: str, feature: Feature) -> bool:
        """Add a feature to an epic"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            project_data = doc.to_dict()
            project = self._create_project_from_dict(project_data, project_id)
            
            if not project:
                return False
            
            # Find epic and add feature
            for epic in project.epics:
                if epic.epic_id == epic_id:
                    feature.feature_id = feature.feature_id or self._generate_id("F")
                    epic.features.append(feature)
                    epic.updated_at = datetime.utcnow()
                    break
            else:
                return False
            
            # Update project
            project.updated_at = datetime.utcnow()
            doc_ref.update({"epics": [epic.dict() for epic in project.epics], "updated_at": project.updated_at})
            
            logger.info(f"Added feature {feature.feature_id} to epic {epic_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding feature to epic {epic_id}: {e}")
            raise
    
    # ================================
    # USE CASE OPERATIONS
    # ================================
    
    def get_feature_use_cases(self, project_id: str, epic_id: str, feature_id: str) -> List[Dict[str, Any]]:
        """Get all use cases for a feature"""
        try:
            project_data = self._safe_get_project_data(project_id)
            if not project_data:
                return []
            
            epics = project_data.get('epics', [])
            
            # Find the epic and feature
            for epic in epics:
                if epic.get('epic_id') == epic_id:
                    features = epic.get('features', [])
                    for feature in features:
                        if feature.get('feature_id') == feature_id:
                            use_cases = feature.get('use_cases', [])
                            logger.info(f"Retrieved {len(use_cases)} use cases for feature {feature_id}")
                            return use_cases
            
            logger.warning(f"Feature {feature_id} not found in epic {epic_id}, project {project_id}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting use cases for feature {feature_id}: {e}")
            return []
    
    def add_use_case_to_feature(self, project_id: str, epic_id: str, feature_id: str, use_case_data: Dict[str, Any]) -> str:
        """Add a use case to a feature (simple version)"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                raise ValueError(f"Project {project_id} not found")
            
            project_data = doc.to_dict()
            if not project_data:
                raise ValueError(f"Project {project_id} has no data")
                
            epics = project_data.get('epics', [])
            
            # Find and update the epic and feature
            epic_found = False
            feature_found = False
            
            for epic in epics:
                if epic.get('epic_id') == epic_id:
                    epic_found = True
                    features = epic.get('features', [])
                    
                    for feature in features:
                        if feature.get('feature_id') == feature_id:
                            feature_found = True
                            use_cases = feature.get('use_cases', [])
                            
                            # Generate use case ID if not provided
                            if not use_case_data.get('use_case_id'):
                                use_case_data['use_case_id'] = self._generate_id("UC_")
                            
                            # Add timestamps
                            use_case_data['created_at'] = datetime.utcnow()
                            use_case_data['updated_at'] = datetime.utcnow()
                            
                            # Add use case to feature
                            use_cases.append(use_case_data)
                            feature['use_cases'] = use_cases
                            feature['updated_at'] = datetime.utcnow()
                            break
                    
                    if feature_found:
                        epic['updated_at'] = datetime.utcnow()
                        break
            
            if not epic_found:
                raise ValueError(f"Epic {epic_id} not found in project {project_id}")
            if not feature_found:
                raise ValueError(f"Feature {feature_id} not found in epic {epic_id}")
            
            # Update project with modified epics
            doc_ref.update({'epics': epics, 'updated_at': datetime.utcnow()})
            
            logger.info(f"Added use case {use_case_data['use_case_id']} to feature {feature_id}")
            return use_case_data['use_case_id']
            
        except Exception as e:
            logger.error(f"Error adding use case to feature {feature_id}: {e}")
            raise
    
    async def add_use_case_to_feature_async(self, project_id: str, epic_id: str, feature_id: str, use_case: UseCase) -> bool:
        """Add a use case to a feature"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            project_data = doc.to_dict()
            project = self._create_project_from_dict(project_data, project_id)
            
            if not project:
                return False
            
            # Find feature and add use case
            for epic in project.epics:
                if epic.epic_id == epic_id:
                    for feature in epic.features:
                        if feature.feature_id == feature_id:
                            use_case.use_case_id = use_case.use_case_id or self._generate_id("UC")
                            feature.use_cases.append(use_case)
                            feature.updated_at = datetime.utcnow()
                            epic.updated_at = datetime.utcnow()
                            break
                    break
            else:
                return False
            
            # Update project
            project.updated_at = datetime.utcnow()
            doc_ref.update({"epics": [epic.dict() for epic in project.epics], "updated_at": project.updated_at})
            
            logger.info(f"Added use case {use_case.use_case_id} to feature {feature_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding use case to feature {feature_id}: {e}")
            raise
    
    # ================================
    # TEST CASE OPERATIONS
    # ================================
    
    def add_test_case_to_use_case(self, project_id: str, epic_id: str, feature_id: str, use_case_id: str, 
                                 test_case_title: str, test_steps: List[str], expected_result: str, 
                                 test_type: str = "Functional", additional_fields: Optional[Dict[str, Any]] = None) -> str:
        """Add a test case to a use case (simple version)"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                raise ValueError(f"Project {project_id} not found")
            
            project_data = doc.to_dict()
            if not project_data:
                raise ValueError(f"Project {project_id} has no data")
                
            epics = project_data.get('epics', [])
            
            # Find the epic, feature, and use case
            epic_found = False
            feature_found = False
            use_case_found = False
            
            for epic in epics:
                if epic.get('epic_id') == epic_id:
                    epic_found = True
                    features = epic.get('features', [])
                    
                    for feature in features:
                        if feature.get('feature_id') == feature_id:
                            feature_found = True
                            use_cases = feature.get('use_cases', [])
                            
                            for use_case in use_cases:
                                if use_case.get('use_case_id') == use_case_id:
                                    use_case_found = True
                                    test_cases = use_case.get('test_cases', [])
                                    
                                    # Create test case data with core fields
                                    test_case_data = {
                                        'test_case_id': self._generate_id("TC_"),
                                        'test_case_title': test_case_title,
                                        'test_steps': test_steps,
                                        'expected_result': expected_result,
                                        'test_type': test_type,
                                        'created_at': datetime.utcnow(),
                                        'updated_at': datetime.utcnow()
                                    }
                                    
                                    # Add additional fields if provided
                                    if additional_fields:
                                        test_case_data.update(additional_fields)
                                    
                                    # Add test case to use case
                                    test_cases.append(test_case_data)
                                    use_case['test_cases'] = test_cases
                                    use_case['updated_at'] = datetime.utcnow()
                                    break
                            
                            if use_case_found:
                                feature['updated_at'] = datetime.utcnow()
                                break
                    
                    if feature_found:
                        epic['updated_at'] = datetime.utcnow()
                        break
            
            if not epic_found:
                raise ValueError(f"Epic {epic_id} not found in project {project_id}")
            if not feature_found:
                raise ValueError(f"Feature {feature_id} not found in epic {epic_id}")
            if not use_case_found:
                raise ValueError(f"Use case {use_case_id} not found in feature {feature_id}")
            
            # Update project with modified epics
            doc_ref.update({'epics': epics, 'updated_at': datetime.utcnow()})
            
            test_case_id = test_case_data['test_case_id']
            logger.info(f"Added test case {test_case_id} to use case {use_case_id}")
            return test_case_id
            
        except Exception as e:
            logger.error(f"Error adding test case to use case {use_case_id}: {e}")
            raise
    
    async def add_test_case_to_use_case_async(self, project_id: str, epic_id: str, feature_id: str, use_case_id: str, test_case: TestCase) -> bool:
        """Add a test case to a use case"""
        try:
            doc_ref = self.client.collection(self.projects_collection).document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            project_data = doc.to_dict()
            project = self._create_project_from_dict(project_data, project_id)
            
            if not project:
                return False
            
            # Find use case and add test case
            for epic in project.epics:
                if epic.epic_id == epic_id:
                    for feature in epic.features:
                        if feature.feature_id == feature_id:
                            for use_case in feature.use_cases:
                                if use_case.use_case_id == use_case_id:
                                    test_case.test_case_id = test_case.test_case_id or self._generate_id("TC")
                                    use_case.test_cases.append(test_case)
                                    use_case.updated_at = datetime.utcnow()
                                    feature.updated_at = datetime.utcnow()
                                    epic.updated_at = datetime.utcnow()
                                    break
                            break
                    break
            else:
                return False
            
            # Update project
            project.updated_at = datetime.utcnow()
            doc_ref.update({"epics": [epic.dict() for epic in project.epics], "updated_at": project.updated_at})
            
            logger.info(f"Added test case {test_case.test_case_id} to use case {use_case_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding test case to use case {use_case_id}: {e}")
            raise
    
    # ================================
    # BULK OPERATIONS
    # ================================
    
    async def bulk_create_from_structure(self, project_id: str, structure_data: Dict[str, Any]) -> BulkOperationResult:
        """Create project structure from generated test case data"""
        try:
            result = BulkOperationResult()
            
            # Get or create project
            project = await self.get_project(project_id)
            if not project:
                return result
            
            # Process epics from structure
            if 'epics' in structure_data:
                for epic_data in structure_data['epics']:
                    try:
                        epic = Epic(**epic_data)
                        success = await self.add_epic_to_project_async(project_id, epic)
                        if success:
                            result.success_count += 1
                            result.processed_ids.append(epic.epic_id)
                        else:
                            result.error_count += 1
                            result.errors.append({"epic_id": epic.epic_id, "error": "Failed to add epic"})
                    except Exception as e:
                        result.error_count += 1
                        result.errors.append({"epic_data": epic_data, "error": str(e)})
            
            # Update coverage summary if provided
            if 'coverage_summary' in structure_data:
                doc_ref = self.client.collection(self.projects_collection).document(project_id)
                doc_ref.update({"coverage_summary": structure_data['coverage_summary']})
            
            logger.info(f"Bulk create completed: {result.success_count} success, {result.error_count} errors")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk create operation: {e}")
            raise
    
    # ================================
    # SEARCH AND ANALYTICS
    # ================================
    
    async def search_test_cases(self, project_id: str, search_term: str) -> List[Dict[str, Any]]:
        """Search test cases within a project"""
        try:
            project = await self.get_project(project_id)
            if not project:
                return []
            
            results = []
            search_term_lower = search_term.lower()
            
            for epic in project.epics:
                for feature in epic.features:
                    for use_case in feature.use_cases:
                        for test_case in use_case.test_cases:
                            # Search in test case fields
                            if (search_term_lower in test_case.title.lower() or
                                search_term_lower in test_case.test_case_id.lower() or
                                (test_case.description and search_term_lower in test_case.description.lower())):
                                
                                results.append({
                                    "project_id": project_id,
                                    "epic_id": epic.epic_id,
                                    "epic_name": epic.epic_name,
                                    "feature_id": feature.feature_id,
                                    "feature_name": feature.feature_name,
                                    "use_case_id": use_case.use_case_id,
                                    "use_case_title": use_case.title,
                                    "test_case": test_case.dict()
                                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching test cases: {e}")
            raise
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """Get overall statistics for all projects (simple version)"""
        try:
            docs = self.client.collection(self.projects_collection).stream()
            
            total_projects = 0
            total_epics = 0
            total_features = 0
            total_use_cases = 0
            total_test_cases = 0
            
            for doc in docs:
                total_projects += 1
                project_data = doc.to_dict()
                epics = project_data.get('epics', [])
                
                for epic in epics:
                    total_epics += 1
                    features = epic.get('features', [])
                    
                    for feature in features:
                        total_features += 1
                        use_cases = feature.get('use_cases', [])
                        
                        for use_case in use_cases:
                            total_use_cases += 1
                            test_cases = use_case.get('test_cases', [])
                            total_test_cases += len(test_cases)
            
            stats = {
                'total_projects': total_projects,
                'total_epics': total_epics,
                'total_features': total_features,
                'total_use_cases': total_use_cases,
                'total_test_cases': total_test_cases
            }
            
            logger.info(f"Generated overall statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            return {}
    
    async def get_project_statistics_async(self, project_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a project"""
        try:
            project = await self.get_project(project_id)
            if not project:
                return {}
            
            stats = {
                "project_id": project_id,
                "project_name": project.project_name,
                "epic_count": len(project.epics),
                "feature_count": 0,
                "use_case_count": 0,
                "test_case_count": 0,
                "jira_sync_stats": {
                    "pushed": 0,
                    "not_pushed": 0,
                    "failed": 0
                },
                "test_type_distribution": {},
                "compliance_coverage": set()
            }
            
            for epic in project.epics:
                # Jira sync stats
                if epic.jira_status == JiraStatus.PUSHED:
                    stats["jira_sync_stats"]["pushed"] += 1
                elif epic.jira_status == JiraStatus.FAILED:
                    stats["jira_sync_stats"]["failed"] += 1
                else:
                    stats["jira_sync_stats"]["not_pushed"] += 1
                
                stats["feature_count"] += len(epic.features)
                
                for feature in epic.features:
                    stats["use_case_count"] += len(feature.use_cases)
                    
                    for use_case in feature.use_cases:
                        stats["test_case_count"] += len(use_case.test_cases)
                        
                        # Compliance coverage
                        stats["compliance_coverage"].update(use_case.compliance_mapping)
                        
                        for test_case in use_case.test_cases:
                            # Test type distribution
                            test_type = test_case.test_type.value
                            stats["test_type_distribution"][test_type] = stats["test_type_distribution"].get(test_type, 0) + 1
                            
                            # More compliance coverage
                            stats["compliance_coverage"].update(test_case.compliance_mapping)
            
            # Convert set to list for JSON serialization
            stats["compliance_coverage"] = list(stats["compliance_coverage"])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            raise