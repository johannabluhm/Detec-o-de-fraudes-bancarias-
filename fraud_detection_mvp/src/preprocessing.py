import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path

def preprocess_and_split(df):
    # Remoção de colunas com risco de vazamento de dados
    cols_to_drop = ['nameOrig', 'nameDest', 'isFlaggedFraud']
    df_cleaned = df.drop(columns=cols_to_drop)
    
    # Mapeamento fixo para garantir consistência entre Treino, API e Frontend
    # CASH_IN -> 0, CASH_OUT -> 1, DEBIT -> 2, PAYMENT -> 3, TRANSFER -> 4
    type_map = {
        'CASH_IN': 0, 'DEPOSITO': 0,
        'CASH_OUT': 1, 'SAQUE': 1,
        'DEBIT': 2, 'DEBITO': 2,
        'PAYMENT': 3, 'PAGAMENTO': 3,
        'TRANSFER': 4, 'TRANSFERENCIA': 4
    }
    df_cleaned['type'] = df_cleaned['type'].map(type_map)
    
    # Preenchimento de possíveis valores nulos após o mapeamento (caso surja um tipo novo)
    df_cleaned['type'] = df_cleaned['type'].fillna(-1)
    
    # Separação de Features e Target
    X = df_cleaned.drop('isFraud', axis=1)
    y = df_cleaned['isFraud']
    
    # Primeiro corte: Separando 10% para o Holdout (Validação Final Cega)
    X_temp, X_holdout, y_temp, y_holdout = train_test_split(
        X, y, test_size=0.10, random_state=42, stratify=y
    )
    
    # Segundo corte: O restante (90%) é dividido em Treino (80%) e Teste (20%)
    X_train, X_test, y_train, y_test = train_test_split(
        X_temp, y_temp, test_size=0.20, random_state=42, stratify=y_temp
    )
    
    print("Divisão de dados concluída com sucesso.")
    print(f"Treino: {X_train.shape[0]} amostras para o aprendizado.")
    print(f"Teste: {X_test.shape[0]} amostras para o ajuste de hiperparâmetros.")
    print(f"Holdout: {X_holdout.shape[0]} amostras intocáveis para o teste final.")
    
    return X_train, X_test, y_train, y_test, X_holdout, y_holdout

def save_holdout(X_holdout, y_holdout):
    base_dir = Path(__file__).resolve().parent.parent
    processed_dir = base_dir / "data" / "processed"
    
    # Cria a pasta caso ela não exista
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Junta as features e o target novamente para salvar em um único CSV
    holdout_df = X_holdout.copy()
    holdout_df['isFraud'] = y_holdout
    
    file_path = processed_dir / "holdout_data.csv"
    holdout_df.to_csv(file_path, index=False)
    print(f"\nArquivo de validação cega salvo em: {file_path}")

if __name__ == "__main__":
    from data_loader import load_and_verify
    
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / "data" / "raw" / "arquivo.csv"
    
    df = load_and_verify(str(data_path))
    
    if df is not None:
        # Recebendo as 6 variáveis após a dupla divisão
        X_train, X_test, y_train, y_test, X_holdout, y_holdout = preprocess_and_split(df)
        
        # Salvando o lote isolado para simulação futura
        save_holdout(X_holdout, y_holdout)