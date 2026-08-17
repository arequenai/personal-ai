import json
from datetime import date, timedelta

import pytest
import respx
from fastmcp import Client, FastMCP
from httpx import Response

from server.config import settings
from server.tools import coach


@pytest.fixture
def mcp_server() -> FastMCP:
    server = FastMCP(name="test")
    coach.register(server)
    return server


@pytest.fixture
def api_mock():
    with respx.mock(
        base_url=settings.railway_api_base, assert_all_called=False
    ) as router:
        yield router


def _payload(result):
    return json.loads(result.content[0].text)


async def test_get_training_state_default_window(mcp_server, api_mock):
    payload = {
        "training_load": [{"date": "2026-08-15", "ctl": 55.0, "atl": 60.0, "tsb": -5.0}],
        "workouts": [],
        "recovery": [],
        "nutrition": [],
    }
    route = api_mock.get("/api/tp/summary").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("coach_get_training_state", {})

    assert route.called
    params = route.calls.last.request.url.params
    to_d = date.today()
    assert params["to_date"] == to_d.isoformat()
    assert params["from_date"] == (to_d - timedelta(days=7)).isoformat()
    assert _payload(result)["training_load"][0]["tsb"] == -5.0


async def test_get_training_state_custom_days_back(mcp_server, api_mock):
    route = api_mock.get("/api/tp/summary").mock(
        return_value=Response(200, json={"training_load": []})
    )

    async with Client(mcp_server) as client:
        await client.call_tool("coach_get_training_state", {"days_back": 30})

    params = route.calls.last.request.url.params
    to_d = date.today()
    assert params["from_date"] == (to_d - timedelta(days=30)).isoformat()


async def test_get_training_load(mcp_server, api_mock):
    payload = [
        {"date": "2026-08-10", "ctl": 54.2, "atl": 61.0, "tsb": -6.8},
        {"date": "2026-08-11", "ctl": 54.5, "atl": 59.3, "tsb": -4.8},
    ]
    route = api_mock.get("/api/tp/training-load").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "coach_get_training_load",
            {"from_date": "2026-08-10", "to_date": "2026-08-11"},
        )

    assert route.called
    params = route.calls.last.request.url.params
    assert params["from_date"] == "2026-08-10"
    assert params["to_date"] == "2026-08-11"
    assert _payload(result)[1]["ctl"] == 54.5


async def test_get_workouts(mcp_server, api_mock):
    payload = [
        {
            "id": "w-1",
            "date": "2026-08-09",
            "sport": "run",
            "duration_s": 16200,
            "tss": 210.0,
        }
    ]
    route = api_mock.get("/api/tp/workouts").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "coach_get_workouts",
            {"from_date": "2026-08-03", "to_date": "2026-08-09"},
        )

    assert route.called
    params = route.calls.last.request.url.params
    assert params["from_date"] == "2026-08-03"
    assert params["to_date"] == "2026-08-09"
    assert _payload(result)[0]["id"] == "w-1"


async def test_get_workout_detail(mcp_server, api_mock):
    payload = {
        "id": "w-1",
        "sport": "run",
        "avg_hr": 152,
        "tss": 210.0,
        "zones": {"z2": 5400, "z3": 9000},
    }
    route = api_mock.get("/api/tp/workout/w-1").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "coach_get_workout_detail", {"workout_id": "w-1"}
        )

    assert route.called
    body = _payload(result)
    assert body["avg_hr"] == 152
    assert body["zones"]["z3"] == 9000


async def test_get_metrics(mcp_server, api_mock):
    payload = [
        {
            "date": "2026-08-14",
            "hrv_ms": 48.0,
            "sleep_h": 7.2,
            "body_battery": 62,
            "weight_kg": 69.0,
        }
    ]
    route = api_mock.get("/api/tp/metrics").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "coach_get_metrics",
            {"from_date": "2026-08-14", "to_date": "2026-08-14"},
        )

    assert route.called
    params = route.calls.last.request.url.params
    assert params["from_date"] == "2026-08-14"
    assert params["to_date"] == "2026-08-14"
    assert _payload(result)[0]["hrv_ms"] == 48.0


