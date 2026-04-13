import uvicorn
import os

if __name__ == "__main__":
    # reload=True spawns a second process which causes the Telegram bot
    # conflict error. Disable reload — use start.bat which handles restarting.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
