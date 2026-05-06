from datetime import date, timedelta
from typing import Any, Literal

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


async def _post(path: str, json_body: dict[str, Any]) -> Any:
    async with httpx.AsyncClient(
        base_url=settings.railway_api_base, timeout=30.0
    ) as client:
        response = await client.post(path, json=json_body)
        response.raise_for_status()
        return response.json()


async def _delete(path: str, params: dict[str, Any] | None = None) -> None:
    async with httpx.AsyncClient(
        base_url=settings.railway_api_base, timeout=30.0
    ) as client:
        response = await client.delete(path, params=params)
        response.raise_for_status()


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

    @mcp.tool
    async def coach_get_nutrition(from_date: str, to_date: str) -> Any:
        """Devuelve macros diarios completos (calorías, proteína, carbos, grasa, fibra, sodio), goals, target adaptativo de calorías, y consumo de alcohol entre dos fechas.

        Úsalo cuando el usuario pregunte por adherencia al plan nutricional, déficit/superávit, evolución de proteína, ingesta de alcohol, o cualquier análisis de macros con detalle. Para una visión rápida del estado general (entrenamiento + recovery + nutrición agregada) usa coach_get_training_state.

        Devuelve lista de dicts por día con: date, calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg, calories_goal, protein_goal_g, alcohol_drinks, calories_target_adaptive.
        """
        return await _get(
            "/api/nutrition",
            params={"from_date": from_date, "to_date": to_date},
        )

    @mcp.tool
    async def coach_get_meals(date: str) -> dict:
        """Devuelve el detalle de comidas individuales registradas en MyFitnessPal para un día concreto, agrupadas por tipo de comida (desayuno, comida, cena, snacks, other) con macros por entry cuando MFP los tiene.

        Úsalo cuando el usuario pregunte qué comió en un día concreto, de dónde vino un pico de calorías o de un macro específico, o quiera revisar la composición real de comidas (no solo los totales).

        Para totales agregados de macros en un rango de fechas usa coach_get_nutrition. Para una visión integral del día con entrenamiento + recovery + nutrición agregada usa coach_get_training_state.

        Args:
            date: Fecha en formato YYYY-MM-DD.

        Devuelve un dict con date, meals (agrupado por tipo: breakfast/lunch/dinner/snacks/other, cada uno una lista de entries con name/calories/protein_g/carbs_g/fat_g/position) y totals."""
        return await _get(f"/api/nutrition/{date}/meals")

    @mcp.tool
    async def coach_get_body_composition(from_date: str, to_date: str) -> Any:
        """Devuelve peso y porcentaje de grasa corporal por día entre dos fechas. La fuente combina Fitbit y MFP weight tracking.

        Úsalo SOLO cuando el usuario pregunte específicamente por evolución de peso, % grasa corporal, o composición corporal. Para métricas generales del día (HRV, sueño, body battery, peso puntual) usa coach_get_metrics — esa también incluye peso.

        Devuelve lista de dicts por día con: date, weight_kg, body_fat_pct.
        """
        return await _get(
            "/api/body-composition",
            params={"from_date": from_date, "to_date": to_date},
        )

    @mcp.tool
    async def coach_search_food(query: str, limit: int = 10) -> Any:
        """Busca alimentos en MyFitnessPal por nombre o marca y devuelve candidatos para loggear.

        Úsalo como PRIMER paso cuando el usuario quiera registrar comida ("apunta una manzana", "logueo 100g de arroz"): obtienes los mfp_id que necesitan coach_get_food_details (para ver tamaños de ración) y coach_log_meal (para registrar).

        Args:
            query: Texto de búsqueda (nombre del alimento o marca). Sé específico ("plátano canario" mejor que "fruta").
            limit: Máximo de resultados. Por defecto 10.

        Devuelve una lista de dicts con: mfp_id, name, brand (puede ser null), verified, calories (para la ración por defecto).
        """
        return await _get(
            "/api/nutrition/search",
            params={"q": query, "limit": limit},
        )

    @mcp.tool
    async def coach_get_food_details(mfp_id: int) -> Any:
        """Devuelve macros y tamaños de ración disponibles de un alimento concreto en MyFitnessPal.

        Úsalo TRAS coach_search_food cuando necesites: (a) ver los unit/serving disponibles para que el usuario elija ("¿lo logueo en gramos o por unidad?"), (b) calcular macros antes de loggear, (c) confirmar al usuario qué alimento se va a registrar. La response incluye un campo version requerido internamente para coach_log_meal.

        Args:
            mfp_id: ID numérico del alimento en MFP (lo devuelve coach_search_food).

        Devuelve un dict con: mfp_id, name, brand, version, serving_sizes (lista de {weight_id, unit, value, multiplier, index, description}), calories_per_serving, protein_per_serving_g, carbs_per_serving_g, fat_per_serving_g.
        """
        return await _get(f"/api/nutrition/food/{mfp_id}")

    @mcp.tool
    async def coach_log_meal(
        mfp_id: int,
        meal_type: Literal["breakfast", "lunch", "dinner", "snacks"],
        date: str | None = None,
        quantity: float = 1.0,
        unit: str | None = None,
        force: bool = False,
    ) -> Any:
        """Registra una entrada de comida en el diario de MyFitnessPal y devuelve el entry creado con macros calculados.

        Úsalo como paso FINAL del flujo de logging tras coach_search_food (+ opcionalmente coach_get_food_details para elegir unit). El aggregator es idempotente: si ya existe un entry equivalente devuelve 409 — en ese caso pregunta al usuario si quiere duplicarlo y reintenta con force=True. NO reintentes 409 automáticamente.

        Args:
            mfp_id: ID del alimento (de coach_search_food).
            meal_type: Una de "breakfast", "lunch", "dinner", "snacks". No traduzcas: el aggregator solo acepta estos valores en inglés.
            date: Fecha YYYY-MM-DD. Si se omite usa hoy en zona Europe/Madrid.
            quantity: Cantidad de raciones. Por defecto 1.0.
            unit: Descripción de la ración (ej "100 g", "1 medium"). Debe coincidir con un serving_sizes.description de coach_get_food_details. Si se omite usa la ración default del alimento.
            force: Por defecto False. Pasa True solo si el usuario confirma duplicar tras un 409.

        Devuelve un dict con: entry_id (UUID, guárdalo para borrar con coach_delete_diary_entry), mfp_id, food_name, meal_type, date, quantity, unit, weight_id, calories, protein_g, carbs_g, fat_g.

        Si el aggregator responde 409 (idempotency conflict), en lugar de propagar la excepción se devuelve un dict {"conflict": True, "detail": str, "hint": str}. El cliente debe comprobar `if result.get("conflict"):` para decidir si pedir confirmación al usuario antes de reintentar con force=True. Otros 4xx/5xx siguen propagándose como HTTPStatusError.
        """
        body: dict[str, Any] = {
            "mfp_id": mfp_id,
            "meal_type": meal_type,
            "quantity": quantity,
            "force": force,
        }
        if date is not None:
            body["date"] = date
        if unit is not None:
            body["unit"] = unit
        try:
            return await _post("/api/nutrition/log", body)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                try:
                    detail = e.response.json().get("detail", "Entry already exists")
                except (ValueError, KeyError):
                    detail = "Entry already exists"
                return {
                    "conflict": True,
                    "detail": detail,
                    "hint": "Set force=True to bypass idempotency and create the duplicate anyway.",
                }
            raise

    @mcp.tool
    async def coach_delete_diary_entry(entry_id: str, date: str) -> dict:
        """Borra una entrada del diario de MyFitnessPal por su entry_id.

        Úsalo cuando el usuario pida deshacer un registro recién hecho ("quita esa manzana", "borra lo que acabo de loggear") o limpiar entries detectados con coach_get_meals. Necesitas el entry_id (devuelto por coach_log_meal o derivable de coach_get_meals) y la fecha del entry.

        Args:
            entry_id: UUID del entry en MFP.
            date: Fecha YYYY-MM-DD del entry (la misma con la que se creó).

        Devuelve un dict {success: True, entry_id, date}.
        """
        await _delete(
            f"/api/nutrition/entry/{entry_id}",
            params={"date": date},
        )
        return {"success": True, "entry_id": entry_id, "date": date}
