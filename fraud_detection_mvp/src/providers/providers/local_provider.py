from __future__ import annotations

import pickle
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from .base import BaseProvider


@st.cache_resource
def load_xgboost_model(model_path: Path):
    """Carrega o modelo do disco e mantém em cache do Streamlit."""
    with model_path.open("rb") as model_file:
        return pickle.load(model_file)


class LocalProvider(BaseProvider):
    """Provedor local que executa o modelo XGBoost carregado a partir do disco."""

    def __init__(self, model_path: Optional[str] = None, timeout_seconds: int = 30) -> None:
        self._model_path = Path(model_path) if model_path is not None else None
        self._timeout_seconds = timeout_seconds
        self._model = None

    def connect(self) -> None:
        """Carrega o modelo local XGBoost a partir do disco usando cache."""
        if self._model is not None:
            return

        if self._model_path is None:
            raise FileNotFoundError("Caminho para o modelo local não foi configurado.")

        if not self._model_path.exists():
            raise FileNotFoundError(f"Modelo local não encontrado em {self._model_path}")

        self._model = load_xgboost_model(self._model_path)

    def predict(self, features: dict) -> dict:
        """Realiza predição local com engenharia de features em tempo real."""
        self.connect()

        if self._model is None:
            raise RuntimeError("Modelo local não está carregado.")

        # 1. Recuperar histórico de Velocity do Streamlit Session State
        if "history_db" not in st.session_state:
            st.session_state.history_db = {}
        
        name_orig = features.get("nameOrig", "unknown")
        st.session_state.history_db[name_orig] = st.session_state.history_db.get(name_orig, 0) + 1

        # 2. Engenharia de Atributos (Deve espelhar preprocessing.py e app.py)
        type_map = {
            'CASH_OUT': 1, 
            'TRANSFER': 4, 
            'PAYMENT': 3, 
            'CASH_IN': 0, 
            'DEBIT': 2
        }
        
        raw_type = features.get("type", "PAYMENT").upper()
        mapped_type = type_map.get(raw_type, 3)

        # Cálculo de features derivadas
        amount = float(features.get("amount", 0.0))
        old_org = float(features.get("oldbalanceOrg", 0.0))
        new_org = float(features.get("newbalanceOrig", 0.0))
        old_dest = float(features.get("oldbalanceDest", 0.0))
        new_dest = float(features.get("newbalanceDest", 0.0))
        step = int(features.get("step", 1))

        processed_features = {
            'type': mapped_type,
            'amount': amount,
            'oldbalanceOrg': old_org,
            'newbalanceOrig': new_org,
            'oldbalanceDest': old_dest,
            'newbalanceDest': new_dest,
            'trans_count_orig': st.session_state.history_db[name_orig],
            'errorBalanceOrig': new_org + amount - old_org,
            'errorBalanceDest': old_dest + amount - new_dest,
            'hour': step % 24
        }

        data_frame = pd.DataFrame([processed_features])

        try:
            raw_label = self._model.predict(data_frame)[0]
            raw_score = float(self._model.predict_proba(data_frame)[0][1])
        except (AttributeError, IndexError):
            # Fallback para modelos que não suportam predict_proba ou formato inesperado
            raw_label = int(self._model.predict(data_frame)[0])
            raw_score = 1.0 if raw_label == 1 else 0.0
        except Exception as exc:
            raise RuntimeError(f"Erro ao executar predição local: {exc}") from exc

        return {
            "label": int(raw_label),
            "score": float(raw_score),
            "provider": "local",
        }

    def health_check(self) -> bool:
        """Verifica se o modelo local pode ser carregado e está acessível."""
        try:
            self.connect()
            return self._model is not None
        except Exception:
            return False
