from __future__ import annotations

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Classe base para provedores de inferência de fraude."""

    @abstractmethod
    def connect(self) -> None:
        """Autentica e inicializa o cliente do provedor."""

    @abstractmethod
    def predict(self, features: dict) -> dict:
        """Envia features e retorna um dicionário padronizado.

        Retorna:
            {'label': int, 'score': float, 'provider': str}
        """

    @abstractmethod
    def health_check(self) -> bool:
        """Verifica se o endpoint do provedor está disponível."""
