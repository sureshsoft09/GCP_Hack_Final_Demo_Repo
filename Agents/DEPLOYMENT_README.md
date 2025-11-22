# Agents Cloud Run Deployment Guide

This guide covers deploying the MedAssure AI Agents service to Google Cloud Run.

## Prerequisites

1. **Google Cloud CLI**: Ensure `gcloud` is installed and authenticated
2. **Docker**: Required for containerization (if using Docker deployment)
3. **Google Cloud Project**: Project ID `gen-lang-client-0182599221`
4. **Service Account**: `firestoreconnectserviceacc@gen-lang-client-0182599221.iam.gserviceaccount.com`

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
gcloud run deploy agents-server \
    --service-account=firestoreconnectserviceacc@gen-lang-client-0182599221.iam.gserviceaccount.com \
    --no-allow-unauthenticated \
    --region=europe-west1 \
    --source=. \
    --labels=environment=dev,service=agents-server \
    --memory=1Gi \
    --cpu=1 \
    --max-instances=10 \
    --min-instances=0 \
    --timeout=600 \
    --concurrency=80 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=gen-lang-client-0182599221,GOOGLE_CLOUD_LOCATION=global,GOOGLE_GENAI_USE_VERTEXAI=True,FIRESTORE_MCP_URL=https://firestore-mcp-server-145534422719.europe-west1.run.app/mcp,JIRA_MCP_URL=https://jira-mcp-server-145534422719.europe-west1.run.app/mcp" \
    --project=gen-lang-client-0182599221
```

## Environment Variables

The following environment variables are configured automatically:

- `GOOGLE_CLOUD_PROJECT`: gen-lang-client-0182599221
- `GOOGLE_CLOUD_LOCATION`: global
- `GOOGLE_GENAI_USE_VERTEXAI`: True
- `FIRESTORE_MCP_URL`: https://firestore-mcp-server-518624836175.europe-west1.run.app/mcp
- `JIRA_MCP_URL`: https://jira-mcp-server-518624836175.europe-west1.run.app/mcp
- `PORT`: Set automatically by Cloud Run

## Service Configuration

- **Service Name**: agents-server
- **Region**: europe-west1
- **Memory**: 1Gi
- **CPU**: 1
- **Port**: 8082 (configurable via PORT env var)
- **Timeout**: 600 seconds
- **Concurrency**: 80

## Dependencies

Key dependencies included in `requirements.txt`:
- google-adk==1.14.0
- fastapi>=0.115.0
- uvicorn>=0.34.0
- google-auth>=2.32.0
- google-cloud-logging>=3.12.0

## IAM Permissions

The service account requires:
- `roles/aiplatform.user` - For Vertex AI access
- `roles/logging.logWriter` - For Cloud Logging

## Testing the Deployment

After deployment, test the service:

```bash
# Get service details
gcloud run services describe agents-server --region=europe-west1 --project=gen-lang-client-0182599221

# Test the API endpoint
curl -X POST "https://agents-server-europe-west1-gen-lang-client-0182599221.a.run.app/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, test query"}'
```

## API Endpoints

- `POST /query` - Main agent interaction endpoint
- `GET /docs` - FastAPI documentation
- `GET /health` - Health check endpoint (if implemented)

## Troubleshooting

1. **Build Failure**: Check Dockerfile and requirements.txt
2. **Runtime Error**: Check Cloud Run logs: `gcloud run services logs read agents-server --region=europe-west1`
3. **Permission Issues**: Verify service account IAM roles
4. **MCP Connection Issues**: Verify MCP server URLs are accessible

## Architecture

The Agents service:
1. Uses Google ADK for agent functionality
2. Connects to Firestore MCP and JIRA MCP servers
3. Provides FastAPI endpoints for frontend integration
4. Runs on Cloud Run with automatic scaling

## Security

- Service runs with non-root user
- No public access (--no-allow-unauthenticated)
- Uses IAM for authentication
- Environment variables for configuration
