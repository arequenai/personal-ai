from datetime import date, timedelta
from typing import Any

import httpx
from fastmcp import FastMCP

from server.config import settings


async def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    async with httpx.AsyncClient(
        base_url=settings.railway_api_base, timeout=30.0
    ) as client:
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def coach_get_training_state(days_back: int = 7) -> Any:
        """Devuelve el estado de entrenamiento, recuperación y nutrición de los últimos N días.

        Úsalo PRIMERO al responder cualquier pregunta sobre entrenamiento, fatiga,
        recuperación, sueño, HRV, body battery o nutrición. Es el endpoint maestro:
        agrega CTL/ATL/TSB, workouts, métricas de recuperación y nutrición en una
        sola llamada.

        Args:
            days_back: Número de días hacia atrás desde hoy. Por defecto 7.

        Devuelve un dict con keys: training_load, workouts, recovery, nutrition.
        """
        to_d = date.today()
        from_d = to_d - timedelta(days=days_back)
        return await _get(
            "/api/tp/summary",
            params={"from_date": from_d.isoformat(), "to_date": to_d.isoformat()},
        )

    @mcp.tool
    async def coach_get_training_load(from_date: str, to_date: str) -> Any:
        """Devuelve la carga de entrenamiento (CTL, ATL, TSB) por día en un rango.

        Úsalo cuando el usuario pregunte específicamente por carga crónica/aguda,
        forma (TSB), fitness, fatiga, o quiera ver la evolución diaria del entrenamiento
        en un periodo concreto. Para preguntas generales sobre estado de entrenamiento
        usa coach_get_training_state, que ya incluye estos datos.

        Args:
            from_date: Fecha inicial inclusive en formato YYYY-MM-DD.
            to_date: Fecha final inclusive en formato YYYY-MM-DD.

        Devuelve una lista de entradas diarias con CTL, ATL y TSB.
        """
        return await _get(
            "/api/tp/training-load",
            params={"from_date": from_date, "to_date": to_date},
        )

    @mcp.tool
    async def coach_get_workouts(from_date: str, to_date: str) -> Any:
        """Devuelve la lista de workouts en un rango de fechas.

        Úsalo cuando el usuario pregunte qué entrenamientos ha hecho, cuántos workouts
        en un periodo, distribución por deporte, o cuando necesites listar sesiones
        para luego pedir detalle de alguna con coach_get_workout_detail.

        Args:
            from_date: Fecha inicial inclusive en formato YYYY-MM-DD.
            to_date: Fecha final inclusive en formato YYYY-MM-DD.

        Devuelve una lista de workouts con id, fecha, deporte, duración y métricas resumen.
        """
        return await _get(
            "/api/tp/workouts",
            params={"from_date": from_date, "to_date": to_date},
        )

    @mcp.tool
    async def coach_get_workout_detail(workout_id: str) -> Any:
        """Devuelve el detalle completo de un workout específico por su ID.

        Úsalo cuando el usuario pregunte por un entrenamiento concreto: análisis de
        un partido, una tirada larga, una sesión específica. Necesitas el workout_id
        previamente obtenido con coach_get_workouts o coach_get_training_state.

        Args:
            workout_id: ID del workout (lo devuelven coach_get_workouts y coach_get_training_state).

        Devuelve un dict con métricas completas: pulsaciones, ritmo, potencia, splits,
        zonas, TSS, etc., según el deporte.
        """
        return await _get(f"/api/tp/workout/{workout_id}")

    @mcp.tool
    async def coach_get_metrics(from_date: str, to_date: str) -> Any:
        """Devuelve las métricas diarias de salud y recuperación en un rango.

        Úsalo cuando el usuario pregunte específicamente por HRV, sueño, body battery,
        peso, composición corporal o nutrición día a día sin necesidad de los datos
        de carga de entrenamiento. Para una visión integral usa coach_get_training_state.

        Args:
            from_date: Fecha inicial inclusive en formato YYYY-MM-DD.
            to_date: Fecha final inclusive en formato YYYY-MM-DD.

        Devuelve una lista de entradas diarias con métricas de Garmin y MyFitnessPal.
        """
        return await _get(
            "/api/tp/metrics",
            params={"from_date": from_date, "to_date": to_date},
        )

    @mcp.tool
    async def coach_get_athlete() -> Any:
        """Devuelve el perfil del atleta: zonas, FTP, umbrales, datos personales.

        Úsalo cuando el usuario pregunte por sus zonas de entrenamiento, FTP, ritmos
        umbral, FC máxima, o necesites contexto de referencia para interpretar
        métricas de un workout (p. ej. "¿en qué zona corrí esta tirada?").

        Devuelve un dict con el perfil completo del atleta.
        """
        return await _get("/api/tp/athlete")
