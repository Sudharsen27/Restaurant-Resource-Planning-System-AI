import uvicorn

from app.utils.config import settings

if __name__ == "__main__":
    # reload=True for local dev so code changes apply without killing the process.
    # Set reload=False (or use a production process manager) when deploying.
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
