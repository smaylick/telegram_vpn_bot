FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app
COPY app/.env .env
WORKDIR /app/app
CMD ["python", "main.py"]
