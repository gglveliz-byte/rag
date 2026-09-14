"""Entrypoint launcher for RAG Knowledge Engine.

Supports Windows (WindowsSelectorEventLoopPolicy for async psycopg3/motor)
and Linux/Production/Render (standard loop, PORT and HOST from environment).
"""
import asyncio
import os
import sys
import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))

    if sys.platform == "win32":
        config = uvicorn.Config(
            "app.main:app",
            host="127.0.0.1",
            port=port,
            loop="none",
        )
        server = uvicorn.Server(config)
        loop = asyncio.WindowsSelectorEventLoopPolicy().new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(server.serve())
        finally:
            loop.close()
    else:
        uvicorn.run("app.main:app", host=host, port=port, log_level="info")

