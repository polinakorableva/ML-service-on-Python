import streamlit as st
import plotly.express as px
import pandas as pd
from dashboard.db_queries import (
    get_user_by_email,
    get_transactions,
    get_prediction_jobs,
    get_daily_spending,
    get_service_stats
)

st.set_page_config(
    page_title="ML Service Dashboard",
    page_icon="🤖",
    layout="wide"
)

def show_login_form():
    st.title("🤖 ML Service Dashboard")
    st.subheader("Войдите в систему")

    with st.form("login_form"):
        email = st.text_input("Email")
        submitted = st.form_submit_button("Войти")

    if submitted:
        if not email:
            st.error("Введите email")
            return None

        user = get_user_by_email(email)
        if user is None:
            st.error("Пользователь не найден")
            return None

        return user

    return None

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    user = show_login_form()
    if user is not None:
        st.session_state.user = user
        st.rerun()
    st.stop()

user = st.session_state.user

col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    st.title("🤖 ML Service Dashboard")

with col2:
    st.metric(
        label="Баланс",
        value=f"{user['balance']:.1f} кредитов"
    )

with col3:
    if st.button("Выйти"):
        st.session_state.user = None
        st.rerun()


st.write(f"Добро пожаловать, **{user['email']}**")
st.divider()

tab1, tab2, tab3 = st.tabs([
    "💳 Баланс и транзакции",
    "🔮 Предсказания",
    "📊 Статистика"
])

with tab1:
    st.header("История транзакций")

    df_transactions = get_transactions(user["id"])

    if df_transactions.empty:
        st.info("Транзакций пока нет")
    else:
        total_credited = df_transactions[
            df_transactions["type"].isin(["credit", "promo"])
        ]["amount"].sum()

        total_spent = df_transactions[
            df_transactions["type"] == "debit"
        ]["amount"].abs().sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Текущий баланс", f"{user['balance']:.1f}")
        m2.metric("Всего пополнено", f"{total_credited:.1f}")
        m3.metric("Всего потрачено", f"{total_spent:.1f}")

        st.subheader("Все транзакции")

        df_display = df_transactions.copy()

        type_labels = {
            "credit": "💰 Пополнение",
            "debit":  "🔮 Предсказание",
            "promo":  "🎁 Промокод"
        }
        df_display["type"] = df_display["type"].map(type_labels)

        df_display["created_at"] = pd.to_datetime(
            df_display["created_at"]
        ).dt.strftime("%d.%m.%Y %H:%M")

        df_display = df_display.rename(columns={
            "id":          "ID",
            "amount":      "Сумма",
            "type":        "Тип",
            "description": "Описание",
            "created_at":  "Дата"
        })

        st.dataframe(df_display, hide_index=True, use_container_width=True)

with tab2:
    st.header("История предсказаний")

    df_jobs = get_prediction_jobs(user["id"])

    if df_jobs.empty:
        st.info("Предсказаний пока нет")
    else:
        total    = len(df_jobs)
        done     = len(df_jobs[df_jobs["status"] == "done"])
        failed   = len(df_jobs[df_jobs["status"] == "failed"])
        pending  = len(df_jobs[df_jobs["status"] == "pending"])

        j1, j2, j3, j4 = st.columns(4)
        j1.metric("Всего задач",  total)
        j2.metric("✅ Выполнено", done)
        j3.metric("❌ Ошибок",    failed)
        j4.metric("⏳ В очереди", pending)

        st.subheader("Все задачи")

        df_display = df_jobs.copy()

        status_labels = {
            "done":    "✅ Выполнено",
            "failed":  "❌ Ошибка",
            "pending": "⏳ Ожидание",
            "running": "🔄 Выполняется"
        }
        df_display["status"] = df_display["status"].map(status_labels)

        df_display["created_at"] = pd.to_datetime(
            df_display["created_at"]
        ).dt.strftime("%d.%m.%Y %H:%M")

        df_display["result"] = df_display["result"].apply(
            lambda x: str(x) if x is not None else "—"
        )

        df_display = df_display.rename(columns={
            "id":          "ID",
            "status":      "Статус",
            "model_name":  "Модель",
            "result":      "Результат",
            "created_at":  "Дата"
        })

        df_display = df_display.drop(columns=["result"], errors="ignore")

        st.dataframe(df_display, hide_index=True, use_container_width=True)

with tab3:
    st.header("Статистика расхода кредитов")

    df_spending = get_daily_spending(user["id"])

    if df_spending.empty:
        st.info("Данных о расходе пока нет — сделайте первое предсказание")
    else:
        fig = px.bar(
            df_spending,
            x="day",
            y="spent",
            title="Расход кредитов за последние 30 дней",
            labels={
                "day":   "Дата",
                "spent": "Потрачено кредитов"
            },
            color_discrete_sequence=["#7C3AED"]
        )

        # Настройка внешнего вида графика
        fig.update_layout(
            xaxis_title="Дата",
            yaxis_title="Кредитов потрачено",
            hovermode="x",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        s1, s2 = st.columns(2)
        s1.metric(
            "Потрачено за 30 дней",
            f"{df_spending['spent'].sum():.1f} кредитов"
        )
        s2.metric(
            "Среднее в день",
            f"{df_spending['spent'].mean():.1f} кредитов"
        )

    if user["role"] == "admin":
        st.divider()
        st.subheader("🔧 Статистика сервиса (Admin)")

        stats = get_service_stats()

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Всего пользователей", stats["total_users"])
        a2.metric("Всего предсказаний",  stats["total_jobs"])
        a3.metric("Успешных",            stats["done_jobs"])
        a4.metric("Ошибок",              stats["failed_jobs"])

        if stats["total_jobs"] > 0:
            success_rate = stats["done_jobs"] / stats["total_jobs"] * 100
            st.progress(
                value=int(success_rate),
                text=f"Успешность: {success_rate:.1f}%"
            )