FROM python:3.10-slim

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir mlflow[extras]==2.6.0

VOLUME /mlflow

EXPOSE 5000

CMD ["mlflow", "server", "--backend-store-uri", "${MLFLOW_BACKEND_STORE_URI}", "--default-artifact-root", "${MLFLOW_DEFAULT_ARTIFACT_ROOT}", "--host", "0.0.0.0", "--port", "5000"]
