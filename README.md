# personal-ai

MCP server that exposes personal training, health and nutrition data to Claude via a custom remote connector. Thin wrapper around a Railway-hosted aggregator API that unifies TrainingPeaks, Garmin and MyFitnessPal in Postgres.

## Tools

All tools are namespaced `coach_*`:

- `coach_get_training_state(days_back=7)` — master endpoint: training load + workouts + recovery + nutrition for the last N days.
- `coach_get_training_load(from_date, to_date)` — CTL, ATL, TSB per day.
- `coach_get_workouts(from_date, to_date)` — workout list.
- `coach_get_workout_detail(workout_id)` — full detail for one workout.
- `coach_get_metrics(from_date, to_date)` — daily HRV, sleep, body battery, nutrition.
- `coach_get_athlete()` — athlete profile (zones, FTP, thresholds).

## Local dev

```bash
python -m venv .venv
source .venv/Scripts/activate     # Git Bash on Windows
pip install -e .

# Generate a secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Create .env
cp .env.example .env
# edit .env: set MCP_SECRET to the generated value

python -m server.main
```

Server listens on `http://localhost:8000`. MCP endpoint is `/mcp` (no trailing slash). Health check at `/health`.

## Deploy to Railway

1. Push this repo to GitHub.
2. In Railway, create a new project → "Deploy from GitHub repo" → select this repo. Railway picks up `railway.json` and uses the Dockerfile.
3. Add environment variables in the Railway service:
   - `MCP_SECRET` — the generated token (same as local).
   - `RAILWAY_API_BASE` — defaults to the production aggregator URL; override only if pointing elsewhere.
4. Railway assigns a public URL once the deploy is healthy (it polls `/health`).

## Connect to Claude.ai

1. In Claude (web or mobile): Settings → Connectors → Add custom connector.
2. URL: `https://<your-railway-app>/mcp` (no trailing slash — FastMCP redirects `/mcp/` → `/mcp` and the redirect drops the bearer token).
3. Authentication: Bearer token. Paste the value of `MCP_SECRET`.
4. Save. The 6 `coach_*` tools should appear in the connector's tool list.
