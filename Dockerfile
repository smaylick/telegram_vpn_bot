FROM python:3.12-slim

WORKDIR /app

# зависимости
COPY requirements.txt .
RUN pip install -r requirements.txt

# исходники бота
COPY app ./app

# старт
CMD ["python", "-m", "app.main"]
