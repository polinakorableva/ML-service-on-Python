import os
from sqlalchemy import create_engine, text
import pandas as pd

DATABASE_URL = os.getenv("DASHBOARD_DB_URL") or os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)


def get_user_by_email(email: str) -> dict | None:
    query = text("""
        SELECT id, email, balance, role
        FROM users
        WHERE email = :email
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"email": email})
        row = result.fetchone()

    if row is None:
        return None

    return dict(row._mapping)


def get_transactions(user_id: int) -> pd.DataFrame:
    query = text("""
        SELECT
            id,
            amount,
            type,
            description,
            created_at
        FROM transactions
        WHERE user_id = :user_id
        ORDER BY created_at DESC
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"user_id": user_id})

    return df


def get_prediction_jobs(user_id: int) -> pd.DataFrame:
    query = text("""
        SELECT
            pj.id,
            pj.status,
            pj.result,
            pj.created_at,
            mm.name AS model_name
        FROM prediction_jobs pj
        LEFT JOIN ml_models mm ON pj.model_id = mm.id
        WHERE pj.user_id = :user_id
        ORDER BY pj.created_at DESC
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"user_id": user_id})

    return df


def get_daily_spending(user_id: int) -> pd.DataFrame:
    query = text("""
        SELECT
            DATE(created_at) AS day,
            SUM(ABS(amount)) AS spent
        FROM transactions
        WHERE
            user_id = :user_id
            AND type = 'debit'
            AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY day ASC
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"user_id": user_id})

    return df


def get_service_stats() -> dict:
    query = text("""
        SELECT
            (SELECT COUNT(*) FROM users) AS total_users,
            (SELECT COUNT(*) FROM prediction_jobs) AS total_jobs,
            (SELECT COUNT(*) FROM prediction_jobs WHERE status = 'done') AS done_jobs,
            (SELECT COUNT(*) FROM prediction_jobs WHERE status = 'failed') AS failed_jobs,
            (SELECT COALESCE(SUM(ABS(amount)), 0)
             FROM transactions WHERE type = 'debit') AS total_spent
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        row = result.fetchone()

    return dict(row._mapping)