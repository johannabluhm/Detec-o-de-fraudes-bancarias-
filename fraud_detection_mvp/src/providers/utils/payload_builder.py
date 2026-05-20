from __future__ import annotations


def build_features(
    type_str: str,
    amount: float,
    oldbalance_org: float,
    newbalance_orig: float,
    oldbalance_dest: float,
    newbalance_dest: float,
    name_orig: str,
    step: int = 1,
) -> dict:
    """Constrói o dicionário de features padrão para inferência."""
    return {
        "step": step,
        "type": type_str,
        "amount": amount,
        "oldbalanceOrg": oldbalance_org,
        "newbalanceOrig": newbalance_orig,
        "oldbalanceDest": oldbalance_dest,
        "newbalanceDest": newbalance_dest,
        "nameOrig": name_orig,
    }


def build_request_payload(features: dict, provider_name: str) -> dict:
    """Serializa o payload de predição para provedores que exigem wrapper JSON."""
    return {
        "transaction": features,
        "infrastructure": provider_name,
    }
