import json

import httpx
import pytest
import respx
from fastmcp import Client, FastMCP
from httpx import Response

from server.config import settings
from server.tools import finance


@pytest.fixture
def mcp_server() -> FastMCP:
    server = FastMCP(name="test")
    finance.register(server)
    return server


@pytest.fixture
def api_mock(monkeypatch):
    monkeypatch.setattr(
        settings, "finance_sync_base_url", "http://test.finance-sync.local"
    )
    with respx.mock(
        base_url="http://test.finance-sync.local", assert_all_called=False
    ) as router:
        yield router


def _payload(result):
    return json.loads(result.content[0].text)


async def test_get_portfolio(mcp_server, api_mock):
    payload = {
        "positions": [{"ticker": "AAPL", "shares": 10, "value": 1750.0}],
        "total_value": 1750.0,
    }
    route = api_mock.get("/api/finance/portfolio").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("finance_get_portfolio", {})

    assert route.called
    body = _payload(result)
    assert body["total_value"] == 1750.0
    assert body["positions"][0]["ticker"] == "AAPL"


async def test_list_active_alerts_default(mcp_server, api_mock):
    route = api_mock.get("/api/finance/alerts/active").mock(
        return_value=Response(200, json={"alerts": []})
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("finance_list_active_alerts", {})

    assert route.called
    assert route.calls.last.request.url.params["days"] == "30"
    assert _payload(result) == {"alerts": []}


async def test_list_active_alerts_custom_days(mcp_server, api_mock):
    payload = {"alerts": [{"id": "a1", "ticker": "MSFT", "severity": "high"}]}
    route = api_mock.get("/api/finance/alerts/active").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("finance_list_active_alerts", {"days": 7})

    assert route.calls.last.request.url.params["days"] == "7"
    assert _payload(result)["alerts"][0]["id"] == "a1"


async def test_upcoming_catalysts(mcp_server, api_mock):
    payload = {
        "catalysts": [
            {"ticker": "NVDA", "type": "earnings", "date": "2026-05-22"}
        ]
    }
    route = api_mock.get("/api/finance/catalysts/upcoming").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "finance_upcoming_catalysts", {"days": 21}
        )

    assert route.called
    assert route.calls.last.request.url.params["days"] == "21"
    assert _payload(result)["catalysts"][0]["ticker"] == "NVDA"


async def test_upcoming_catalysts_default(mcp_server, api_mock):
    route = api_mock.get("/api/finance/catalysts/upcoming").mock(
        return_value=Response(200, json={"catalysts": []})
    )

    async with Client(mcp_server) as client:
        await client.call_tool("finance_upcoming_catalysts", {})

    assert route.calls.last.request.url.params["days"] == "14"


async def test_top_overhype(mcp_server, api_mock):
    payload = {"top": [{"ticker": "TSLA", "score": 92.0}]}
    route = api_mock.get("/api/finance/overhype/top").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("finance_top_overhype", {"n": 5})

    assert route.calls.last.request.url.params["n"] == "5"
    assert _payload(result)["top"][0]["ticker"] == "TSLA"


async def test_top_overhype_default(mcp_server, api_mock):
    route = api_mock.get("/api/finance/overhype/top").mock(
        return_value=Response(200, json={"top": []})
    )

    async with Client(mcp_server) as client:
        await client.call_tool("finance_top_overhype", {})

    assert route.calls.last.request.url.params["n"] == "3"


async def test_evaluate_rules(mcp_server, api_mock):
    payload = {"passed": 8, "failed": 2, "violations": [{"rule": "max_concentration"}]}
    route = api_mock.post("/api/finance/rules/evaluate").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("finance_evaluate_rules", {})

    assert route.called
    body = _payload(result)
    assert body["passed"] == 8
    assert body["failed"] == 2


async def test_generate_digest(mcp_server, api_mock):
    payload = {"digest_id": "d-2026-05-08", "summary": "All systems nominal"}
    route = api_mock.post("/api/finance/digest/generate").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("finance_generate_digest", {})

    assert route.called
    assert _payload(result)["digest_id"] == "d-2026-05-08"


async def test_moat_coverage(mcp_server, api_mock):
    payload = {"covered": 12, "total": 15, "missing": ["XYZ", "ABC", "DEF"]}
    route = api_mock.get("/api/finance/moat/coverage").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool("finance_moat_coverage", {})

    assert route.called
    body = _payload(result)
    assert body["covered"] == 12
    assert "XYZ" in body["missing"]


async def test_moat_scorecard(mcp_server, api_mock):
    payload = {
        "ticker": "AAPL",
        "moat_rating": "wide",
        "score": 87,
        "factors": ["network_effects", "switching_costs"],
    }
    route = api_mock.get("/api/finance/moat/scorecard/AAPL").mock(
        return_value=Response(200, json=payload)
    )

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "finance_moat_scorecard", {"ticker": "aapl"}
        )

    assert route.called
    body = _payload(result)
    assert body["ticker"] == "AAPL"
    assert body["moat_rating"] == "wide"


async def test_moat_scorecard_uppercases_ticker(mcp_server, api_mock):
    route = api_mock.get("/api/finance/moat/scorecard/MSFT").mock(
        return_value=Response(200, json={"ticker": "MSFT", "score": 90})
    )

    async with Client(mcp_server) as client:
        await client.call_tool("finance_moat_scorecard", {"ticker": "msft"})

    assert route.called


async def test_aggregator_5xx_raises(mcp_server, api_mock):
    api_mock.get("/api/finance/portfolio").mock(
        return_value=Response(500, json={"error": "internal"})
    )

    async with Client(mcp_server) as client:
        with pytest.raises(Exception) as exc_info:
            await client.call_tool("finance_get_portfolio", {})

    msg = str(exc_info.value)
    assert "500" in msg or "Internal Server Error" in msg or "HTTPStatusError" in msg


def test_httpx_status_error_class_exists():
    assert hasattr(httpx, "HTTPStatusError")
