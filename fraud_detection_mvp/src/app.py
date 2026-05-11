from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pickle
import pandas as pd
from pathlib import Path

# Inicialização da API
app = FastAPI(
    title="API de Detecção de Fraudes",
    description="MVP para o Hackathon",
    version="1.0.0"
)

# Configuração de caminhos e carregamento do modelo
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "xgboost_fraud_model.pkl"

model = None
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
except Exception as e:
    print(f"Aviso: Não foi possível carregar o modelo. Erro: {e}")

# Esquema de Validação de Dados (Segurança)
class Transaction(BaseModel):
    step: int = Field(..., description="Unidade de tempo no mundo real")
    type: int = Field(..., description="Tipo de transação codificada (ex: 0 a 4)")
    amount: float = Field(..., gt=0, description="Valor da transação (deve ser maior que zero)")
    oldbalanceOrg: float = Field(..., description="Saldo inicial da origem")
    newbalanceOrig: float = Field(..., description="Saldo final da origem")
    oldbalanceDest: float = Field(..., description="Saldo inicial do destino")
    newbalanceDest: float = Field(..., description="Saldo final do destino")

@app.post("/predict")
def predict_fraud(transaction: Transaction):
    # Verificação de segurança interna
    if model is None:
        raise HTTPException(status_code=500, detail="Modelo preditivo não disponível.")

    # Conversão dos dados validados para DataFrame
    input_data = pd.DataFrame([transaction.dict()])

    # Realizando a predição
    try:
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0][1]
        
        # Lógica de negócio: definindo risco baseado na probabilidade
        risk_level = "Alto" if probability > 0.8 else "Médio" if probability > 0.5 else "Baixo"

        return {
            "is_fraud": bool(prediction),
            "fraud_probability": round(float(probability), 4),
            "risk_level": risk_level,
            "status": "Transação bloqueada" if prediction == 1 else "Transação aprovada"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar predição: {str(e)}")