from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def read_health():
    return {"status": "ok", "message": "Hello from Janus Backend"}