import os
import joblib
import numpy as np
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.job import PredictionJob
from app.models.user import User
from app.models.billing import Transaction


@celery_app.task(bind=True, max_retries=3)
def run_prediction(self, job_id: int, model_path: str, features: list):
    """
    Фоновая задача: загружает модель, делает предсказание,
    списывает кредит, сохраняет результат.
    """
    db: Session = SessionLocal()

    try:
        job = db.query(PredictionJob).filter(PredictionJob.id == job_id).first()
        if job is None:
            return

        job.status = "running"
        db.commit()

        # Шаг 2 — загружаем модель с диска
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Файл модели не найден: {model_path}")

        model = joblib.load(model_path)

        X = np.array(features).reshape(1, -1)
        prediction = model.predict(X)
        result = prediction.tolist()

        user = db.query(User).filter(User.id == job.user_id).first()

        user.balance -= settings.CREDITS_PER_PREDICTION

        transaction = Transaction(
            user_id=job.user_id,
            amount=-settings.CREDITS_PER_PREDICTION,
            type="debit",
            description=f"Предсказание job#{job_id}"
        )
        db.add(transaction)

        job.status = "done"
        job.result = {"prediction": result}

        db.commit()

    except Exception as exc:
        db.rollback()

        try:
            job = db.query(PredictionJob).filter(PredictionJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.result = {"error": str(exc)}
                db.commit()
        except Exception:
            pass

        raise self.retry(exc=exc, countdown=5)

    finally:
        db.close()