import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

import uvicorn
from app.platform.config import settings
from app.platform.logging import configure_logging


def main() -> None:
    configure_logging()
    uvicorn.run(
        "app.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
