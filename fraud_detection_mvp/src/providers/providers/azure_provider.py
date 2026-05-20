from __future__ import annotations

from typing import Optional

from .base import BaseProvider


class AzureProvider(BaseProvider):
    """Provedor Azure ML para inferência via endpoint online."""

    def __init__(
        self,
        subscription_id: str,
        resource_group: str,
        workspace_name: str,
        endpoint_name: str,
        deployment_name: str,
        timeout_seconds: int = 30,
    ) -> None:
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.workspace_name = workspace_name
        self.endpoint_name = endpoint_name
        self.deployment_name = deployment_name
        self.timeout_seconds = timeout_seconds
        self.client = None

    def connect(self) -> None:
        """Inicializa o cliente MLClient para Azure Machine Learning."""
        if self.client is not None:
            return

        try:
            from azure.ai.ml import MLClient
            from azure.identity import DefaultAzureCredential
        except ImportError as exc:
            raise ImportError(
                "Bibliotecas do Azure ML não estão instaladas. "
                "Instale com: pip install azure-ai-ml azure-identity"
            ) from exc

        credential = DefaultAzureCredential()
        self.client = MLClient(
            credential=credential,
            subscription_id=self.subscription_id,
            resource_group_name=self.resource_group,
            workspace_name=self.workspace_name,
        )

    def predict(self, features: dict) -> dict:
        """Executa a chamada ao endpoint online do Azure ML e retorna resultado padronizado."""
        try:
            from azure.core.exceptions import HttpResponseError
        except ImportError as exc:
            raise ImportError(
                "Bibliotecas do Azure ML não estão instaladas. "
                "Instale com: pip install azure-ai-ml azure-identity azure-core"
            ) from exc

        self.connect()

        if self.client is None:
            raise RuntimeError("Cliente Azure ML não inicializado.")

        try:
            response = self.client.online_endpoints.invoke(
                name=self.endpoint_name,
                deployment_name=self.deployment_name,
                input_data=[features],
            )
        except HttpResponseError as exc:
            raise RuntimeError(f"Azure ML error: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Erro inesperado na inferência Azure: {exc}") from exc

        if isinstance(response, dict) and response.get("predictions"):
            raw_prediction = response["predictions"][0]
        else:
            raw_prediction = response[0] if isinstance(response, list) and response else response

        if isinstance(raw_prediction, dict):
            label = int(
                raw_prediction.get("prediction")
                if raw_prediction.get("prediction") is not None
                else raw_prediction.get("label", 0)
            )
            score = float(
                raw_prediction.get("probability")
                if raw_prediction.get("probability") is not None
                else raw_prediction.get("score", 0.0)
            )
        else:
            label = int(raw_prediction)
            score = 1.0 if label == 1 else 0.0

        return {
            "label": label,
            "score": score,
            "provider": "azure",
        }

    def health_check(self) -> bool:
        """Verifica se o endpoint Azure ML está configurado e disponível."""
        try:
            self.connect()
            return self.client is not None
        except Exception:
            return False
