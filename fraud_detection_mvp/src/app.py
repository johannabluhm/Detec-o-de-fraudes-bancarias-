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
    version="3.0.0",
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


import hashlib

# Configurações de Threshold
# Valor 0.62 calibrado via Curva Precision-Recall para minimizar a função de custo:
# Perda = (10 * Falsos Negativos) + (1 * Falsos Positivos)
# Baseado nos resultados do treinamento em model.py
FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.62"))

@app.post("/predict")
def predict_fraud(request: PredictionRequest):
    trans = request.transaction
    infra = request.infrastructure

    # TAREFA 2: Tratar Train-Serve Skew (Bloquear tipos não treinados)
    if trans.type.upper() not in ['TRANSFER', 'CASH_OUT']:
        return {
            "is_fraud": False, 
            "fraud_probability": 0.0,
            "risk_level": "Baixo",
            "status": "Transação aprovada (Tipo não monitorado)"
        }

    # TAREFA 6: Anonimizar PII (LGPD)
    account_hash = hashlib.sha256(trans.nameOrig.encode()).hexdigest()
    print(f"Processando transação para conta (hash): {account_hash}")

    if infra == "AWS":
        return call_sagemaker(trans.model_dump())

    if model is None:
        raise HTTPException(status_code=500, detail="Modelo local não disponível.")

    # 1. Atualizar histórico de Velocity
    history_db[trans.nameOrig] = history_db.get(trans.nameOrig, 0) + 1

    # Nova Regra de Segurança Primária: Saldo Insuficiente
    if trans.amount > trans.oldbalanceOrg:
        return {
            "is_fraud": True,
            "fraud_probability": 1.0,
            "risk_level": "Crítico",
            "status": "Transação bloqueada: Saldo insuficiente na conta de origem",
        }
    
    # 2. Engenharia de Features em tempo real (Sync com preprocessing.py)
    type_map = {
        'CASH_OUT': 1, 
        'TRANSFER': 4, 
        'PAYMENT': 3, 
        'CASH_IN': 0, 
        'DEBIT': 2
    }
    mapped_type = type_map.get(trans.type.upper(), -1)
    
    if mapped_type == -1:
        # Em vez de aprovar tudo, logar e usar um valor neutro ou barrar se for política rígida
        mapped_type = 3 # Default para PAYMENT se desconhecido (menos fraudulento no dataset)

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
        
        # TAREFA 5: Usar threshold calibrado para decisão
        is_fraud = probability > FRAUD_THRESHOLD
        risk_level = "Alto" if probability > 0.8 else "Médio" if probability > FRAUD_THRESHOLD else "Baixo"

        return {
            "is_fraud": bool(is_fraud),
            "fraud_probability": round(float(probability), 4),
            "risk_level": risk_level,
            "status": "Transação bloqueada (ALERTA DE FRAUDE)" if is_fraud else "Transação aprovada",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar predição: {e}")