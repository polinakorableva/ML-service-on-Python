from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.api.auth import router as auth_router
from app.api.ml import router as ml_router
from app.api.billing import router as billing_router
from fastapi.responses import ORJSONResponse

app = FastAPI(
    efault_response_class=ORJSONResponse,
    title="ML Service",
    description="Сервис предсказаний с биллингом",
    version="1.0.0"
)

Instrumentator().instrument(app).expose(app)  

app.include_router(auth_router)
app.include_router(ml_router)
app.include_router(billing_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}