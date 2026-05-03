from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from server.config import settings
from server.tools import coach

mcp = FastMCP(name="personal-ai")

coach.register(mcp)


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def main() -> None:
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=settings.port,
        path=f"/mcp/{settings.mcp_secret}",
    )


if __name__ == "__main__":
    main()
