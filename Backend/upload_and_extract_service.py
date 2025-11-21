import os
import tempfile
from typing import List, Dict, Any
from datetime import datetime
import PyPDF2
from docx import Document
from google.cloud import storage
from fastapi import HTTPException, UploadFile


class UploadAndExtractService:
    """Service for handling file uploads and text extraction."""
    
    def __init__(self):
        # Load environment variables
        self.google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT", "medassureaiproject")
        self.google_cloud_bucket = os.getenv("GOOGLE_CLOUD_BUCKET", "medassure-ai-documents")
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB default
        
        # Handle both MIME types and simplified extensions
        allowed_file_types_env = os.getenv(
            "ALLOWED_FILE_TYPES", 
            "application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # Map simplified extensions to MIME types for backward compatibility
        extension_to_mime = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        
        self.allowed_file_types = []
        for file_type in allowed_file_types_env.split(","):
            file_type = file_type.strip()
            if file_type in extension_to_mime:
                # If it's a simplified extension, convert to MIME type
                self.allowed_file_types.append(extension_to_mime[file_type])
            else:
                # If it's already a MIME type, keep as is
                self.allowed_file_types.append(file_type)
        
        self.max_text_length = int(os.getenv("MAX_TEXT_LENGTH", "1048576"))  # 1MB default
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        
        # Initialize Google Cloud Storage client
        try:
            self.storage_client = storage.Client(project=self.google_cloud_project)
            self.bucket = self.storage_client.bucket(self.google_cloud_bucket)
            if self.debug:
                print(f"Initialized Google Cloud Storage with project: {self.google_cloud_project}, bucket: {self.google_cloud_bucket}")
        except Exception as e:
            if self.debug:
                print(f"Warning: Could not initialize Google Cloud Storage: {e}")
            self.storage_client = None
            self.bucket = None
    
    def validate_files(self, files: List[UploadFile]) -> None:
        """Validate uploaded files for type and size."""
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        for file in files:
            # Validate file type
            if file.content_type not in self.allowed_file_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} has unsupported type: {file.content_type}. "
                           f"Allowed types: {', '.join(self.allowed_file_types)}"
                )
            
            # Validate file size
            if file.size and file.size > self.max_file_size:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} is too large. "
                           f"Maximum size: {self.max_file_size / 1024 / 1024:.1f}MB"
                )
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error extracting text from PDF: {str(e)}"
            )
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error extracting text from DOCX: {str(e)}"
            )
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """Extract text based on file type."""
        if file_type == "application/pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self.extract_text_from_docx(file_path)
        else:
            return ""
    
    def upload_file_to_cloud_storage(self, file_path: str, destination_blob_name: str) -> bool:
        """Upload file to Google Cloud Storage."""
        if not self.storage_client or not self.bucket:
            if self.debug:
                print("Cloud storage not available, file stored locally only")
            return True
        
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(file_path)
            if self.debug:
                print(f"File uploaded to cloud storage: {destination_blob_name}")
            return True
        except Exception as e:
            if self.debug:
                print(f"Error uploading to cloud storage: {e}")
            return False
    
    async def process_files(
        self, 
        files: List[UploadFile], 
        project_name: str, 
        project_id: str
    ) -> Dict[str, Any]:
        """Process uploaded files: validate, extract text, and upload to cloud storage."""
        
        # Validate files first
        self.validate_files(files)
        
        processed_files = []
        all_extracted_text = ""
        
        for file in files:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Extract text based on file type
                extracted_text = self.extract_text_from_file(temp_file_path, file.content_type) #type:ignore
                
                # Limit text length
                if len(extracted_text) > self.max_text_length:
                    truncated_text = extracted_text[:self.max_text_length]
                    extracted_text = truncated_text + "... [Text truncated due to length limit]"
                
                # Upload to cloud storage
                destination_path = f"{project_name}_{project_id}/{file.filename}"
                
                if self.debug:
                    print(f"Generated folder path for project: {project_name}_{project_id}")
                    print(f"Project ID: {project_id}")
                
                upload_success = self.upload_file_to_cloud_storage(temp_file_path, destination_path)
                
                processed_files.append({
                    "filename": file.filename,
                    "size": len(content),
                    "type": file.content_type,
                    "cloud_path": destination_path if upload_success else None,
                    "text_length": len(extracted_text),
                    "upload_success": upload_success
                })
                
                all_extracted_text += f"\n\n--- Content from {file.filename} ---\n{extracted_text}"
                
                if self.debug:
                    print(f"Processed file: {file.filename}, extracted {len(extracted_text)} characters")
                
            except Exception as e:
                if self.debug:
                    print(f"Error processing file {file.filename}: {str(e)}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error processing file {file.filename}: {str(e)}"
                )
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
        
        return {
            "processed_files": processed_files,
            "extracted_content": all_extracted_text.strip(),
            "total_files": len(processed_files),
            "total_text_length": len(all_extracted_text.strip())
        }


# Create a singleton instance
upload_extract_service = UploadAndExtractService()