# personal-ai/CLAUDE.md — específico del repo

## Naturaleza
MCP server custom (FastAPI). Expone tools al chat de claude.ai vía OAuth-style
bearer token en URL path. Desplegado como servicio `personal-ai` dentro del
proyecto Railway `health-dashboard` (que aloja también `finance-sync` y los
servicios de health-dashboard). URL: personal-ai-production-0d2d.up.railway.app/mcp/<token>.

## Tools expuestas
- coach.* (8 tools): wrappers sobre Railway API de health-dashboard.
  Ver app/tools/coach.py.
- finance.* (8 tools): wrappers sobre finance-dashboard. Ver app/tools/finance.py.

## Stack
Python 3.12+, FastAPI, uv, ruff, pytest. Sin Docker en repo (Railway construye).

## Branch convention
- claude/<topic>-<id> — sesiones cc-CLI o cc-web.
- feat/<topic>, fix/<topic>, chore/<topic> — manuales.
- main protegido vía workflow.

## Smoke específico
- POST /mcp/<bearer> con tools/list → debe devolver lista no vacía con coach.* y finance.*.
- Health: GET / → 200.

## CI
Sin GitHub Actions configurada (a fecha 2026-05-10). Cuando se añada, requerirla
en branch protection antes de habilitar auto-merge.

## Reglas particulares
- NO añadir tools nuevas sin entry en docstring que cumpla schema MCP.
- Cambios de bearer token: regenerar también en claude.ai connector
  manualmente (no automatizable).
