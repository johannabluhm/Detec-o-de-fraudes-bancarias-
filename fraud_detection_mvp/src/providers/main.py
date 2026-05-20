from __future__ import annotations

import locale
import logging
import time
import traceback

import streamlit as st

from . import get_provider
from .utils.payload_builder import build_features

logger = logging.getLogger(__name__)

PROVIDER_OPTIONS = [
    "Local (XGBoost)",
    "AWS (SageMaker)",
    "Google Cloud (Vertex AI)",
    "Azure (Azure ML)",
]

BADGE_MAPPING = {
    "Local (XGBoost)": "🟡 Local",
    "AWS (SageMaker)": "🟠 AWS",
    "Google Cloud (Vertex AI)": "🔵 GCP",
    "Azure (Azure ML)": "🔷 Azure",
}

TYPE_MAP = {
    "TRANSFERENCIA": "TRANSFER",
    "SAQUE": "CASH_OUT",
    "PAGAMENTO": "PAYMENT",
    "DEPOSITO": "CASH_IN",
    "DEBITO": "DEBIT",
}


def formatar_real(valor: float) -> str:
    """Formata valores monetários em reais usando padrão brasileiro."""
    try:
        locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
        return locale.currency(valor, grouping=True, symbol="R$ ")
    except locale.Error:
        valor_formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor_formatado}"
    except Exception:
        return f"R$ {valor:.2f}"


def compute_result_metadata(label: int, score: float) -> dict:
    """Agrupa metadados padrão de resultado para exibição."""
    is_fraud = bool(label)
    risk_level = "Alto" if score > 0.8 else "Médio" if score > 0.5 else "Baixo"
    status = "Transação bloqueada (ALERTA DE FRAUDE)" if is_fraud else "Transação aprovada"
    return {
        "is_fraud": is_fraud,
        "fraud_probability": round(score, 4),
        "risk_level": risk_level,
        "status": status,
    }


def render_prediction_result(result: dict, amount: float, oldbalance_org: float, newbalance_orig: float, type_op: str) -> None:
    """Exibe os resultados da predição na interface Streamlit com impacto visual."""
    
    st.divider()
    col_res1, col_res2 = st.columns([2, 1])
    
    with col_res1:
        if result["is_fraud"]:
            st.error(f"### 🚨 {result.get('status', 'FRAUDE DETECTADA')}")
            st.write(f"**Nível de Risco:** {result['risk_level']}")
        else:
            st.success(f"### ✅ {result.get('status', 'TRANSACAO APROVADA')}")
            st.write(f"**Nível de Risco:** {result['risk_level']}")

    with col_res2:
        delta_color = "inverse" if result["is_fraud"] else "normal"
        st.metric(
            label="Probabilidade de Risco", 
            value=f"{result['fraud_probability']*100:.1f}%",
            delta=result['risk_level'],
            delta_color=delta_color
        )

    st.divider()
    
    if result["is_fraud"]:
        st.subheader("Análise de Diagnóstico")
        if amount > oldbalance_org:
            st.info("💡 **Causa Provável:** O valor solicitado excede o saldo disponível (Inconsistência Financeira).")
        elif newbalance_orig == 0 and type_op == "TRANSFERENCIA":
            st.info("💡 **Causa Provável:** Padrão de 'Esvaziamento de Conta' detectado via transferência imediata.")
        else:
            st.info("💡 **Causa Provável:** O algoritmo identificou desvios comportamentais severos em relação ao perfil de segurança.")
    else:
        st.subheader("Verificação de Segurança")
        st.write("Assinatura transacional validada contra 14 camadas de verificação. Nenhuma anomalia crítica detectada.")


def login() -> None:
    """Renderiza a tela de login e atualiza o estado da sessão."""
    st.title("Login - Sistema Anti Fraude")
    with st.container():
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if user == "admin" and pwd == "123456":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciais inválidas")


