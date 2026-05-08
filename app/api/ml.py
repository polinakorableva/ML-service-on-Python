import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.schemas.ml import PredictRequest, JobResponse, ModelResponse
from app.services.ml_service import (
    save_model_file,
    validate_sklearn_model,
    create_model_record,
    create_prediction_job,
    get_job,
    get_model
)
from app.core.config import settings
from worker.tasks import run_prediction


router = APIRouter(tags=["ml"])


@router.post("/models/upload", response_model=ModelResponse, status_code=201)
def upload_model(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".pkl"):
        raise HTTPException(status_code=400, detail="Файл должен быть .pkl")
    file_bytes = file.file.read()
    unique_filename = f"{uuid.uuid4()}.pkl"
    file_path = save_model_file(current_user.id, unique_filename, file_bytes)
    try:
        validate_sklearn_model(file_path)
    except ValueError as e:
        import os
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))

    ml_model = create_model_record(
        db=db,
        user_id=current_user.id,
        name=file.filename,
        file_path=file_path
    )

    return ml_model


@router.post("/predict", response_model=JobResponse, status_code=202)
def predict(
    data: PredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.balance < settings.CREDITS_PER_PREDICTION:
        raise HTTPException(status_code=402, detail="Недостаточно кредитов")

    ml_model = get_model(db, data.model_id, current_user.id)
    if ml_model is None:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    job = create_prediction_job(db, current_user.id, data.model_id)
    run_prediction.delay(
        job_id=job.id,
        model_path=ml_model.file_path,
        features=data.features
    )

    return job


@router.get("/predict/{job_id}", response_model=JobResponse)
def get_prediction_result(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = get_job(db, job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return job