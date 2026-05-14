import locale

import requests
import streamlit as st

import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/predict")
TYPE_MAP = {
    "TRANSFERENCIA": 4,
    "SAQUE": 1,
    "PAGAMENTO": 3,
    "DEPOSITO": 0,
    "DEBITO": 2,
}

st.set_page_config(page_title="Plataforma Anti Fraude", layout="centered")

# Gerenciamento de Sessão de Login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("Login - Sistema Anti Fraude")
    with st.container():
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if user == "admin" and pwd == "hackathon":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciais inválidas")

if not st.session_state.logged_in:
    login()
    st.stop()

# Configurações na Barra Lateral
st.sidebar.title("Configurações")
infra_choice = st.sidebar.selectbox(
    "Infraestrutura do Modelo",
    ["Local (XGBoost)", "AWS (SageMaker)"],
    help="Escolha onde o modelo de detecção será executado."
)
infra_flag = "AWS" if "AWS" in infra_choice else "Local"

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

def formatar_real(valor: float) -> str:
    try:
        locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
        return locale.currency(valor, grouping=True, symbol="R$ ")
    except locale.Error:
        valor_formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor_formatado}"
    except Exception:
        return f"R$ {valor:.2f}"


def build_payload(type_code: int, amount: float, oldbalance_org: float, newbalance_orig: float, oldbalance_dest: float, newbalance_dest: float, infra: str) -> dict:
    return {
        "transaction": {
            "step": 1,
            "type": type_code,
            "amount": amount,
            "oldbalanceOrg": oldbalance_org,
            "newbalanceOrig": newbalance_orig,
            "oldbalanceDest": oldbalance_dest,
            "newbalanceDest": newbalance_dest,
        },
        "infrastructure": infra
    }


def request_prediction(payload: dict) -> tuple[dict | None, str | None]:
    try:
        response = requests.post(API_URL, json=payload, timeout=8)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.Timeout:
        return None, "A solicitacao excedeu o tempo limite. Tente novamente mais tarde."
    except requests.exceptions.ConnectionError:
        return None, "Nao foi possivel conectar ao servidor. Verifique se a API FastAPI esta rodando."
    except requests.exceptions.RequestException as exc:
        if exc.response is not None:
            try:
                detail = exc.response.json().get("detail", str(exc))
                return None, f"Erro da API: {detail}"
            except:
                pass
        return None, f"Erro de comunicacao com a API: {exc}"
    except ValueError:
        return None, "Resposta invalida do servidor."


def render_prediction_result(result: dict, amount: float, oldbalance_org: float, newbalance_orig: float, type_op: str) -> None:
    if result["is_fraud"]:
        st.error(f"TRANSACAO BLOQUEADA - {result.get('status', 'FRAUDE DETECTADA')}")
        st.warning(f"Nivel de Risco: {result['risk_level']} (Probabilidade: {result['fraud_probability']*100:.1f}%)")

        if amount > oldbalance_org:
            st.write("Diagnostico do Sistema: O valor solicitado excede a capacidade financeira da conta de origem.")
        elif newbalance_orig == 0 and type_op == "TRANSFERENCIA":
            st.write("Diagnostico do Sistema: Padrao agressivo detectado. Esvaziamento total de conta via transferencia imediata.")
        else:
            st.write("Diagnostico do Sistema: O algoritmo identificou desvios severos em relacao ao historico de seguranca.")
    else:
        st.success(f"TRANSACAO LIBERADA - {result.get('status', 'APROVADA')}")
        st.write("Diagnostico do Sistema: Assinatura transacional validada e considerada segura.")


st.title("Motor Preditivo Anti Fraude")
st.info(f"Executando via: **{infra_choice}**")
st.write("Insira os dados da transacao para analise em tempo real pela Inteligencia Artificial.")
st.divider()

with st.form("transaction_form"):
    st.subheader("Dados da Operacao")
    type_op = st.selectbox(
        "Categoria da Operacao",
        ["TRANSFERENCIA", "SAQUE", "PAGAMENTO", "DEPOSITO", "DEBITO"],
    )

    type_code = TYPE_MAP[type_op]

    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Valor Solicitado (R$)", min_value=0.1, value=1500.0, step=100.0, format="%.2f")
        oldbalance_org = st.number_input("Saldo da Origem (R$)", min_value=0.0, value=5000.0, step=100.0, format="%.2f")
    with col2:
        oldbalance_dest = st.number_input("Saldo do Destino (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f")

    newbalance_orig = max(0.0, oldbalance_org - amount)
    newbalance_dest = oldbalance_dest + amount

    if amount > oldbalance_org:
        st.warning("O valor informado e maior que o saldo da conta de origem. Verifique se os dados estao corretos.")

    submit_button = st.form_submit_button("Executar Analise de Risco", use_container_width=True)

if submit_button:
    st.divider()
    st.subheader("Visao Geral do Balanco Financeiro")

    colA, colB, colC = st.columns(3)
    colA.metric("Valor da Operacao", formatar_real(amount))
    colB.metric("Saldo Restante (Origem)", formatar_real(newbalance_orig))
    colC.metric("Novo Saldo (Destino)", formatar_real(newbalance_dest))

    st.divider()
    payload = build_payload(type_code, amount, oldbalance_org, newbalance_orig, oldbalance_dest, newbalance_dest, infra_flag)

    with st.spinner("Enviando informacoes para analise..."):
        result, error_message = request_prediction(payload)

    if error_message:
        st.error(error_message)
    elif result is not None:
        render_prediction_result(result, amount, oldbalance_org, newbalance_orig, type_op)
    else:
        st.error("Ocorreu um erro inesperado ao processar a solicitacao.")