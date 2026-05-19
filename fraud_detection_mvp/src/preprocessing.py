import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path

def preprocess_and_split(df):
    # 1. Filtro de Domínio: Fraudes ocorrem apenas em TRANSFER e CASH_OUT
    df = df[df['type'].isin(['TRANSFER', 'CASH_OUT'])].copy()
    
    # 2. Velocity Features (Novos Atributos Comportamentais)
    # Contagem de transações por conta de origem (indica disparada de uso)
    df['trans_count_orig'] = df.groupby('nameOrig')['step'].transform('count')
    
    # 3. Engenharia de Atributos (Domain Knowledge)
    df['errorBalanceOrig'] = df['newbalanceOrig'] + df['amount'] - df['oldbalanceOrg']
    df['errorBalanceDest'] = df['oldbalanceDest'] + df['amount'] - df['newbalanceDest']
    df['hour'] = df['step'] % 24
    
    # 4. Remoção de colunas com risco de vazamento ou irrelevantes
    # nameOrig usado para velocity, agora pode cair. step usado para split cronológico.
    cols_to_drop = ['nameOrig', 'nameDest', 'isFlaggedFraud']
    df_cleaned = df.drop(columns=cols_to_drop)
    
    # Mapeamento fixo
    type_map = {'CASH_OUT': 1, 'TRANSFER': 4}
    df_cleaned['type'] = df_cleaned['type'].map(type_map)
    df_cleaned['type'] = df_cleaned['type'].fillna(-1)
    
    # 5. Validação Temporal (Split Cronológico)
    # Não usamos shuffle. O passado treina o futuro.
    df_cleaned = df_cleaned.sort_values('step')
    X = df_cleaned.drop('isFraud', axis=1)
    y = df_cleaned['isFraud']
    
    # Divisão manual para manter a ordem temporal (Holdout = últimos 10% do tempo)
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
    
    print(f"Features finais: {list(X_train.columns)}")
    print(f"Split Temporal: Treino (até {test_idx}), Teste ({test_idx} a {holdout_idx}), Holdout (pós {holdout_idx})")
    
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