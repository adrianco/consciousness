#!/usr/bin/env python3
"""Development server script."""

import uvicorn

from consciousness.main import app

if __name__ == "__main__":
    uvicorn.run(
        "consciousness.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["consciousness"],
        log_level="debug",
    )
