from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pickle
import pandas as pd
from pathlib import Path
import boto3
import json
import os

# Inicialização da API
app = FastAPI(
    title="API de Detecção de Fraudes",
    description="MVP para o Hackathon",
    version="2.0.0",
)

# Configuração de caminhos e carregamento do modelo
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "xgboost_fraud_model.pkl"
SAGEMAKER_ENDPOINT = os.getenv("SAGEMAKER_ENDPOINT", "fraud-detection-endpoint")


def load_model() -> object:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Modelo não encontrado em {MODEL_PATH}")

    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


model = None
try:
    model = load_model()
except Exception as e:
    print(f"Aviso: não foi possível carregar o modelo de predição. Erro: {e}")
    model = None


# Esquema de Validação de Dados (Segurança)
class Transaction(BaseModel):
    step: int = Field(..., description="Unidade de tempo no mundo real")
    type: int = Field(..., description="Tipo de transação codificada (ex: 0 a 4)")
    amount: float = Field(..., gt=0, description="Valor da transação (deve ser maior que zero)")
    oldbalanceOrg: float = Field(..., description="Saldo inicial da origem")
    newbalanceOrig: float = Field(..., description="Saldo final da origem")
    oldbalanceDest: float = Field(..., description="Saldo inicial do destino")
    newbalanceDest: float = Field(..., description="Saldo final do destino")


class PredictionRequest(BaseModel):
    transaction: Transaction
    infrastructure: str = Field("Local", description="Infraestrutura: 'Local' ou 'AWS'")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "aws_configured": SAGEMAKER_ENDPOINT != "fraud-detection-endpoint"
    }


def call_sagemaker(data: dict):
    try:
        client = boto3.client("sagemaker-runtime")
        payload = json.dumps(data)
        response = client.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType="application/json",
            Body=payload
        )
        result = json.loads(response["Body"].read().decode())
        # Formato esperado da AWS deve bater com o da nossa API
        return {
            "is_fraud": result.get("prediction") == 1,
            "fraud_probability": result.get("probability", 0.5),
            "risk_level": "Alto" if result.get("probability", 0) > 0.8 else "Médio",
            "status": "Processado via AWS SageMaker"
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao chamar AWS SageMaker: {e}. Verifique credenciais.")


@app.post("/predict")
def predict_fraud(request: PredictionRequest):
    transaction = request.transaction
    infra = request.infrastructure

    if infra == "AWS":
        return call_sagemaker(transaction.model_dump())

    if model is None:
        raise HTTPException(status_code=500, detail="Modelo local não disponível.")

    input_data = pd.DataFrame([transaction.model_dump()])

    try:
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0][1]

        risk_level = "Alto" if probability > 0.8 else "Médio" if probability > 0.5 else "Baixo"

        return {
            "is_fraud": bool(prediction),
            "fraud_probability": round(float(probability), 4),
            "risk_level": risk_level,
            "status": "Transação bloqueada" if prediction == 1 else "Transação aprovada",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar predição: {e}")