async def test_get_athlete(mcp_server, api_mock):
    payload = {
        "name": "Athlete",
        "threshold_hr": 172,
        "zones": [{"zone": "Z2", "min": 131, "max": 145}],
    }
    route = api_mock.get("/api/tp/athlete").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("coach_get_athlete", {})

    assert route.called
    body = _payload(result)
    assert body["threshold_hr"] == 172
    assert body["zones"][0]["zone"] == "Z2"


async def test_get_nutrition(mcp_server, api_mock):
    payload = [
        {
            "date": "2026-08-15",
            "calories": 2100.0,
            "protein_g": 130.0,
            "carbs_g": 220.0,
            "fat_g": 70.0,
            "fiber_g": 28.0,
            "sodium_mg": 2300.0,
            "calories_goal": 2200.0,
            "protein_goal_g": 120.0,
            "alcohol_drinks": 0,
        }
    ]
    route = api_mock.get("/api/nutrition").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "coach_get_nutrition",
            {"from_date": "2026-08-15", "to_date": "2026-08-15"},
        )

    assert route.called
    params = route.calls.last.request.url.params
    assert params["from_date"] == "2026-08-15"
    assert params["to_date"] == "2026-08-15"
    body = _payload(result)
    assert body[0]["protein_g"] == 130.0
    assert body[0]["alcohol_drinks"] == 0


async def test_get_meals(mcp_server, api_mock):
    payload = {
        "date": "2026-08-15",
        "meals": {
            "breakfast": [
                {
                    "name": "Oatmeal",
                    "calories": 350.0,
                    "protein_g": 12.0,
                    "carbs_g": 60.0,
                    "fat_g": 6.0,
                    "position": 0,
                }
            ],
            "lunch": [],
            "dinner": [],
            "snacks": [],
            "other": [],
        },
        "totals": {"calories": 350.0},
    }
    route = api_mock.get("/api/nutrition/2026-08-15/meals").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("coach_get_meals", {"date": "2026-08-15"})

    assert route.called
    body = _payload(result)
    assert body["meals"]["breakfast"][0]["name"] == "Oatmeal"
    assert body["totals"]["calories"] == 350.0


async def test_get_body_composition(mcp_server, api_mock):
    payload = [
        {"date": "2026-08-14", "weight_kg": 69.0, "body_fat_pct": 18.5},
    ]
    route = api_mock.get("/api/body-composition").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "coach_get_body_composition",
            {"from_date": "2026-08-10", "to_date": "2026-08-14"},
        )

    assert route.called
    params = route.calls.last.request.url.params
    assert params["from_date"] == "2026-08-10"
    assert params["to_date"] == "2026-08-14"
    assert _payload(result)[0]["weight_kg"] == 69.0


async def test_search_food(mcp_server, api_mock):
    payload = [
        {
            "mfp_id": 12345,
            "name": "Banana",
            "brand": None,
            "verified": True,
            "calories": 89.0,
        }
    ]
    route = api_mock.get("/api/nutrition/search").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "coach_search_food", {"query": "banana", "limit": 5}
        )

    assert route.called
    sent = route.calls.last.request.url
    assert sent.params["q"] == "banana"
    assert sent.params["limit"] == "5"
    assert _payload(result)[0]["mfp_id"] == 12345


async def test_search_food_default_limit(mcp_server, api_mock):
    route = api_mock.get("/api/nutrition/search").mock(
        return_value=Response(200, json=[])
    )

    async with Client(mcp_server) as client:
        await client.call_tool("coach_search_food", {"query": "rice"})

    assert route.calls.last.request.url.params["limit"] == "10"


async def test_get_food_details(mcp_server, api_mock):
    payload = {
        "mfp_id": 12345,
        "name": "Banana",
        "brand": None,
        "version": "v2",
        "serving_sizes": [
            {
                "weight_id": 1,
                "unit": "medium",
                "value": 1.0,
                "multiplier": 1.0,
                "index": 0,
                "description": "1 medium",
            }
        ],
        "calories_per_serving": 89.0,
        "protein_per_serving_g": 1.1,
        "carbs_per_serving_g": 22.8,
        "fat_per_serving_g": 0.3,
    }
    route = api_mock.get("/api/nutrition/food/12345").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("coach_get_food_details", {"mfp_id": 12345})

    assert route.called
    body_out = _payload(result)
    assert body_out["version"] == "v2"
    assert body_out["serving_sizes"][0]["description"] == "1 medium"


