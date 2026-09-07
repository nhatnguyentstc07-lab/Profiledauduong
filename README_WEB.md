# Learnbuddy AI — Web version

This version replaces the Streamlit interface with a normal web application:

- Frontend: HTML + CSS + JavaScript
- Backend: FastAPI
- AI/RAG/business logic: reused from `core/`
- Database: SQLite
- Authentication: HttpOnly session cookie
- Default AI backend: native OpenAI (CrewAI is not required)

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set `OPENAI_API_KEY`.

Then:

```bash
uvicorn web_app:app --reload
```

Open `http://127.0.0.1:8000`.

## Deploy on Render

Create a new **Web Service** from this GitHub repository.

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn web_app:app --host 0.0.0.0 --port $PORT`
- Add secret environment variable: `OPENAI_API_KEY`

`render.yaml` already contains these settings.

## Notes

The web version deliberately does not parse every PDF at server startup. Lightweight question banks and the existing corpus are synchronized at boot; PDF textbook ingestion can be run later if needed. This avoids long deployment startup times on small hosts.

Do not commit `.env` or API keys.
