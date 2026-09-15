# Markdown Note-Taking Service

## 1. Setup

1. Create and activate a virtual environment.
2. Install dependencies:

pip install -r requirements.txt

3. Create a .env file and add the required environment variables.
4. Make sure PostgreSQL is running, run it via docker compose up -d db (without API for now).

## 2. Database Migrations

Alembic is used for database migrations.

Create a new migration after changing the models:

alembic revision --autogenerate -m "migration description"

Apply migrations:

alembic upgrade head

## 3. Run the Application

### Run Locally

uvicorn main:app --reload

### Run with Docker Compose

docker compose up -d db 

I ran postgres database only via docker

## 4. Example Curl Flow

The `scripts/demo.sh` script tests the main application flow:

run via:

bash scripts/demo.sh

## 5. Design Decisions

### Grammar Check / Queue Approach

I have used LanguageTool synchronously with a 10-second timeout.  
A timeout returns 504, while other LanguageTool failures return 502.
For now, it is easier to use synchronous

### Markdown Library

The markdown package converts Markdown to HTML.  
bh3 sanitizes the generated HTML to prevent unsafe content via bh3.clean().

### Search Approach

Search uses PostgreSQL ILIKE through SQLAlchemy.  
It searches both title and body_markdown, is case-insensitive, and ignores an empty q.

### Authorization / Ownership Decision

Unauthorized access to another user's resource returns 404 not 403 to avoid revealing whether the resource exists.

### JWT Configuration

Tokens expire after 30 minutes.