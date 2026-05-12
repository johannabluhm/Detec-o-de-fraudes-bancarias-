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
- **Tratamento de Desbalanceamento:** Utilizamos `scale_pos_weight` para lidar com a raridade das fraudes, garantindo que o modelo não ignore os casos críticos.
- **Validação Robusta (Holdout):** 10% dos dados foram isolados e nunca vistos pelo modelo até o teste final. Isso prova que o sistema funciona em dados reais, não apenas "decorou" o passado.
- **API Segura:** Validação de dados via **Pydantic v2**, bloqueando inputs malformados ou valores negativos antes de processar a predição.

---

## 🛠️ Instalação Manual
Caso prefira rodar no seu ambiente local:

1. **Venv:** `python -m venv venv` e ative-o.
2. **Deps:** `pip install -r requirements.txt`
3. **Pipeline:** `python run_pipeline.py` (Isso treina o modelo, testa a API e sobe os servidores).

## 📁 Estrutura do Projeto
- `src/app.py`: API FastAPI de baixa latência.
- `src/model.py`: Lógica de treinamento XGBoost.
- `src/frontend.py`: Dashboard Streamlit para análise de risco.
- `data/`: Bases brutas e processadas.
- `tests/`: Testes de estresse e segurança da API.

---
**Desenvolvido para máxima performance e transparência técnica.** 🚀
