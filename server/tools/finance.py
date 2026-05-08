from typing import Any

import httpx
from fastmcp import FastMCP

from server.config import settings


async def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    async with httpx.AsyncClient(
        base_url=settings.finance_sync_base_url, timeout=30.0
    ) as client:
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()


async def _post(path: str, json_body: dict[str, Any] | None = None) -> Any:
    async with httpx.AsyncClient(
        base_url=settings.finance_sync_base_url, timeout=30.0
    ) as client:
        response = await client.post(path, json=json_body or {})
        response.raise_for_status()
        return response.json()


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def finance_get_portfolio() -> dict:
        """Devuelve el snapshot actual de la cartera de inversión: posiciones, valores y exposición.

        Úsalo cuando el usuario pregunte por el estado de su cartera, qué tiene en cartera,
        valor total, posiciones abiertas o exposición por activo/sector.

        Devuelve un dict con la cartera completa.
        """
        return await _get("/api/finance/portfolio")

    @mcp.tool
    async def finance_list_active_alerts(days: int = 30) -> dict:
        """Devuelve las alertas activas de la cartera generadas en los últimos N días.

        Úsalo cuando el usuario pregunte por alertas, avisos, señales recientes o eventos
        que requieran atención sobre sus posiciones.

        Args:
            days: Ventana hacia atrás en días. Por defecto 30.

        Devuelve un dict con las alertas activas.
        """
        return await _get("/api/finance/alerts/active", params={"days": days})

    @mcp.tool
    async def finance_upcoming_catalysts(days: int = 14) -> dict:
        """Devuelve los catalizadores próximos (earnings, eventos relevantes) para las posiciones en cartera.

        Úsalo cuando el usuario pregunte por earnings próximos, fechas clave, eventos que
        puedan mover sus posiciones, o calendario de catalizadores.

        Args:
            days: Ventana hacia delante en días. Por defecto 14.

        Devuelve un dict con los catalizadores próximos.
        """
        return await _get("/api/finance/catalysts/upcoming", params={"days": days})

    @mcp.tool
    async def finance_top_overhype(n: int = 3) -> dict:
        """Devuelve el top N de posiciones con mayor índice de overhype (sobreexpectativa de mercado).

        Úsalo cuando el usuario pregunte por posiciones sobrecalentadas, sobrevaloración por
        narrativa, riesgo de corrección, o quiera identificar qué activos están más infladas
        por hype.

        Args:
            n: Número de posiciones a devolver. Por defecto 3.

        Devuelve un dict con el ranking de overhype.
        """
        return await _get("/api/finance/overhype/top", params={"n": n})

    @mcp.tool
    async def finance_evaluate_rules() -> dict:
        """Evalúa las reglas de inversión configuradas contra el estado actual de la cartera y devuelve el resultado.

        Úsalo cuando el usuario pida revisar el cumplimiento de sus reglas, validar la cartera
        contra su sistema, o detectar incumplimientos de criterios definidos.

        Devuelve un dict con el resultado de la evaluación de reglas.
        """
        return await _post("/api/finance/rules/evaluate")

    @mcp.tool
    async def finance_generate_digest() -> dict:
        """Genera el digest financiero del momento (resumen de cartera, alertas, catalizadores y señales).

        Úsalo cuando el usuario pida un resumen general de la cartera, un brief diario/semanal,
        o un panorama consolidado de la situación financiera.

        Devuelve un dict con el digest generado.
        """
        return await _post("/api/finance/digest/generate")

    @mcp.tool
    async def finance_moat_coverage() -> dict:
        """Devuelve la cobertura del análisis de moat (ventaja competitiva) sobre las posiciones de la cartera.

        Úsalo cuando el usuario pregunte cuántas posiciones tienen análisis de moat hecho,
        cobertura del análisis competitivo, o qué tickers faltan por evaluar.

        Devuelve un dict con la cobertura de moat.
        """
        return await _get("/api/finance/moat/coverage")

    @mcp.tool
    async def finance_moat_scorecard(ticker: str) -> dict:
        """Devuelve el scorecard de moat (ventaja competitiva) para un ticker concreto.

        Úsalo cuando el usuario pregunte por la ventaja competitiva, foso económico, calidad
        del negocio o moat de una empresa específica de su cartera.

        Args:
            ticker: Símbolo bursátil. Se normaliza a mayúsculas antes de consultar.

        Devuelve un dict con el scorecard de moat del ticker.
        """
        return await _get(f"/api/finance/moat/scorecard/{ticker.upper()}")
