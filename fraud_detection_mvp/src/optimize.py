import optuna
import xgboost as xgb
from sklearn.metrics import f1_score
from pathlib import Path
from data_loader import load_and_verify
from preprocessing import preprocess_and_split
import pickle

def objective(trial, X_train, y_train, X_test, y_test):
    # Proporção para desbalanceamento
    scale_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1])
    
    param = {
        'verbosity': 0,
        'objective': 'binary:logistic',
        'tree_method': 'hist',
        'random_state': 42,
        'scale_pos_weight': scale_weight,
        # Hiperparâmetros para otimizar
        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'gamma': trial.suggest_float('gamma', 1e-8, 1.0, log=True),
    }

    model = xgb.XGBClassifier(**param)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    score = f1_score(y_test, preds)
    return score

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_PATH = BASE_DIR / "data" / "raw" / "arquivo.csv"
    
    df = load_and_verify(str(DATA_PATH))
    if df is not None:
        # Amostragem para otimização rápida
        if len(df) > 50000:
            df = df.sample(50000, random_state=42)
            
        X_train, X_test, y_train, y_test, _, _ = preprocess_and_split(df)
        
        print("Iniciando otimização com Optuna...")
        study = optuna.create_study(direction='maximize')
        study.optimize(lambda trial: objective(trial, X_train, y_train, X_test, y_test), n_trials=20)
        
        print("\nMelhores hiperparâmetros:")
        print(study.best_params)
        print(f"Melhor F1-Score: {study.best_value:.4f}")
        
        # Salvar melhores parâmetros
        best_params_path = BASE_DIR / "models" / "best_params.pkl"
        best_params_path.parent.mkdir(exist_ok=True)
        with open(best_params_path, 'wb') as f:
            pickle.dump(study.best_params, f)
        print(f"Parâmetros salvos em: {best_params_path}")
