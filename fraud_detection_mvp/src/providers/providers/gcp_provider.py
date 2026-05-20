from __future__ import annotations

from typing import Optional

from .base import BaseProvider


class GCPProvider(BaseProvider):
    """Provedor Vertex AI para inferência via endpoint do GCP."""

    def __init__(
        self,
        project_id: str,
        region: str,
        endpoint_id: str,
        credentials_path: Optional[str] = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.project_id = project_id
        self.region = region
        self.endpoint_id = endpoint_id
        self.credentials_path = credentials_path
        self.timeout_seconds = timeout_seconds
        self.endpoint = None

    def connect(self) -> None:
        """Inicializa o cliente Vertex AI e prepara o endpoint de inferência."""
        if self.endpoint is not None:
            return

        try:
            from google.cloud import aiplatform
            from google.oauth2 import service_account
        except ImportError as exc:
            raise ImportError(
                "Bibliotecas do Google Cloud não estão instaladas. "
                "Instale com: pip install google-cloud-aiplatform google-auth"
            ) from exc

        credentials = None
        if self.credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )

        aiplatform.init(
            project=self.project_id,
            location=self.region,
            credentials=credentials,
        )

        endpoint_name = self._build_endpoint_resource_name()
        self.endpoint = aiplatform.Endpoint(endpoint_name)

    def _build_endpoint_resource_name(self) -> str:
        return f"projects/{self.project_id}/locations/{self.region}/endpoints/{self.endpoint_id}"

    def predict(self, features: dict) -> dict:
        """Faz a chamada ao endpoint Vertex AI e retorna resultado padronizado."""
        try:
            from google.api_core.exceptions import GoogleAPIError
        except ImportError as exc:
            raise ImportError(
                "Bibliotecas do Google Cloud não estão instaladas. "
                "Instale com: pip install google-cloud-aiplatform google-auth"
            ) from exc

        self.connect()

        if self.endpoint is None:
            raise RuntimeError("Endpoint Vertex AI não inicializado.")

        try:
            prediction_response = self.endpoint.predict(instances=[features])
            predictions = (
                prediction_response.predictions
                if hasattr(prediction_response, "predictions")
                else prediction_response
            )
        except GoogleAPIError as exc:
            raise RuntimeError(f"Vertex AI error: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Erro inesperado na inferência GCP: {exc}") from exc

        if not predictions:
            raise RuntimeError("Resposta vazia do Vertex AI.")

        raw_prediction = predictions[0]
        label = int(
            raw_prediction.get("prediction")
            if isinstance(raw_prediction, dict) and raw_prediction.get("prediction") is not None
            else raw_prediction
        )
        score = float(
            raw_prediction.get("probability")
            if isinstance(raw_prediction, dict) and raw_prediction.get("probability") is not None
            else raw_prediction.get("score", 0.0)
            if isinstance(raw_prediction, dict)
            else 0.0
        )

        return {
            "label": label,
            "score": score,
            "provider": "gcp",
        }

    def health_check(self) -> bool:
        """Verifica se o endpoint Vertex AI está inicializado e acessível."""
        try:
            self.connect()
            return self.endpoint is not None
        except Exception:
            return False
