# Agents Cloud Run Deployment Script (PowerShell)

# Configuration
$GOOGLE_CLOUD_PROJECT = "gen-lang-client-0182599221"
$REGION = "europe-west1"
$SERVICE_NAME = "agents-server"
$SERVICE_ACCOUNT = "master-agent-sa@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com"

# Ensure you're authenticated and project is set
Write-Host "Setting up Google Cloud configuration..." -ForegroundColor Green
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Enable required APIs
Write-Host "Enabling required Google Cloud APIs..." -ForegroundColor Green
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Grant necessary permissions to the service account
Write-Host "Granting permissions to existing service account..." -ForegroundColor Green
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/logging.logWriter"

# Deploy to Cloud Run using source deployment
Write-Host "Deploying Agents Server to Cloud Run..." -ForegroundColor Green
gcloud run deploy $SERVICE_NAME `
    --service-account=$SERVICE_ACCOUNT `
    --allow-unauthenticated `
    --region=$REGION `
    --source=. `
    --labels=dev-medassai=agents-service `
    --memory=1Gi `
    --cpu=1 `
    --max-instances=10 `
    --min-instances=1 `
    --timeout=600 `
    --concurrency=80 `
    --set-env-vars="GOOGLE_CLOUD_PROJECT=gen-lang-client-0182599221,GOOGLE_CLOUD_LOCATION=global,GOOGLE_GENAI_USE_VERTEXAI=True,FIRESTORE_MCP_URL=https://firestore-mcp-server-145534422719.europe-west1.run.app/mcp,JIRA_MCP_URL=https://jira-mcp-server-145534422719.europe-west1.run.app/mcp" `
    --project=$GOOGLE_CLOUD_PROJECT


