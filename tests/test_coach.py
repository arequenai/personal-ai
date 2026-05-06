import json

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
