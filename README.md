# University AI Chatbot

An AI chatbot that answers student questions about **courses, fees, schedules and university services**, 24/7, in **Khmer and English**, on the **university website** and **Telegram**.

It uses **RAG (Retrieval-Augmented Generation)**: the bot first searches the university's approved knowledge base, then the AI model writes the answer *only* from what it found. If nothing relevant is found, the question is handed to staff instead of guessing.

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Backend + admin panel | Django 5 + Django REST Framework |
| Database + vector search | PostgreSQL 16 + pgvector |
| Embeddings (Khmer + English) | `intfloat/multilingual-e5-small` via sentence-transformers |
| AI model | Claude API (Anthropic) – swappable in `chat/services/llm.py` |
| Website widget | Plain JavaScript (`static/chat/widget.js`) |
| Telegram | python-telegram-bot |
| Security | HTTPS settings, django-axes (login lockout), role groups, API rate limits |
| Dev environment | Docker + Docker Compose |

## Project structure

```
uni-ai-chatbot/
├── config/                 Django settings and URLs
├── knowledge/              Knowledge base (FAQs, documents, search index)
│   ├── models.py           Category, FAQ, Document, Chunk (vector)
│   ├── admin.py            Staff admin screens (US-10, US-11)
│   ├── signals.py          Auto re-index when staff save an FAQ or upload a file
│   ├── services/
│   │   ├── embeddings.py   Text → vector (e5 model or hash backend)
│   │   ├── chunking.py     Split long documents into pieces
│   │   ├── extraction.py   Read PDF / Word / text files
│   │   └── indexing.py     Keep the search index up to date
│   └── management/commands/
│       ├── setup_roles.py       Create Admin and Editor staff groups (US-12)
│       └── load_sample_data.py  Sample FAQs for testing
├── chat/                   Chatbot
│   ├── models.py           ChatLog, Escalation (hand-off to staff)
│   ├── views.py            REST API: /api/chat/ and /api/chat/<id>/feedback/
│   ├── services/
│   │   ├── rag.py          The answer pipeline
│   │   ├── llm.py          AI model call + system prompt
│   │   ├── language.py     Khmer / English detection (US-05)
│   │   └── messages.py     Fixed bot messages in both languages
│   └── management/commands/run_telegram_bot.py   (US-06)
├── static/chat/widget.js   Website chat widget (US-07)
├── templates/index.html    Demo page
├── tests/                  Fast unit tests (pytest)
├── Dockerfile, docker-compose.yml, requirements.txt, .env.example
```

---

## 1. Set up (every team member, once)

**Install:** [Git](https://git-scm.com/), [Docker Desktop](https://www.docker.com/products/docker-desktop/) and [VS Code](https://code.visualstudio.com/).

```bash
# 1. Get the code (the team lead first pushes this folder to GitHub)
git clone https://github.com/<your-team>/uni-ai-chatbot.git
cd uni-ai-chatbot

# 2. Create your settings file
cp .env.example .env          # Windows PowerShell: copy .env.example .env

# 3. Build and start PostgreSQL + Django (first build takes 5–10 minutes)
docker compose up --build
```

In a **second terminal**:

```bash
docker compose exec web python manage.py createsuperuser   # your admin login
docker compose exec web python manage.py setup_roles       # Admin + Editor groups
docker compose exec web python manage.py load_sample_data  # sample FAQs
```

> The first `load_sample_data` downloads the e5 embedding model (~500 MB). On a weak laptop or slow internet, set `EMBEDDING_BACKEND=hash` in `.env` for now (less accurate, no download). If you switch backends later, re-index: in the admin select all FAQs → **Re-index selected FAQs**.

**Open:**
- Demo page with the chat widget: http://localhost:8000
- Admin panel: http://localhost:8000/admin

## 2. Turn on the AI model

Without an API key the bot replies with the best-matching FAQ answer directly. That is enough for Sprints 4–5.

To get real AI answers (rephrased, combined from several sources, in the student's language):
1. Create an API key at https://console.anthropic.com
2. Put it in `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
3. Restart: `docker compose restart web`

Keep the key secret. Never commit `.env` to GitHub.

## 3. Run the Telegram bot

1. On Telegram, message **@BotFather** → `/newbot` → copy the token.
2. Put it in `.env`: `TELEGRAM_BOT_TOKEN=...`
3. Start it: `docker compose --profile telegram up`

## 4. Add the widget to the university website

```html
<script src="https://YOUR-SERVER/static/chat/widget.js"
        data-api="https://YOUR-SERVER"
        data-title="University AI Chatbot" defer></script>
```

Add the website address to `CORS_ALLOWED_ORIGINS` in `.env`.

## 5. Staff guide (admin panel)

| Task | Where |
|---|---|
| Add or edit a question and answer | Knowledge base → FAQs |
| Upload a fee table or calendar (PDF / Word) | Knowledge base → Documents |
| Hide an outdated answer | Untick **Is active** on the FAQ |
| Reply to questions the bot couldn't answer | Chat & hand-offs → Escalations |
| See what students ask and their ratings | Chat & hand-offs → Chat logs |
| Give a staff member access | Users → tick **Staff status** → add to **Editor** or **Admin** group |

Changes are searchable by the bot immediately after saving.

## 6. Run the tests

```bash
pytest                                              # fast unit tests, no database
docker compose exec web python manage.py test      # API + database tests
```

## 7. API

`POST /api/chat/`
```json
{ "message": "Where can I pay my tuition fees?", "session_id": "web-abc123" }
```
Response:
```json
{ "answer": "...", "language": "en", "escalated": false, "log_id": 12,
  "sources": [{ "title": "Where can I pay my tuition fees?", "type": "faq" }] }
```

`POST /api/chat/<log_id>/feedback/` with `{ "rating": 1, "session_id": "web-abc123" }` (1 = 👍, -1 = 👎)

Rate limits: 20 chat messages and 30 ratings per minute per IP.

---

## User stories in this starter

| Story | Status in starter | Sprint |
|---|---|---|
| US-12 Secure staff login with roles | ✅ Done (roles, password rules, lockout after 5 failed logins) | S4 |
| US-10 Staff add/edit FAQs | ✅ Done | S4 |
| US-11 Upload documents | ✅ Done (PDF, Word, text; scanned PDFs not supported) | S4 |
| US-01/02/03 Schedule, fee, course answers | ⚙️ Pipeline done – needs the real university data | S5 |
| US-07 Website chat widget | ✅ Done | S5 |
| US-05 Khmer + English | ⚙️ Detection + Khmer messages done – test Khmer accuracy | S6 |
| US-04/09 Services, admissions | ⚙️ Add the content in the admin | S6 |
| US-06 Telegram bot | ✅ Done | S7 |
| US-08 Hand-off to staff | ⚙️ Escalations created – **to do:** send the staff reply back to the student (Telegram message / email) | S7 |
| US-13 Rate answers | ✅ Done (website + Telegram) | S7 |
| US-14 Reports dashboard | 🔲 To do – chat logs are already saved; build the charts page | S8 |

## Team workflow

- One branch per user story: `git checkout -b feature/US-14-report`
- Commit often, open a Pull Request, one teammate reviews before merging to `main`.
- Never commit `.env`, API keys or student data.
- Tune `RAG_MAX_DISTANCE` during the Sprint 9 accuracy test: lower = stricter (more hand-offs, fewer wrong answers).
