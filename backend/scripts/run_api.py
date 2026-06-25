# run_api.py
import os
import uvicorn

# backend/ root (parent of this scripts/ dir) must be on sys.path so "app.main" resolves
# regardless of the caller's working directory.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Port matches the hardcoded baseURL in frontend/src/api/client.js.
    # reload=False deliberately — this script is the production launcher; with
    # reload on, uvicorn spawns a separate watcher+worker process pair, and a
    # plain Stop-Process on the parent PID leaves the actual listening process
    # (the orphaned worker) still running the old code.
    uvicorn.run("app.main:app", host="0.0.0.0", port=4747, reload=False, app_dir=BACKEND_DIR)
