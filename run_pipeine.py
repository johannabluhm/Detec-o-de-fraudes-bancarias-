import subprocess
import sys
import time

def executar_comando(comando, descricao):
    print(f"\n[ETAPA] Iniciando: {descricao}...")
    try:
        subprocess.run(comando, shell=True, check=True)
        print(f"[SUCESSO] {descricao} finalizada sem erros.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO CRITICO] Falha na execucao da etapa: {descricao}.")
        sys.exit(1)

if __name__ == "__main__":
    print("===================================================")
    print(" INICIANDO PIPELINE DO MVP DE DETECCAO DE FRAUDES  ")
    print("===================================================")

    # Passo 1: Treinamento do Modelo
    executar_comando("venv\\Scripts\\python.exe fraud_detection_mvp/src/model.py", "Treinamento do Modelo XGBoost")

    # Pausa de seguranca para garantir que o arquivo do modelo foi gravado no disco
    time.sleep(2)

    # Passo 2: Validacao Cega
    executar_comando("venv\\Scripts\\python.exe fraud_detection_mvp/src/evaluate_holdout.py", "Validacao na Base Holdout")

    # Passo 3: Garantia de Qualidade
    executar_comando("venv\\Scripts\\pytest.exe -v fraud_detection_mvp/tests/", "Testes Automatizados da API")

    # Passo 4: Subida do Servidor
    print("\n[ETAPA] Subindo os Servidores...")
    
    # 1. Ligando a API em segundo plano (Popen)
    print("Iniciando API FastAPI nos bastidores...")
    api_process = subprocess.Popen(["venv\\Scripts\\uvicorn.exe", "src.app:app", "--reload"], cwd="fraud_detection_mvp")
    
    # Aguardando 3 segundos para a API carregar completamente
    time.sleep(3)
    
    # 2. Ligando a interface visual (Streamlit)
    print("Abrindo o Front end no navegador...")
    try:
        subprocess.run(["venv\\Scripts\\streamlit.exe", "run", "src/frontend.py"], cwd="fraud_detection_mvp")
    except KeyboardInterrupt:
        print("\nEncerrando o sistema...")
    finally:
        # Quando o usuario encerrar o Streamlit, desligamos a API tambem
        api_process.terminate()
        print("Pipeline e servidores encerrados com seguranca.")