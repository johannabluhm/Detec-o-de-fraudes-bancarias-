import pandas as pd
import pickle
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from pathlib import Path

from preprocessing import preprocess_and_split, save_processed_data

REQUIRED_FEATURES = [
    "type",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "trans_count_orig",
    "errorBalanceOrig",
    "errorBalanceDest",
    "hour",
]


def run_holdout_validation():
    print("Iniciando a validacao final com a base Holdout...")
    
    # Configurando os caminhos dinamicamente
    base_dir = Path(__file__).resolve().parent.parent
    model_path = base_dir / "models" / "xgboost_fraud_model.pkl"
    data_path = base_dir / "data" / "processed" / "holdout_data.csv"
    raw_path = base_dir / "data" / "raw" / "arquivo.csv"
    
    # Verificação de segurança para os arquivos
    if not model_path.exists():
        print(f"Erro: Modelo não encontrado em {model_path}")
        return
        
    if not data_path.exists():
        print(f"Erro: Base Holdout não encontrada em {data_path}")
        return

    # 1. Carregando o modelo treinado (Caixa Preta)
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
        
    # 2. Carregando os dados intocados
    df_holdout = pd.read_csv(data_path)
    
    # 3. Separando as variáveis (Features) do alvo (Target)
    X_holdout = df_holdout.drop('isFraud', axis=1)
    y_holdout = df_holdout['isFraud']

    missing_features = [c for c in REQUIRED_FEATURES if c not in X_holdout.columns]
    if missing_features or 'step' in X_holdout.columns:
        print(
            "Holdout dataset não contém as features processadas usadas pelo modelo. "
            "Regenerando a partir dos dados brutos."
        )
        if not raw_path.exists():
            print(f"Erro crítico: não foi possível regenerar o holdout porque o raw file não existe em {raw_path}")
            return

        raw_df = pd.read_csv(raw_path)
        X_train, X_test, y_train, y_test, X_holdout, y_holdout = preprocess_and_split(raw_df)
        save_processed_data(X_train, X_test, y_train, y_test, X_holdout, y_holdout)

        print("Holdout regenerado com sucesso. Iniciando nova avaliação.")

    # 4. Realizando as predições com as features corretas
    y_pred = model.predict(X_holdout)
    y_pred_proba = model.predict_proba(X_holdout)[:, 1]
    
    # 5. Avaliando a performance real do modelo
    print("\nResultados Oficiais da Validacao Cega (Holdout):")
    print("\nRelatorio de Classificacao:")
    print(classification_report(y_holdout, y_pred))
    
    print("\nMatriz de Confusao (Foco nos Falsos Negativos):")
    print(confusion_matrix(y_holdout, y_pred))
    
    auc = roc_auc_score(y_holdout, y_pred_proba)
    print(f"\nROC AUC Score Final: {auc:.4f}")

if __name__ == "__main__":
    run_holdout_validation()