# 🛡️ Fraud Detection MVP - Hackathon Edition

Este projeto é um MVP (Minimum Viable Product) de detecção de fraudes financeiras em tempo real, utilizando Machine Learning de alta performance e uma interface intuitiva.

## 🚀 Fast Track (Docker)
Para rodar o projeto completo (API + Frontend) sem instalar nada localmente:
```bash
docker-compose up --build
```
- **API:** http://localhost:8000/docs
- **Interface:** http://localhost:8501

---

## 🧠 Arquitetura e Inteligência
O motor preditivo foi construído com **XGBoost**, escolhido por sua eficiência em grandes volumes de dados.

### Diferenciais Técnicos:
- **Prevenção de Data Leakage:** Pipeline de dados estritamente cronológico, garantindo que o modelo nunca use informações do futuro (vazamento temporal) para prever o presente.
- **Treinamento com Early Stopping:** Proteção ativa contra overfitting; o treinamento é interrompido assim que o modelo para de generalizar, garantindo estabilidade em produção.
- **Threshold Calibrado por Negócio:** Ponto de corte de decisão (0.62) otimizado via curva Precision-Recall para minimizar perdas financeiras reais (Custo de Fraude vs. Atrito com Cliente).
- **Compliance e Segurança (LGPD):** Anonimização de dados sensíveis (PII) via hashing SHA-256 antes do processamento, garantindo privacidade sem perda de poder preditivo.
- **API Segura:** Validação de dados via **Pydantic v2**, com bloqueio inteligente de tipos de transação não suportados e verificação de saldo insuficiente.

---

## 🛠️ Instalação Manual
Caso prefira rodar no seu ambiente local:

1. **Venv:** `python -m venv venv` e ative-o.
2. **Deps:** `pip install -r requirements.txt`
3. **Pipeline:** `python run_pipeline.py` (Isso treina o modelo, testa a API e sobe os servidores).

## 📱 Mobile App (v4.0)
Novo aplicativo mobile desenvolvido em **React Native + Expo** para alertas de fraude em tempo real na palma da mão.

### Como Rodar o Mobile:
1. Acesse a pasta: `cd fraud_detection_mobile`
2. Instale as dependências: `npm install`
3. Inicie o Expo: `npx expo start`

---

## 📁 Estrutura do Projeto
- `fraud_detection_mvp/`: Core do projeto (API + ML).
- `fraud_detection_mobile/`: Aplicativo mobile React Native.
- `src/app.py`: API FastAPI de baixa latência.
- `src/model.py`: Lógica de treinamento XGBoost.
- `src/frontend.py`: Dashboard Streamlit para análise de risco.
- `data/`: Bases brutas e processadas.
- `tests/`: Testes de estresse e segurança da API.

---
**Desenvolvido para máxima performance e transparência técnica.** 🚀
