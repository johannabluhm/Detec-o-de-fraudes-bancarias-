import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path

def preprocess_and_split(df):
    # 1. Filtro de Domínio: Fraudes ocorrem apenas em TRANSFER e CASH_OUT
    df = df[df['type'].isin(['TRANSFER', 'CASH_OUT'])].copy()
    
    # Garantir ordem temporal para evitar leakage em features cumulativas
    df = df.sort_values('step')
    
    # 2. Velocity Features (Novos Atributos Comportamentais - Sem Leakage)
    df['trans_count_orig'] = df.groupby('nameOrig').cumcount() + 1
    
    # 3. Engenharia de Atributos (Domain Knowledge)
    df['errorBalanceOrig'] = df['newbalanceOrig'] + df['amount'] - df['oldbalanceOrg']
    df['errorBalanceDest'] = df['oldbalanceDest'] + df['amount'] - df['newbalanceDest']
    df['hour'] = df['step'] % 24
    
    # 4. Mapeamento de Tipos
    type_map = {'CASH_OUT': 1, 'TRANSFER': 4}
    df['type'] = df['type'].map(type_map)
    df['type'] = df['type'].fillna(-1)
    
    # 5. Remoção de colunas com risco de vazamento ou irrelevantes
    cols_to_drop = ['nameOrig', 'nameDest', 'isFlaggedFraud']
    df_cleaned = df.drop(columns=cols_to_drop)
    
    # 6. Validação Temporal (Split Cronológico)
    df_cleaned = df_cleaned.sort_values('step')
    X = df_cleaned.drop('isFraud', axis=1)
    y = df_cleaned['isFraud']
    
    # Divisão manual para manter a ordem temporal
    total_len = len(df_cleaned)
    holdout_idx = int(total_len * 0.9)
    test_idx = int(total_len * 0.7)
    
    X_train = X.iloc[:test_idx]
    y_train = y.iloc[:test_idx]
    
    X_test = X.iloc[test_idx:holdout_idx]
    y_test = y.iloc[test_idx:holdout_idx]
    
    X_holdout = X.iloc[holdout_idx:]
    y_holdout = y.iloc[holdout_idx:]
    
    # Drop do 'step' após o split para não ser feature (já temos 'hour')
    X_train = X_train.drop(columns=['step'])
    X_test = X_test.drop(columns=['step'])
    X_holdout = X_holdout.drop(columns=['step'])
    
    return X_train, X_test, y_train, y_test, X_holdout, y_holdout

def save_processed_data(X_train, X_test, y_train, y_test, X_holdout, y_holdout):
    base_dir = Path(__file__).resolve().parent.parent
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Salvar todos os conjuntos para garantir consistência no notebook/SHAP
    X_train.to_csv(processed_dir / "X_train.csv", index=False)
    X_test.to_csv(processed_dir / "X_test.csv", index=False)
    y_train.to_csv(processed_dir / "y_train.csv", index=False)
    y_test.to_csv(processed_dir / "y_test.csv", index=False)
    
    holdout_df = X_holdout.copy()
    holdout_df['isFraud'] = y_holdout
    holdout_df.to_csv(processed_dir / "holdout_data.csv", index=False)
    
    print(f"\nDados processados (com Engenharia de Features) salvos em: {processed_dir}")

if __name__ == "__main__":
    from data_loader import load_and_verify
    
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / "data" / "raw" / "arquivo.csv"
    
    df = load_and_verify(str(data_path))
    
    if df is not None:
        X_train, X_test, y_train, y_test, X_holdout, y_holdout = preprocess_and_split(df)
        save_processed_data(X_train, X_test, y_train, y_test, X_holdout, y_holdout)