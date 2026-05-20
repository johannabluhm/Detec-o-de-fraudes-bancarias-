import os
import subprocess
import sys
import time
from pathlib import Path

def iniciar_aplicacao():
    print("===================================================")
    print(" INICIANDO PLATAFORMA ANTI FRAUDE - MVP ")
    print("===================================================")

    projeto_dir = Path(__file__).resolve().parent
    python_executable = sys.executable

    # 1. Iniciar API FastAPI nos bastidores
    print("Iniciando API de Detecção (Back-end)...")
    api_process = subprocess.Popen(
        [python_executable, "-m", "uvicorn", "src.app:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=projeto_dir
    )

    # Verificação de Saúde da API
    import requests
    for _ in range(10):
        try:
            if requests.get("http://127.0.0.1:8000/health", timeout=1).status_code == 200:
                print("API Online!")
                break
        except:
            pass
        time.sleep(1)

    # 2. Iniciar Dashboard Streamlit
    env_vars = os.environ.copy()
    env_vars["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    print("Abrindo Dashboard de Monitoramento (Front-end)...")
    try:
        frontend_path = projeto_dir / "src" / "frontend.py"
        subprocess.run(
            [python_executable, "-m", "streamlit", "run", str(frontend_path), "--server.port", "8501"],
            cwd=projeto_dir,
            env=env_vars,
        )
    except KeyboardInterrupt:
        print("\nSessao encerrada pelo usuario.")
    except Exception as e:
        print(f"\nErro ao iniciar aplicacao: {e}")
    finally:
        api_process.terminate()
        print("Operacao finalizada.")

if __name__ == "__main__":
    iniciar_aplicacao()