async def test_log_meal_minimal(mcp_server, api_mock):
    payload = {
        "entry_id": "uuid-1",
        "mfp_id": 12345,
        "food_name": "Banana",
        "meal_type": "breakfast",
        "date": "2026-05-06",
        "quantity": 1.0,
        "unit": None,
        "weight_id": None,
        "calories": 89.0,
        "protein_g": 1.1,
        "carbs_g": 22.8,
        "fat_g": 0.3,
    }
    route = api_mock.post("/api/nutrition/log").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "coach_log_meal",
            {"mfp_id": 12345, "meal_type": "breakfast"},
        )

    sent = json.loads(route.calls.last.request.content)
    assert sent == {
        "mfp_id": 12345,
        "meal_type": "breakfast",
        "quantity": 1.0,
        "force": False,
    }
    assert "date" not in sent
    assert "unit" not in sent
    assert _payload(result)["entry_id"] == "uuid-1"


async def test_log_meal_full(mcp_server, api_mock):
    route = api_mock.post("/api/nutrition/log").mock(
        return_value=Response(
            200,
            json={
                "entry_id": "uuid-2",
                "mfp_id": 99,
                "food_name": "Rice",
                "meal_type": "lunch",
                "date": "2026-05-04",
                "quantity": 2.0,
                "unit": "100 g",
                "weight_id": 7,
                "calories": 260.0,
                "protein_g": 5.4,
                "carbs_g": 56.0,
                "fat_g": 0.6,
            },
        )
    )

    async with Client(mcp_server) as client:
        await client.call_tool(
            "coach_log_meal",
            {
                "mfp_id": 99,
                "meal_type": "lunch",
                "date": "2026-05-04",
                "quantity": 2.0,
                "unit": "100 g",
                "force": True,
            },
        )

    sent = json.loads(route.calls.last.request.content)
    assert sent == {
        "mfp_id": 99,
        "meal_type": "lunch",
        "quantity": 2.0,
        "force": True,
        "date": "2026-05-04",
        "unit": "100 g",
    }


async def test_log_meal_conflict_409(mcp_server, api_mock):
    api_mock.post("/api/nutrition/log").mock(
        return_value=Response(
            409,
            json={"detail": "Entry already exists for mfp_id=12345 on 2026-05-06"},
        )
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "coach_log_meal",
            {"mfp_id": 12345, "meal_type": "breakfast"},
        )

    body_out = _payload(result)
    assert body_out["conflict"] is True
    assert "Entry already exists" in body_out["detail"]
    assert "force=True" in body_out["hint"]


async def test_delete_diary_entry(mcp_server, api_mock):
    route = api_mock.delete("/api/nutrition/entry/uuid-3").mock(
        return_value=Response(204)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "coach_delete_diary_entry",
            {"entry_id": "uuid-3", "date": "2026-05-06"},
        )

    assert route.called
    assert route.calls.last.request.url.params["date"] == "2026-05-06"
    assert _payload(result) == {
        "success": True,
        "entry_id": "uuid-3",
        "date": "2026-05-06",
    }


async def test_api_key_header_sent_when_configured(mcp_server, api_mock, monkeypatch):
    monkeypatch.setattr(settings, "railway_api_key", "clave-test")
    route = api_mock.get("/api/nutrition/search").mock(
        return_value=Response(200, json={"results": []})
    )

    async with Client(mcp_server) as client:
        await client.call_tool("coach_search_food", {"query": "banana"})

    assert route.calls.last.request.headers["x-api-key"] == "clave-test"


async def test_no_api_key_header_by_default(mcp_server, api_mock):
    assert settings.railway_api_key == ""
    route = api_mock.get("/api/nutrition/search").mock(
        return_value=Response(200, json={"results": []})
    )

    async with Client(mcp_server) as client:
        await client.call_tool("coach_search_food", {"query": "banana"})

    assert "x-api-key" not in route.calls.last.request.headers
