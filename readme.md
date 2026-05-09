# ML Service
Сервис для запуска ML-предсказаний с биллингом на кредитах. Загружаешь sklearn-модель — получаешь предсказание. Оплата только за успешный результат.

## Запуск
'''bash
cp .env.example .env
docker-compose up --build
docker exec -it ml-service-in-python-api-1 alembic upgrade head
'''

## Сервисы
API + Swagger: http://localhost:8000/docs  
Дашборд: http://localhost:8501  
Grafana: http://localhost:3000 (admin / admin) 

## Стек
Python, FastAPI, PostgreSQL, Celery, Redis, Scikit-learn, Streamlit, Prometheus, Grafana, Docker

## Как работает:
1) Регистрируешься — получаешь 10 кредитов
2) Загружаешь .pkl модель через POST /models/upload
3) Отправляешь данные через POST /predict — задача уходит в очередь
4) Получаешь результат через GET /predict/{job_id}
5) За каждое успешное предсказание списывается 1 кредит