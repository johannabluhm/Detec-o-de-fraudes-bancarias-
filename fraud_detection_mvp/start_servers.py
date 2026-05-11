import subprocess
import time
import sys
import os
from pathlib import Path

def iniciar_aplicacao():
    print("===================================================")
    print(" INICIANDO APLICACAO WEB DO MVP ")
    print("===================================================")

    projeto_dir = Path(__file__).resolve().parent

    print("Ligando API FastAPI nos bastidores...")
    
    api_process = subprocess.Popen(
        ["uvicorn", "src.app:app", "--reload"], 
        cwd=projeto_dir
    )
    
    print("Aguardando inicializacao do motor preditivo...")
    time.sleep(3)
    
    # Criando configuracao para bloquear a pergunta de email do Streamlit
    env_vars = os.environ.copy()
    env_vars["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    
    print("Abrindo a interface visual no navegador...")
    try:
        frontend_path = projeto_dir / "src" / "frontend.py"
        subprocess.run(
            ["streamlit", "run", str(frontend_path)], 
            cwd=projeto_dir,
            env=env_vars
        )
    except KeyboardInterrupt:
        print("\nComando de encerramento recebido...")
    finally:
        api_process.terminate()
        print("Servidores desligados com seguranca. Operacao finalizada.")

if __name__ == "__main__":
    iniciar_aplicacao()