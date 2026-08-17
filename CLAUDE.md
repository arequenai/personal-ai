# personal-ai/CLAUDE.md — específico del repo

## Naturaleza
Servidor MCP custom (FastMCP 2.0, transport `streamable-http`). Expone tools al chat de
claude.ai; el secreto viaja en el **path de la URL** (`/mcp/<MCP_SECRET>`), no en cabecera,
porque el conector custom de claude.ai solo admite OAuth. Desplegado como servicio
`personal-ai` dentro del proyecto Railway `health-dashboard` (que aloja también
`finance-sync`, `garmin-sync` y `garmin-front-end`).

**Es un forwarder HTTP puro: no tiene lógica de dominio, ni estado, ni persistencia.** Todo
lo que sirve lo calculan los dos backends. Su valor está en los **docstrings**, que son el
prompt de enrutado con el que Claude decide qué tool usar — por eso se escriben largos y en
español, y por eso cambiarlos cambia el comportamiento del sistema.

## Tools expuestas (21)
- `coach_*` (13) → aggregator `garmin-sync` (`RAILWAY_API_BASE`). Ver `server/tools/coach.py`.
- `finance_*` (8) → `finance-sync` (`FINANCE_SYNC_BASE_URL`). Ver `server/tools/finance.py`.

Nombres con **guion bajo** (`coach_get_metrics`), no con punto.

## Configuración (`server/config.py`)
| Variable | Obligatoria | Qué |
|---|---|---|
| `MCP_SECRET` | **sí** (sin default; el import falla sin ella) | credencial en el path |
| `RAILWAY_API_BASE` | no (default de producción) | aggregator de salud |
| `RAILWAY_API_KEY` | en producción **sí** | `X-API-Key` que exige garmin-sync |
| `FINANCE_SYNC_BASE_URL` | **sí en producción** | sin ella el default es `localhost:8000`, que es **este mismo servidor**: las 8 tools finance se llamarían a sí mismas. `/health` expone `finance_sync_configured` y el arranque loguea un warning |
| `PORT` | no (8000) | |

## Stack
Python 3.11+, FastMCP, httpx, pydantic-settings. Build con setuptools (`pip install -e .`).
**Sí hay Docker en el repo** (`Dockerfile` + `railway.json` con builder DOCKERFILE).
Tests con pytest + respx; lint con ruff (`ruff check`; el árbol aún no está formateado con
`ruff format`).

## Branch convention
- `claude/<topic>-<id>` — sesiones cc-CLI o cc-web.
- `feat/<topic>`, `fix/<topic>`, `chore/<topic>` — manuales.

## Smoke específico
- POST `/mcp/<MCP_SECRET>` con `tools/list` → lista no vacía con `coach_*` y `finance_*`.
- `GET /health` → 200 con `{"status": "ok", "finance_sync_configured": true}`. **Si
  `finance_sync_configured` es `false`, las tools de finanzas están rotas** aunque el
  servicio esté verde.

## CI
`.github/workflows/ci.yml`: ruff + pytest en cada PR y push a main.

## Reglas particulares
- NO añadir tools nuevas sin docstring que cumpla el schema MCP.
- **El docstring es contrato**: si el backend deja de servir un campo, hay que quitarlo del
  docstring en la misma PR. Pasó con `calories_target_adaptive`, retirado del canon en
  agosto de 2026 mientras el docstring lo siguió anunciando.
- Cambios de `MCP_SECRET`: regenerar también el conector en claude.ai a mano (no automatizable).
- **Repo público**: nunca datos personales, ni credenciales, ni rutas internas nuevas.
