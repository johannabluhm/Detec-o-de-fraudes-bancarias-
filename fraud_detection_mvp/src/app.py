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


# Mock de banco de dados para Velocity (Em produção seria um Redis/SQL)
history_db = {}

# Esquema de Validação de Dados (Segurança)
class Transaction(BaseModel):
    step: int = Field(..., description="Unidade de tempo no mundo real")
    type: str = Field(..., description="Tipo de transação (TRANSFER ou CASH_OUT)")
    amount: float = Field(..., gt=0, description="Valor da transação")
    oldbalanceOrg: float = Field(..., description="Saldo inicial da origem")
    newbalanceOrig: float = Field(..., description="Saldo final da origem")
    oldbalanceDest: float = Field(..., description="Saldo inicial do destino")
    newbalanceDest: float = Field(..., description="Saldo final do destino")
    nameOrig: str = Field(..., description="ID da conta de origem para cálculo de velocity")

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
    # Nota: SageMaker precisaria ser atualizado para o novo schema de features
    try:
        client = boto3.client("sagemaker-runtime")
        payload = json.dumps(data)
        response = client.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType="application/json",
            Body=payload
        )
        result = json.loads(response["Body"].read().decode())
        return {
            "is_fraud": result.get("prediction") == 1,
            "fraud_probability": result.get("probability", 0.5),
            "risk_level": "Alto" if result.get("probability", 0) > 0.8 else "Médio",
            "status": "Processado via AWS SageMaker"
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao chamar AWS SageMaker: {e}")


@app.post("/predict")
def predict_fraud(request: PredictionRequest):
    trans = request.transaction
    infra = request.infrastructure

    if infra == "AWS":
        return call_sagemaker(trans.model_dump())

    if model is None:
        raise HTTPException(status_code=500, detail="Modelo local não disponível.")

    # 1. Atualizar histórico de Velocity
    history_db[trans.nameOrig] = history_db.get(trans.nameOrig, 0) + 1
    
    # 2. Engenharia de Features em tempo real (Sync com preprocessing.py)
    type_map = {'CASH_OUT': 1, 'TRANSFER': 4}
    mapped_type = type_map.get(trans.type.upper(), -1)
    
    if mapped_type == -1:
        return {
            "is_fraud": False,
            "fraud_probability": 0.0,
            "risk_level": "Baixo",
            "status": "Tipo de transação sem histórico de fraude (Aprovado automaticamente)"
        }

    features = {
        'type': mapped_type,
        'amount': trans.amount,
        'oldbalanceOrg': trans.oldbalanceOrg,
        'newbalanceOrig': trans.newbalanceOrig,
        'oldbalanceDest': trans.oldbalanceDest,
        'newbalanceDest': trans.newbalanceDest,
        'trans_count_orig': history_db[trans.nameOrig],
        'errorBalanceOrig': trans.newbalanceOrig + trans.amount - trans.oldbalanceOrg,
        'errorBalanceDest': trans.oldbalanceDest + trans.amount - trans.newbalanceDest,
        'hour': trans.step % 24
    }

    input_data = pd.DataFrame([features])

    try:
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0][1]

        risk_level = "Alto" if probability > 0.8 else "Médio" if probability > 0.5 else "Baixo"

        return {
            "is_fraud": bool(prediction),
            "fraud_probability": round(float(probability), 4),
            "risk_level": risk_level,
            "status": "Transação bloqueada (ALERTA DE FRAUDE)" if prediction == 1 else "Transação aprovada",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar predição: {e}")