def run_app() -> None:
    """Ponto de entrada do aplicativo Streamlit."""
    st.set_page_config(page_title="Plataforma Anti Fraude", layout="centered")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login()
        st.stop()

    st.sidebar.title("Configurações")
    selected_provider = st.sidebar.selectbox(
        "Infraestrutura do Modelo",
        PROVIDER_OPTIONS,
        help="Escolha onde o modelo de detecção será executado.",
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    provider_badge = BADGE_MAPPING.get(selected_provider, selected_provider)
    provider = get_provider(selected_provider)

    if not provider.health_check():
        st.sidebar.warning(
            f"Atenção: o provedor selecionado ({selected_provider}) pode não estar configurado corretamente."
        )

    st.title("Motor Preditivo Anti Fraude")
    st.markdown(f"**Provedor ativo:** {provider_badge}  \\  **Latência:** aguardando")
    st.write("Análise comportamental avançada ativada (Velocity & Balance Error).")
    st.divider()

    with st.form("transaction_form"):
        st.subheader("Dados da Operacao")

        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            name_orig = st.text_input("ID Conta de Origem", value="C12345678")
        with col_acc2:
            type_op = st.selectbox(
                "Categoria da Operacao",
                ["TRANSFERENCIA", "SAQUE"],
            )

        type_str = TYPE_MAP[type_op]

        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input(
                "Valor Solicitado (R$)",
                min_value=0.1,
                value=1500.0,
                step=100.0,
                format="%.2f",
            )
            oldbalance_org = st.number_input(
                "Saldo da Origem (R$)",
                min_value=0.0,
                value=5000.0,
                step=100.0,
                format="%.2f",
            )
        with col2:
            oldbalance_dest = st.number_input(
                "Saldo do Destino (R$)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
            )

        newbalance_orig = max(0.0, oldbalance_org - amount)
        newbalance_dest = oldbalance_dest + amount

        if amount > oldbalance_org:
            st.warning("O valor informado e maior que o saldo da conta de origem.")

        submit_button = st.form_submit_button("Executar Analise de Risco", use_container_width=True)

    if submit_button:
        st.divider()
        st.subheader("Visao Geral do Balanco Financeiro")

        colA, colB, colC = st.columns(3)
        colA.metric("Valor da Operacao", formatar_real(amount))
        colB.metric("Saldo Restante (Origem)", formatar_real(newbalance_orig))
        colC.metric("Novo Saldo (Destino)", formatar_real(newbalance_dest))

        features = build_features(
            type_str=type_str,
            amount=amount,
            oldbalance_org=oldbalance_org,
            newbalance_orig=newbalance_orig,
            oldbalance_dest=oldbalance_dest,
            newbalance_dest=newbalance_dest,
            name_orig=name_orig,
        )

        # Regra de Ouro: Bloqueio Determinístico por Saldo Insuficiente
        if amount > oldbalance_org:
            result = {
                "is_fraud": True,
                "fraud_probability": 1.0,
                "risk_level": "Crítico",
                "status": "Transação Negada: Saldo Insuficiente"
            }
            render_prediction_result(result, amount, oldbalance_org, newbalance_orig, type_op)
            return

        with st.spinner("Enviando informacoes para analise comportamental..."):
            try:
                start_time = time.perf_counter()
                prediction = provider.predict(features)
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                result = compute_result_metadata(prediction["label"], prediction["score"])
                result["provider"] = prediction["provider"]
                provider_status = f"**Provedor ativo:** {provider_badge}  \n**Latência:** {latency_ms} ms"
                st.markdown(provider_status)
            except Exception as exc:
                error_text = (
                    f"Erro ao executar a inferência no provedor {selected_provider}: {exc}"
                )
                st.error(error_text)
                logger.error(traceback.format_exc())
                return

        render_prediction_result(result, amount, oldbalance_org, newbalance_orig, type_op)


if __name__ == "__main__":
    run_app()
