import sys
from pathlib import Path

# Garante que o diretório 'src' esteja no path para importações
src_path = str(Path(__file__).resolve().parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from providers.main import run_app


if __name__ == "__main__":
    run_app()
