from fastapi import FastAPI

from server.api.scan import router

app = FastAPI(title="Cybersec Analysis Server")

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}