import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import pickle
from pathlib import Path

def train_xgboost(X_train, y_train, X_test=None, y_test=None):
    print("Iniciando o treinamento do modelo XGBoost...")
    
    # Calculando a proporção para lidar com o desbalanceamento
    num_negatives = len(y_train[y_train == 0])
    num_positives = len(y_train[y_train == 1])
    scale_weight = num_negatives / num_positives
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    params_path = BASE_DIR / "models" / "best_params.pkl"
    
    # Configuração Padrão
    params = {
        'n_estimators': 1000, # Aumentado para early stopping agir
        'max_depth': 5,
        'learning_rate': 0.1,
        'scale_pos_weight': scale_weight,
        'tree_method': 'hist',
        'random_state': 42,
        'eval_metric': 'aucpr',
        'early_stopping_rounds': 20 # Definido no construtor
    }
    
    # Sobrescreve com parâmetros otimizados se existirem
    if params_path.exists():
        print(f"Carregando hiperparâmetros otimizados de {params_path}...")
        with open(params_path, 'rb') as f:
            best_params = pickle.load(f)
            params.update(best_params)
    else:
        print("Usando hiperparâmetros padrão.")
    
    model = XGBClassifier(**params)
    
    fit_params = {}
    if X_test is not None and y_test is not None:
        fit_params['eval_set'] = [(X_test, y_test)]
        fit_params['verbose'] = False
        print("Early stopping ativado com conjunto de teste.")

    model.fit(X_train, y_train, **fit_params)
    print("Treinamento concluído.")
    return model

def evaluate_model(model, X_test, y_test):
    print("\n--- Avaliação do Modelo ---")
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Acurácia não é recomendada; usamos o F1-Score e matriz de confusão
    print("\nRelatório de Classificação (Foco no F1-Score da Classe 1):")
    print(classification_report(y_test, y_pred))
    
    # TAREFA 5: Análise de Threshold (Minimização de Perda Total)
    from sklearn.metrics import precision_recall_curve
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_pred_proba)
    
    # Exemplo de cálculo de custo (C_FN=10, C_FP=1)
    # Perda = (10 * Falsos Negativos) + (1 * Falsos Positivos)
    # Nota: Simplificado para demonstração usando métricas PR
    costs = (10 * (1 - recalls[:-1])) + (1 * (1 - precisions[:-1]))
    best_idx = costs.argmin()
    print(f"\nThreshold sugerido para minimizar custo (C_FN=10x): {thresholds[best_idx]:.4f}")
    
    print("\nMatriz de Confusão (no threshold 0.5):")
    print(confusion_matrix(y_test, y_pred))
    
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"\nROC AUC Score: {auc:.4f}")

def save_model(model, file_name="xgboost_fraud_model.pkl"):
    BASE_DIR = Path(__file__).resolve().parent.parent
    # Criando o diretório de modelos, caso não exista
    model_dir = BASE_DIR / "models"
    model_dir.mkdir(exist_ok=True)
    
    file_path = model_dir / file_name
    with open(file_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"Modelo salvo com sucesso em: {file_path}")

if __name__ == "__main__":
    from data_loader import load_and_verify
    from preprocessing import preprocess_and_split
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_PATH = BASE_DIR / "data" / "raw" / "arquivo.csv"
    
    df = load_and_verify(str(DATA_PATH))
    if df is not None:
        X_train, X_test, y_train, y_test, _, _ = preprocess_and_split(df)
        
        # Treinamento e Avaliação
        xgb_model = train_xgboost(X_train, y_train, X_test, y_test)
        evaluate_model(xgb_model, X_test, y_test)
        
        # Salvando para a API do MVP
        save_model(xgb_model)