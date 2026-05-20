from __future__ import annotations

from ..config import (
    AZURE_CONFIG,
    AWS_CONFIG,
    GCP_CONFIG,
    LOCAL_CONFIG,
    TIMEOUT_SECONDS,
)
from .base import BaseProvider


def get_provider(name: str) -> BaseProvider:
    """Retorna a instância do provedor correto com base no nome selecionado."""
    if name == "Local (XGBoost)":
        from .local_provider import LocalProvider

        return LocalProvider(
            model_path=LOCAL_CONFIG["model_path"],
            timeout_seconds=TIMEOUT_SECONDS,
        )

    if name == "AWS (SageMaker)":
        from .aws_provider import AWSProvider

        return AWSProvider(
            region=AWS_CONFIG["region"],
            endpoint_name=AWS_CONFIG["endpoint_name"],
            access_key=AWS_CONFIG["access_key"],
            secret_key=AWS_CONFIG["secret_key"],
            timeout_seconds=TIMEOUT_SECONDS,
        )

    if name == "Google Cloud (Vertex AI)":
        from .gcp_provider import GCPProvider

        return GCPProvider(
            project_id=GCP_CONFIG["project_id"],
            region=GCP_CONFIG["region"],
            endpoint_id=GCP_CONFIG["endpoint_id"],
            credentials_path=GCP_CONFIG["credentials_path"],
            timeout_seconds=TIMEOUT_SECONDS,
        )

    if name == "Azure (Azure ML)":
        from .azure_provider import AzureProvider

        return AzureProvider(
            subscription_id=AZURE_CONFIG["subscription_id"],
            resource_group=AZURE_CONFIG["resource_group"],
            workspace_name=AZURE_CONFIG["workspace_name"],
            endpoint_name=AZURE_CONFIG["endpoint_name"],
            deployment_name=AZURE_CONFIG["deployment_name"],
            timeout_seconds=TIMEOUT_SECONDS,
        )

    raise ValueError(
        f"Provedor '{name}' não suportado. Escolha entre: Local (XGBoost), AWS (SageMaker), Google Cloud (Vertex AI), Azure (Azure ML)"
    )
