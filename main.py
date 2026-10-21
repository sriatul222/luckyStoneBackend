import os

from app.main import app


if __name__ == "__main__":
    import uvicorn

    # Local development server (Render runs the startCommand in render.yaml instead).
    # 0.0.0.0 so the Android emulator (10.0.2.2) and phones on the same Wi-Fi can connect.
    # PORT can be set in .env; 8000 by default.
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
