import streamlit as st
import requests

# Configuração da página
st.set_page_config(page_title="Anti-Fraude MVP", layout="centered")

st.title("🛡️ Sistema de Detecção de Fraudes")
st.write("Insira os dados da transação para análise em tempo real pelo nosso motor de IA.")

# Formulário de entrada de dados
with st.form("transaction_form"):
    type_op = st.selectbox("Tipo de Operação", ["TRANSFERÊNCIA", "SAQUE", "PAGAMENTO", "DEPÓSITO"])
    
    # Mapeamento do tipo para o código numérico que o modelo espera
    type_map = {"TRANSFERÊNCIA": 3, "SAQUE": 1, "PAGAMENTO": 2, "DEPÓSITO": 0}
    type_code = type_map[type_op]

    amount = st.number_input("Valor da Transação (R$)", min_value=0.1, value=1500.0)
    oldbalanceOrg = st.number_input("Saldo Atual da Origem (R$)", min_value=0.0, value=5000.0)
    
    # Calculando o novo saldo automaticamente para facilitar a demo
    newbalanceOrig = st.number_input("Novo Saldo da Origem (R$)", value=max(0.0, oldbalanceOrg - amount))
    
    oldbalanceDest = st.number_input("Saldo Atual do Destino (R$)", min_value=0.0, value=0.0)
    newbalanceDest = st.number_input("Novo Saldo do Destino (R$)", value=oldbalanceDest + amount)

    submit_button = st.form_submit_button("Analisar Transação")

# Ação após clicar no botão
if submit_button:
    # Montando o payload para a API
    payload = {
        "step": 1,
        "type": type_code,
        "amount": amount,
        "oldbalanceOrg": oldbalanceOrg,
        "newbalanceOrig": newbalanceOrig,
        "oldbalanceDest": oldbalanceDest,
        "newbalanceDest": newbalanceDest
    }

    try:
        # Enviando para a nossa API FastAPI
        # Certifique-se de que o uvicorn esteja rodando em outro terminal!
        response = requests.post("http://127.0.0.1:8000/predict", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            st.divider()
            
            # Lógica de exibição visual baseada no retorno da API
            if result["is_fraud"]:
                st.error("🚨 **TRANSAÇÃO BLOQUEADA (FRAUDE DETECTADA)**")
                st.write(f"**Risco:** {result['risk_level']} (Probabilidade: {result['fraud_probability']*100:.1f}%)")
                
                # Explicação de negócio (Explicabilidade)
                if amount > oldbalanceOrg:
                    st.warning("Explicação: Bloqueado porque o valor solicitado excede o saldo da conta de origem.")
                elif newbalanceOrig == 0 and type_op == "TRANSFERÊNCIA":
                    st.warning("Explicação: Padrão de alto risco - Conta de origem esvaziada em transferência imediata.")
                else:
                    st.warning("Explicação: Comportamento transacional anômalo detectado pelo modelo histórico.")
                    
            else:
                st.success("✅ **TRANSAÇÃO APROVADA**")
                st.write(f"**Risco:** {result['risk_level']} (Probabilidade: {result['fraud_probability']*100:.1f}%)")
                st.info("Explicação: Padrão comportamental dentro da normalidade estatística.")
                
        else:
            st.error(f"Erro na validação dos dados: {response.text}")
            
    except requests.exceptions.ConnectionError:
        st.error("Erro de conexão. A API do modelo está rodando? (Execute: uvicorn src.app:app)")