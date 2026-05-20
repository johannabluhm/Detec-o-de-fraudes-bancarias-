import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import learning_curve
from sklearn.metrics import precision_recall_curve, auc
from xgboost import XGBClassifier
import shap
from pathlib import Path
import pickle

def plot_learning_curve(estimator, X, y):
    print("Gerando curva de aprendizado...")
    train_sizes, train_scores, test_scores = learning_curve(
        estimator, X, y, cv=3, n_jobs=-1, 
        train_sizes=np.linspace(0.1, 1.0, 5),
        scoring='f1'
    )
    
    train_mean = np.mean(train_scores, axis=1)
    test_mean = np.mean(test_scores, axis=1)

    plt.figure(figsize=(10, 6))
    plt.plot(train_sizes, train_mean, label='Treino')
    plt.plot(train_sizes, test_mean, label='Validação')
    plt.title('Curva de Aprendizado (F1-Score)')
    plt.xlabel('Tamanho do Conjunto de Treinamento')
    plt.ylabel('F1-Score')
    plt.legend()
    plt.grid(True)
    
    save_path = Path("reports/figures/learning_curve.png")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path)
    plt.close()
    print(f"Curva salva em: {save_path}")

def plot_precision_recall(model, X_test, y_test):
    print("Gerando curva Precision-Recall...")
    y_probs = model.predict_proba(X_test)[:, 1]
    precision, recall, _ = precision_recall_curve(y_test, y_probs)
    pr_auc = auc(recall, precision)

    plt.figure(figsize=(10, 6))
    plt.plot(recall, precision, label=f'AUC-PR = {pr_auc:.4f}')
    plt.title('Curva Precision-Recall (Padrão Ouro para Fraude)')
    plt.xlabel('Recall (Taxa de Fraudes Detectadas)')
    plt.ylabel('Precision (Confiança no Bloqueio)')
    plt.legend()
    plt.grid(True)
    
    save_path = Path("reports/figures/precision_recall_curve.png")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path)
    plt.close()
    print(f"PR Curve salva em: {save_path}")

def explain_model(model, X):
    print("Gerando explicações SHAP...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    plt.figure()
    shap.summary_plot(shap_values, X, show=False)
    
    save_path = Path("reports/figures/shap_summary.png")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path)
    plt.close()
    print(f"SHAP summary salvo em: {save_path}")

if __name__ == "__main__":
    from data_loader import load_and_verify
    from preprocessing import preprocess_and_split
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_PATH = BASE_DIR / "data" / "raw" / "arquivo.csv"
    
    df = load_and_verify(str(DATA_PATH))
    if df is not None:
        # Amostragem temporal para diagnóstico mantendo a linha do tempo
        if len(df) > 100000:
            df = df.sort_values('step').head(100000)
            
        X_train, X_test, y_train, y_test, _, _ = preprocess_and_split(df)
        
        # Parâmetros atuais
        scale_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1])
        model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            scale_pos_weight=scale_weight,
            tree_method='hist',
            random_state=42
        )
        
        # 1. Curva de Aprendizado
        plot_learning_curve(model, X_train, y_train)
        
        # 2. PR Curve & SHAP
        model.fit(X_train, y_train)
        plot_precision_recall(model, X_test, y_test)
        explain_model(model, X_test)
