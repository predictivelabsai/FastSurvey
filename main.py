"""Deployment entry point."""
from web_app import app

if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", os.getenv("FASTSURVEY_PORT", "5019"))))
