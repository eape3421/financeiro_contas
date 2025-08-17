import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Carregar config.yaml
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Inicializar autenticação
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']
)

# Login
name, authentication_status, username = authenticator.login('main')

if authentication_status:
    st.sidebar.success(f"Bem-vindo, {name}!")
    st.title("Sistema Financeiro")
    st.write("Aqui vai o conteúdo do app...")
elif authentication_status is False:
    st.error("Usuário ou senha incorretos")
elif authentication_status is None:
    st.warning("Por favor, insira suas credenciais")

# Logout
authenticator.logout('Sair', 'sidebar')
