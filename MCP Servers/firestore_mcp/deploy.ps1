# Firestore MCP Server Cloud Run Deployment Script (PowerShell)

# Configuration
$GOOGLE_CLOUD_PROJECT = "gen-lang-client-0182599221"  # Using the actual GCP project ID
$REGION = "europe-west1"                       # Using europe-west1 as specified
$SERVICE_NAME = "firestore-mcp-server"
$SERVICE_ACCOUNT = "firestoreconnectserviceacc@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com"

# Ensure you're authenticated and project is set
Write-Host "Setting up Google Cloud configuration..." -ForegroundColor Green
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Enable required APIs
Write-Host "Enabling required Google Cloud APIs..." -ForegroundColor Green
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Grant necessary permissions to the service account (assuming it already exists)
Write-Host "Granting permissions to existing service account..." -ForegroundColor Green
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/logging.logWriter"

# Deploy to Cloud Run using source deployment
Write-Host "Deploying Firestore MCP Server to Cloud Run..." -ForegroundColor Green
gcloud run deploy $SERVICE_NAME `
    --service-account=$SERVICE_ACCOUNT `
    --allow-unauthenticated `
    --region=$REGION `
    --source=. `
    --labels=dev-medassai=firestore-mcp `
    --set-env-vars=GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,FIRESTORE_DATABASE_Name=medassureaifirestoredb,ENVIRONMENT=production,DEBUG=false `
    --memory=512Mi `
    --cpu=1 `
    --max-instances=10 `
    --min-instances=1 `
    --timeout=300 `
    --concurrency=80 `
    --project=$GOOGLE_CLOUD_PROJECT

