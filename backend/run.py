from __future__ import annotations

import uvicorn

from backend.app.bootstrap import bootstrap_application


def main() -> None:
    settings = bootstrap_application()
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()