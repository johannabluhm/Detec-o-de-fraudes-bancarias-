from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "xgboost_fraud_model.pkl"

TIMEOUT_SECONDS = int(os.getenv("PREDICTION_TIMEOUT", "30"))

LOCAL_CONFIG = {
    "model_path": os.getenv("LOCAL_MODEL_PATH", str(MODEL_PATH))
}

AWS_CONFIG = {
    "region": os.getenv("AWS_REGION", "us-east-1"),
    "endpoint_name": os.getenv("SAGEMAKER_ENDPOINT_NAME", ""),
    "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
    "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
}

GCP_CONFIG = {
    "project_id": os.getenv("GCP_PROJECT_ID", ""),
    "region": os.getenv("GCP_REGION", "us-central1"),
    "endpoint_id": os.getenv("GCP_ENDPOINT_ID", ""),
    "credentials_path": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./credentials/gcp_service_account.json"),
}

AZURE_CONFIG = {
    "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID", ""),
    "resource_group": os.getenv("AZURE_RESOURCE_GROUP", ""),
    "workspace_name": os.getenv("AZURE_WORKSPACE_NAME", ""),
    "endpoint_name": os.getenv("AZURE_ENDPOINT_NAME", ""),
    "deployment_name": os.getenv("AZURE_DEPLOYMENT_NAME", ""),
}
