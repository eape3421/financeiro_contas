import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# 🔽 Carregando o arquivo de configuração
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# 🔐 Autenticação
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']
)

# 🟢 Login
name, authentication_status, username = authenticator.login(
    location='main',
    fields={
        'Form name': 'Login',
        'Username': 'Usuário',
        'Password': 'Senha',
        'Login': 'Entrar'
    }
)

# 🎨 Configuração da página
st.set_page_config(page_title="Controle Financeiro Pro", layout="wide")

# 🔄 Verificação de login
if authentication_status:
    st.sidebar.success(f"Bem-vindo, {name}!")

    # 🔘 Menu lateral
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Lançamentos", "Perfil", "Sair"])

    if menu == "Dashboard":
        st.title("📊 Dashboard Financeiro")
        st.write("Aqui você verá gráficos e análises dos seus dados financeiros.")
        # Exemplo de gráfico fictício
        df = pd.DataFrame({
            "Categoria": ["Alimentação", "Transporte", "Lazer"],
            "Valor": [500, 300, 200]
        })
        fig = px.pie(df, names="Categoria", values="Valor", title="Distribuição de Gastos")
        st.plotly_chart(fig)

    elif menu == "Lançamentos":
        st.title("💰 Lançamentos Financeiros")
        st.write("Adicione ou visualize seus lançamentos aqui.")
        # Exemplo de formulário
        with st.form("form_lancamento"):
            categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Outros"])
            valor = st.number_input("Valor", min_value=0.0, step=0.01)
            data = st.date_input("Data", value=datetime.today())
            submit = st.form_submit_button("Salvar")
            if submit:
                st.success("Lançamento salvo com sucesso!")

    elif menu == "Perfil":
        st.title("👤 Perfil do Usuário")
        st.write(f"Nome: {name}")
        st.write(f"Usuário: {username}")
        st.write(f"E-mail: {config['credentials']['usernames'][username]['email']}")

        # 🔁 Redefinir senha
        with st.expander("Redefinir senha"):
            try:
                if authenticator.reset_password(username):
                    st.success("Senha redefinida com sucesso!")
            except Exception as e:
                st.error(f"Erro ao redefinir senha: {e}")

    elif menu == "Sair":
        authenticator.logout("Logout", "sidebar")
        st.warning("Você saiu do sistema.")

elif authentication_status is False:
    st.error("Usuário ou senha incorretos.")
elif authentication_status is None:
    st.warning("Por favor, insira suas credenciais.")
