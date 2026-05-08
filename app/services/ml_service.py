import os
import joblib
import numpy as np
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.ml_model import MLModel
from app.models.job import PredictionJob


def save_model_file(user_id: int, filename: str, file_bytes: bytes) -> str:
    user_dir = os.path.join(settings.MODEL_STORAGE_PATH, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    # Путь к файлу
    file_path = os.path.join(user_dir, filename)

    # Записываем байты файла на диск
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return file_path


def validate_sklearn_model(file_path: str) -> None:

    try:
        model = joblib.load(file_path)
    except Exception:
        raise ValueError("Не удалось загрузить файл как sklearn-модель")

    if not hasattr(model, "predict"):
        raise ValueError("Объект не является sklearn-моделью (нет метода predict)")


def create_model_record(db: Session, user_id: int, name: str, file_path: str) -> MLModel:
    ml_model = MLModel(
        user_id=user_id,
        name=name,
        file_path=file_path
    )
    db.add(ml_model)
    db.commit()
    db.refresh(ml_model)
    return ml_model


def create_prediction_job(db: Session, user_id: int, model_id: int) -> PredictionJob:
    job = PredictionJob(
        user_id=user_id,
        model_id=model_id,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int, user_id: int) -> PredictionJob | None:
    return (
        db.query(PredictionJob)
        .filter(PredictionJob.id == job_id, PredictionJob.user_id == user_id)
        .first()
    )


def get_model(db: Session, model_id: int, user_id: int) -> MLModel | None:
    return (
        db.query(MLModel)
        .filter(MLModel.id == model_id, MLModel.user_id == user_id)
        .first()
    )