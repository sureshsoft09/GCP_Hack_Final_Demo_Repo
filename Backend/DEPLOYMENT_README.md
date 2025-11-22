# Backend Cloud Run Deployment Guide

This guide covers deploying the MedAssure AI Backend service to Google Cloud Run.

## Prerequisites

1. **Google Cloud CLI**: Ensure `gcloud` is installed and authenticated
2. **Google Cloud Project**: Project ID `gen-lang-client-0182599221`
3. **Service Account**: `firestoreconnectserviceacc@gen-lang-client-0182599221.iam.gserviceaccount.com`
4. **Dependencies**: Agents service and MCP servers must be deployed first

## Deployment Options

### Option 1: PowerShell Script (Windows)
```powershell
./deploy.ps1
```

### Option 2: Bash Script (Linux/Mac)
```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 3: Manual gcloud Command
```bash
gcloud run deploy medassure-backend \
    --service-account=firestoreconnectserviceacc@gen-lang-client-0182599221.iam.gserviceaccount.com \
    --allow-unauthenticated \
    --region=europe-west1 \
    --source=. \
    --labels=environment=dev,service=backend \
    --memory=1Gi \
    --cpu=1 \
    --max-instances=10 \
    --min-instances=0 \
    --timeout=600 \
    --concurrency=80 \
    --project=gen-lang-client-0182599221
```

## Environment Variables

The following environment variables are configured automatically:

### Agents Integration
- `AGENTS_API_URL`: https://agents-server-518624836175.europe-west1.run.app/query
- `RESET_AGENT_SESSION_API_URL`: https://agents-server-518624836175.europe-west1.run.app/reset-session
- `AGENTS_API_TIMEOUT`: 600

### Google Cloud Storage
- `GOOGLE_CLOUD_BUCKET`: medassure-ai-documents1

### Firestore Configuration
- `FIRESTORE_PROJECT_ID`: gen-lang-client-0182599221
- `FIRESTORE_DATABASE_NAME`: medassureaifirestoredb
- `FIRESTORE_PROJECTS_COLLECTION`: testcase_projects

### File Upload Settings
- `MAX_FILE_SIZE`: 50485760 (50MB)
- `ALLOWED_FILE_TYPES`: application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document
- `MAX_TEXT_LENGTH`: 1048576 (1MB)

### Application Settings
- `ENVIRONMENT`: production
- `DEBUG`: false
- `PORT`: Set automatically by Cloud Run

## Service Configuration

- **Service Name**: medassure-backend
- **Region**: europe-west1
- **Memory**: 1Gi
- **CPU**: 1
- **Port**: 8083 (configurable via PORT env var)
- **Timeout**: 600 seconds
- **Concurrency**: 80
- **Public Access**: Enabled (--allow-unauthenticated)

## Dependencies

Key dependencies from `requirements.txt`:
- fastapi
- uvicorn
- google-cloud-storage
- google-cloud-firestore
- python-multipart
- httpx
- python-dotenv

## IAM Permissions

The service account requires:
- `roles/storage.admin` - For Cloud Storage access
- `roles/datastore.user` - For Firestore database access
- `roles/logging.logWriter` - For Cloud Logging

## API Endpoints

### Core Endpoints
- `GET /` - Health check endpoint
- `GET /health` - Detailed health check with service status
- `POST /generate` - Generate content via Agents API
- `POST /review` - Review requirements via Agents API

### File Management
- `POST /upload` - Upload and extract content from files
- `GET /projects` - List all projects
- `GET /projects/{project_id}` - Get specific project details
- `DELETE /projects/{project_id}` - Delete project

### Content Management
- `GET /projects/{project_id}/content` - Get project content
- `POST /projects/{project_id}/content` - Store project content
- `PUT /projects/{project_id}/content` - Update project content

## Testing the Deployment

After deployment, test the service:

```bash
# Get service details
gcloud run services describe medassure-backend --region=europe-west1 --project=gen-lang-client-0182599221

# Test health endpoint
curl https://medassure-backend-europe-west1-gen-lang-client-0182599221.a.run.app/

# Test detailed health check
curl https://medassure-backend-europe-west1-gen-lang-client-0182599221.a.run.app/health

# Test generate endpoint
curl -X POST "https://medassure-backend-europe-west1-gen-lang-client-0182599221.a.run.app/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test query", "metadata": {}}'
```

## Architecture

The Backend service:
1. **API Gateway**: FastAPI-based REST API
2. **Agents Integration**: Forwards requests to Agents service
3. **File Processing**: Handles PDF/DOCX uploads and text extraction
4. **Storage Management**: Manages content in Google Cloud Storage
5. **Database Integration**: Firestore for project and metadata storage
6. **CORS Configuration**: Supports both development and production frontends

## Security Features

- **Service Account Authentication**: Uses dedicated service account
- **CORS Configuration**: Configurable for different environments
- **File Upload Validation**: Size and type restrictions
- **Environment-based Configuration**: Separate dev/prod settings

## Troubleshooting

### Common Issues

1. **Build Failure**
   ```bash
   # Check Dockerfile and requirements.txt
   docker build -t test-backend .
   ```

2. **Runtime Errors**
   ```bash
   # Check Cloud Run logs
   gcloud run services logs read medassure-backend --region=europe-west1
   ```

3. **Agents Connection Issues**
   - Verify Agents service is deployed and accessible
   - Check AGENTS_API_URL environment variable

4. **Storage Permission Issues**
   - Verify service account has storage.admin role
   - Check GOOGLE_CLOUD_BUCKET exists and is accessible

5. **Firestore Issues**
   - Verify service account has datastore.user role
   - Check Firestore database exists

### Debug Mode

For debugging, you can temporarily enable debug mode:

```bash
gcloud run services update medassure-backend \
    --set-env-vars="DEBUG=true" \
    --region=europe-west1
```

## Production Considerations

1. **CORS Configuration**: Update cors_origins in app.py with actual frontend domain
2. **Security**: Consider removing `allow_origins=["*"]` and specify exact domains
3. **Monitoring**: Set up Cloud Monitoring alerts
4. **Backup**: Configure automated Firestore backups
5. **Scaling**: Adjust min/max instances based on usage patterns

## Integration

After deployment, update your Frontend configuration to use:
```
BACKEND_URL=https://medassure-backend-europe-west1-gen-lang-client-0182599221.a.run.app
```
