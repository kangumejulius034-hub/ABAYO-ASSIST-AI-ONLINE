# ABAYO Assist AI

ABAYO is an internal Streamlit operations assistant for packaging machines. It
organizes fault knowledge, recipes, maintenance history, troubleshooting,
machine components, HMI profiles, and recoverable deletion.

## Architecture

```text
app.py                    Launch dashboard and workflow coordination
core/                     Access, authorization, database, settings, machines
ui/                       Shared responsive theme, sidebar, and components
storage/                  Atomic JSON plus Supabase document persistence
pages/                    Streamlit feature pages
knowledge/                Versioned seed and local-development data
supabase/migrations/      Idempotent launch database changes
tests/                    Unit and regression tests
```

The existing Supabase tables and the recycle-bin behavior are preserved.
Machine records are identified by their database ID, so duplicate display names
cannot overwrite one another.

## Local setup

1. Create a Python 3.11 virtual environment.
2. Install dependencies:

   ```bash
   python -m pip install -r requirements-dev.txt
   ```

3. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml` and
   replace every placeholder.
4. Run the SQL in `supabase/migrations/001_launch_persistence.sql` after taking
   a Supabase backup.
5. Start ABAYO:

   ```bash
   streamlit run app.py
   ```

## Required secrets

- `supabase.url`: Supabase project URL.
- `supabase.key`: a server-only Supabase key with access to the launch tables
  (normally the service-role key). Keep it only in Streamlit Secrets. The new
  tables use row-level security and do not create anonymous browser policies.
- `ABAYO_ACCESS_PASSWORD`: protects every Streamlit page before public exposure.
- `ABAYO_ADMIN_PIN`: provides a separate, short-lived unlock for destructive
  actions.
- `ANTHROPIC_API_KEY` (optional): enables grounded Claude answers on the AI
  Assistant page. Create the key in the Anthropic Console and store it only in
  Streamlit Secrets. Without it, ABAYO keeps using the local answer generator.
- `ANTHROPIC_MODEL` (optional): overrides the default `claude-sonnet-5` model.

Never commit `.streamlit/secrets.toml` or place a Supabase service-role key in
browser code. Retrieved ABAYO evidence is sent to Anthropic only when the
operator enables Claude on the AI Assistant page.

## Data durability

Tracked JSON files are seed data and a local-development fallback. At launch,
the complete documents are mirrored to `knowledge_documents`, because files
written on hosted Streamlit instances are not durable across redeployments.
Uploaded maintenance and recipe images still use local compatibility paths; use
Supabase Storage before relying on those images as permanent evidence.

## Verification

```bash
ruff check .
pytest
python -m compileall -q .
```

GitHub Actions runs the same checks for every pull request and every push to
`main`.

## Launch checklist

- Apply the migration and confirm the dashboard reports durable storage ready.
- Configure both access secrets.
- Verify machine creation, soft deletion, restoration, and permanent deletion.
- Import and compare two HMI profiles for the same machine.
- Confirm a new recipe or fault remains after restarting the app.
- Keep the app internal until permanent image storage and named user accounts
  are added.
