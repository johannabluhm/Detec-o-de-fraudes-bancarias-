from fastapi.testclient import TestClient
from src.app import app

# Inicializa o cliente de testes, simulando um servidor real
client = TestClient(app)

def test_health_check():
    """Verifica se a API está online e respondendo (Docs route)"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_predicao_transacao_valida():
    """Testa o Caminho Feliz: Uma transação perfeitamente estruturada."""
    payload = {
        "transaction": {
            "step": 1,
            "type": 3,
            "amount": 1500.0,
            "oldbalanceOrg": 5000.0,
            "newbalanceOrig": 3500.0,
            "oldbalanceDest": 1000.0,
            "newbalanceDest": 2500.0
        },
        "infrastructure": "Local"
    }
    
    response = client.post("/predict", json=payload)
    
    # Valida se a requisição foi aceita
    assert response.status_code == 200
    
    # Valida se a estrutura de resposta contém o que o front-end precisa
    data = response.json()
    assert "is_fraud" in data
    assert "fraud_probability" in data
    assert "risk_level" in data
    assert "status" in data

def test_seguranca_valor_negativo():
    """
    Testa a Segurança: O sistema deve barrar valores negativos
    antes mesmo de acionar o modelo de Machine Learning.
    """
    payload = {
        "transaction": {
            "step": 1,
            "type": 3,
            "amount": -500.0,  # Valor malicioso
            "oldbalanceOrg": 5000.0,
            "newbalanceOrig": 5500.0,
            "oldbalanceDest": 1000.0,
            "newbalanceDest": 500.0
        },
        "infrastructure": "Local"
    }
    
    response = client.post("/predict", json=payload)
    
    # 422 é o código HTTP para 'Unprocessable Entity' (Entidade Não Processável)
    assert response.status_code == 422
    assert "amount" in response.text # Verifica se o erro aponta para a coluna correta

def test_seguranca_dados_faltantes():
    """
    Testa a Segurança: O sistema não pode quebrar se o front-end
    esquecer de enviar uma informação obrigatória.
    """
    payload = {
        "transaction": {
            "step": 1,
            "type": 3,
            # 'amount' foi removido propositalmente
            "oldbalanceOrg": 5000.0,
            "newbalanceOrig": 5000.0,
            "oldbalanceDest": 1000.0,
            "newbalanceDest": 1000.0
        },
        "infrastructure": "Local"
    }
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 422
    assert "amount" in response.text