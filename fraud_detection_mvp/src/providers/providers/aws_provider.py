from __future__ import annotations

import json
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from .base import BaseProvider


class AWSProvider(BaseProvider):
    """Provedor AWS SageMaker para inferência via endpoint."""

    def __init__(
        self,
        region: str,
        endpoint_name: str,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.region = region
        self.endpoint_name = endpoint_name
        self.access_key = access_key
        self.secret_key = secret_key
        self.timeout_seconds = timeout_seconds
        self._client = None

    def connect(self) -> None:
        """Inicializa o cliente do SageMaker Runtime com timeout configurável."""
        if self._client is not None:
            return

        session_kwargs = {
            "region_name": self.region,
        }
        if self.access_key and self.secret_key:
            session_kwargs.update(
                {
                    "aws_access_key_id": self.access_key,
                    "aws_secret_access_key": self.secret_key,
                }
            )

        session = boto3.Session(**session_kwargs)
        botocore_config = Config(
            connect_timeout=10,
            read_timeout=self.timeout_seconds,
        )

        self._client = session.client(
            "sagemaker-runtime",
            config=botocore_config,
        )

    def predict(self, features: dict) -> dict:
        """Chama o endpoint do SageMaker e retorna resultado padronizado."""
        self.connect()

        if self._client is None:
            raise RuntimeError("Cliente SageMaker não inicializado.")

        payload = json.dumps({"instances": [features]})

        try:
            response = self._client.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Body=payload,
            )
            body = response["Body"].read().decode("utf-8")
            result = json.loads(body)
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"AWS SageMaker error: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Erro inesperado na inferência AWS: {exc}") from exc

        label = int(result.get("prediction") if result.get("prediction") is not None else 0)
        score = float(result.get("probability") if result.get("probability") is not None else result.get("score", 0.0))

        return {
            "label": label,
            "score": score,
            "provider": "aws",
        }

    def health_check(self) -> bool:
        """Verifica se a configuração do endpoint AWS está disponível."""
        try:
            self.connect()
            return self._client is not None and bool(self.endpoint_name)
        except Exception:
            return False
