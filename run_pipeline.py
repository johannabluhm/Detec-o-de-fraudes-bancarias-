import subprocess
import sys
import time
import os

def executar_comando(comando, descricao):
    print(f"\n[ETAPA] Iniciando: {descricao}...")
    try:
        # Usando sys.executable para garantir que usamos o mesmo python
        if comando.startswith("venv"):
             # Se o comando explicitamente pede venv, tentamos respeitar, 
             # mas para portabilidade em diferentes ambientes, sys.executable é melhor.
             pass
             
        subprocess.run(comando, shell=True, check=True)
        print(f"[SUCESSO] {descricao} finalizada sem erros.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO CRITICO] Falha na execucao da etapa: {descricao}.")
        sys.exit(1)

if __name__ == "__main__":
    print("===================================================")
    print(" INICIANDO PIPELINE DO MVP DE DETECCAO DE FRAUDES  ")
    print("===================================================")

    python_exe = sys.executable

    # Passo 1: Instalação de dependências (Garante que o ambiente está pronto antes de rodar código)
    # Comentado pois o ambiente 3.14 já possui as dependências instaladas manualmente.
    # executar_comando(
    #    f"{python_exe} -m pip install -q -r fraud_detection_mvp/requirements.txt",
    #    "Instalacao/Verificacao de dependencias do projeto",
    # )

    # Passo 2: Pré-processamento e Engenharia de Features (Gera X_train, X_test, holdout)
    executar_comando(f"{python_exe} fraud_detection_mvp/src/preprocessing.py", "Processamento de Dados e Engenharia de Features")

    # Passo 3: Treinamento do Modelo XGBoost (Usa X_train e X_test para Early Stopping)
    executar_comando(f"{python_exe} fraud_detection_mvp/src/model.py", "Treinamento do Modelo (XGBoost + Early Stopping)")

    # Passo 4: Validacao Final (Holdout)
    executar_comando(f"{python_exe} fraud_detection_mvp/src/evaluate_holdout.py", "Validacao Final na Base Holdout (Dados Inéditos)")

    # Passo 5: Testes de Integridade da API
    executar_comando(f"{python_exe} -m pytest -v fraud_detection_mvp/tests/test_api.py", "Testes de Seguranca e Regras da API")

    # Passo 6: Subida do Servidor
    print("\n[ETAPA] Iniciando Servidores...")

    # 1. API FastAPI (Back-end)
    print("Iniciando API FastAPI...")
    api_process = subprocess.Popen([python_exe, "-m", "uvicorn", "src.app:app", "--host", "127.0.0.1", "--port", "8000"], cwd="fraud_detection_mvp")

    # Verificação de Saúde
    import requests
    for i in range(15):
        try:
            if requests.get("http://127.0.0.1:8000/health", timeout=1).status_code == 200:
                print(f"API Online em {i+1}s!")
                break
        except:
            pass
        time.sleep(1)

    # 2. Interface Visual (Streamlit)
    print("Abrindo Dashboard de Monitoramento...")
    try:
        subprocess.run([python_exe, "-m", "streamlit", "run", "src/frontend.py", "--server.port", "8501"], cwd="fraud_detection_mvp")
    except KeyboardInterrupt:
        print("\n[INFO] Encerrando sistema pelo usuario...")
    finally:
        api_process.terminate()
        print("[SUCESSO] Pipeline e servidores encerrados.")
