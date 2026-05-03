from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from starlette.requests import Request
from starlette.responses import JSONResponse

from server.config import settings
from server.tools import coach

verifier = StaticTokenVerifier(
    tokens={
        settings.mcp_secret: {
            "client_id": "claude-ai",
            "scopes": ["read"],
        }
    },
    required_scopes=["read"],
)

mcp = FastMCP(name="personal-ai", auth=verifier)

coach.register(mcp)


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def main() -> None:
    mcp.run(transport="http", host="0.0.0.0", port=settings.port)


if __name__ == "__main__":
    main()
