<p align="center">
  <img src="../frontend/public/favicon.png" alt="Sirius Logo" width="100"/>
</p>

## Sirius Backend Server

Python (FastAPI)
- EXPA OAuth flow
- Chat creation and messaging logic
- Chat history (via Supabase)
- RAG Pipeline & Chatbot logic (via Pinecone & Google Gemini)

<br />

**Setup Instructions (Local Development)**

1. **Install dependencies:**
   
   We use `pip-tools` to manage dependencies safely.
   ```bash
   pip install pip-tools
   pip-compile requirements.in
   pip install -r requirements.txt
   ```

2. **Environment Variables:**
   
   Copy `.env.example` to `.env` and set the required variables.

3. **Run the FastAPI Server:**
   
   ```bash
   python -m app.main
   ```
   The server will run on `http://localhost:8000`