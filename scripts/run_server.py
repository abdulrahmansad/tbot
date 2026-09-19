from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "tbot.api:app",
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
