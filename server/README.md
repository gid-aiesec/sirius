<p align="center">
  <img src="../frontend/public/favicon.png" alt="Sirius Logo" width="100"/>
</p>

# Sirus Backend Server

## Setup Instructions (Local Development)

1. **Install dependencies:**
   We use `pip-tools` to manage dependencies safely.
   ```bash
   pip install pip-tools
   pip-compile requirements.in
   pip install -r requirements.txt

2. **Environment Variables:**
Copy .env.example to .env. Contact the PM for the active Pinecone API Key.

3. **Run the FastAPI Server:**
uvicorn app.main:app --reload
The server will run on http://localhost:8000.