import os
import subprocess
import sys
import time
from pathlib import Path

def iniciar_aplicacao():
    print("===================================================")
    print(" INICIANDO APLICACAO WEB DO MVP ")
    print("===================================================")

    projeto_dir = Path(__file__).resolve().parent
    python_executable = sys.executable

    print("Ligando API FastAPI nos bastidores...")
    env_vars = os.environ.copy()
    env_vars["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    api_process = subprocess.Popen(
        [python_executable, "-m", "uvicorn", "src.app:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=projeto_dir,
        env=env_vars,
    )

    print("Aguardando inicializacao do motor preditivo...")
    
    # Verificação de Saúde da API
    import requests
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=1)
            if response.status_code == 200:
                print("API carregada com sucesso!")
                break
        except requests.exceptions.ConnectionError:
            pass
        print(f"Tentativa {i+1}/{max_retries}...")
        time.sleep(1)
    else:
        print("Erro: A API demorou muito para responder. Verifique os logs.")

    print("Abrindo a interface visual no navegador...")
    try:
        frontend_path = projeto_dir / "src" / "frontend.py"
        subprocess.run(
            [python_executable, "-m", "streamlit", "run", str(frontend_path)],
            cwd=projeto_dir,
            env=env_vars,
        )
    except KeyboardInterrupt:
        print("\nComando de encerramento recebido...")
    finally:
        api_process.terminate()
        api_process.wait()
        print("Servidores desligados com seguranca. Operacao finalizada.")

if __name__ == "__main__":
    iniciar_aplicacao()