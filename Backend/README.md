MedAssure AI - Backend
======================

This backend forwards requests from the frontend to the Agents API (FastAPI) running in `Agents/main.py`.

## Local Development

1. Activate the project's virtual environment (from project root):

```powershell
cd "d:\Google Projects\Final Sample\MedAssure AI"
.venv\Scripts\Activate.ps1
```

2. Install backend dependencies:

```powershell
cd Backend
pip install -r requirements.txt
```

3. Create `.env` file from template:

```powershell
cp .env.template .env
# Edit .env with your local Agents API URL
```

4. Ensure the Agents API is running (default: http://localhost:8082).

5. Start the backend server:

```powershell
python app.py
# Or with uvicorn:
uvicorn app:app --reload --port 8083
```

## Cloud Run Deployment

1. Update `deploy.sh` with your project details:
   - Set `PROJECT_ID` to your Google Cloud project
   - Update `AGENTS_API_URL` to your deployed Agents service URL

2. Make deploy script executable and run:

```bash
chmod +x deploy.sh
./deploy.sh your-project-id us-central1
```

3. Or deploy manually:

```bash
gcloud run deploy medassure-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "AGENTS_API_URL=https://your-agents-url.run.app/query"
```

## Environment Variables

- `AGENTS_API_URL`: URL of the Agents API (required)
- `AGENTS_API_TIMEOUT`: Timeout for API calls (default: 30s)
- `PORT`: Server port (default: 8083, Cloud Run overrides this)

## Endpoints

- POST /generate_test_cases
  - Body: { "prompt": "..." }
  - Forwards a generated prompt to the Agents API and returns the agent response.

- POST /enhance_test_cases
- POST /migration_test_cases
- POST /clarification_chat
- GET /health
- GET / (health check for Cloud Run)

All POST endpoints return JSON: { "response": "...", "debug_info": "..." }

## Notes

- The backend uses `httpx` async client to call the Agents API.
- Cloud Run friendly: uses PORT environment variable and includes health check endpoint.
- Dockerfile included for containerized deployment.

