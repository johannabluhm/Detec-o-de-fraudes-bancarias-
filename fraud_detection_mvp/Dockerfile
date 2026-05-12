# Imagem base leve com Python
FROM python:3.11-slim

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho no container
WORKDIR /app

# Instala dependências do sistema necessárias para algumas libs (ex: xgboost)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de dependências
COPY fraud_detection_mvp/requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do projeto
COPY fraud_detection_mvp/ /app/

# Expõe as portas da API (8000) e do Streamlit (8501)
EXPOSE 8000
EXPOSE 8501

# O comando padrão será sobrescrito pelo docker-compose, 
# mas deixamos o uvicorn como fallback
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
