"""Entrypoint launcher for RAG Knowledge Engine with WindowsSelectorEventLoopPolicy.

Enforces SelectorEventLoop with loop='none' so Uvicorn does not override WindowsSelectorEventLoopPolicy.
This enables async psycopg3 (PostgreSQL pgvector) and motor (MongoDB Atlas) to run simultaneously on Windows.
"""
import asyncio
import sys
import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        loop="none",
    )
    server = uvicorn.Server(config)
    loop = asyncio.WindowsSelectorEventLoopPolicy().new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(server.serve())
    finally:
        loop.close()
