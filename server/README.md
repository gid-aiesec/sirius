# Sirus Backend Server

## Setup Instructions (Local Development)

1. **Install dependencies:**
   (It is recommended to use a virtual environment like `venv` or `conda`)
   ```bash
   pip install -r requirements.txt

2. **Environment Variables:**
Copy .env.example to .env. Contact the PM for the active Pinecone API Key.

3. **Run the FastAPI Server:**
uvicorn app.main:app --reload
The server will run on http://localhost:8000.