import pandas as pd
import os
from pathlib import Path

def load_and_verify(file_path):
    if not os.path.exists(file_path):
        print(f"Erro: O arquivo {file_path} não foi localizado.")
        print(f"Diretório atual de execução: {os.getcwd()}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        print("Arquivo carregado com sucesso.")
        
        print("\nResumo da Base de Dados:")
        print(f"Total de registros: {df.shape[0]}")
        print(f"Total de colunas: {df.shape[1]}")
        
        null_counts = df.isnull().sum().sum()
        print(f"Total de valores nulos globais: {null_counts}")
        
        if 'isFraud' in df.columns:
            fraud_count = df['isFraud'].value_counts()
            print("\nDistribuição da classe alvo (isFraud):")
            print(fraud_count)
            
        return df
    
    except Exception as e:
        print(f"Erro ao carregar o arquivo: {e}")
        return None

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_PATH = BASE_DIR / "data" / "raw" / "arquivo.csv"
    
    data = load_and_verify(str(DATA_PATH))