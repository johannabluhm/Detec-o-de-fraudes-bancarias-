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

    # Passo 1: Treinamento do Modelo
    executar_comando(f"{python_exe} fraud_detection_mvp/src/model.py", "Treinamento do Modelo XGBoost")

    # Pausa de seguranca
    time.sleep(2)

    # Passo 2: Validacao Cega
    executar_comando(f"{python_exe} fraud_detection_mvp/src/evaluate_holdout.py", "Validacao na Base Holdout")

    # Passo 3: Garantia de Qualidade
    executar_comando(f"{python_exe} -m pytest -v fraud_detection_mvp/tests/", "Testes Automatizados da API")

    # Passo 4: Subida do Servidor
    print("\n[ETAPA] Subindo os Servidores...")
    
    # 1. Ligando a API em segundo plano
    print("Iniciando API FastAPI nos bastidores...")
    api_process = subprocess.Popen([python_exe, "-m", "uvicorn", "src.app:app", "--host", "127.0.0.1", "--port", "8000"], cwd="fraud_detection_mvp")
    
    # Verificação de Saúde
    import requests
    for _ in range(10):
        try:
            if requests.get("http://127.0.0.1:8000/health").status_code == 200:
                print("API Online!")
                break
        except:
            pass
        time.sleep(1)
    
    # 2. Ligando a interface visual (Streamlit)
    print("Abrindo o Front end no navegador...")
    try:
        subprocess.run([python_exe, "-m", "streamlit", "run", "src/frontend.py"], cwd="fraud_detection_mvp")
    except KeyboardInterrupt:
        print("\nEncerrando o sistema...")
    finally:
        api_process.terminate()
        print("Pipeline e servidores encerrados com seguranca.")
