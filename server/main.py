import logging

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from server.config import settings
from server.tools import coach, finance

logger = logging.getLogger("personal-ai")

mcp = FastMCP(name="personal-ai")

coach.register(mcp)
finance.register(mcp)


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "finance_sync_configured": not settings.finance_sync_is_localhost,
        }
    )


def main() -> None:
    if settings.finance_sync_is_localhost:
        logger.warning(
            "FINANCE_SYNC_BASE_URL no está configurada (vale %s, el propio host): "
            "las 8 tools finance_* se llamarán al propio servidor MCP y devolverán "
            "404. Define FINANCE_SYNC_BASE_URL en el entorno para que apunte a "
            "finance-sync.",
            settings.finance_sync_base_url,
        )
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=settings.port,
        path=f"/mcp/{settings.mcp_secret}",
    )


if __name__ == "__main__":
    main()
