import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd

# Carregar configurações de autenticação
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# Login
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status is False:
    st.error('Usuário ou senha incorretos')
elif authentication_status is None:
    st.warning('Por favor, insira seu usuário e senha')
elif authentication_status:
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.title(f'Bem-vindo, {name}!')

    st.title('📊 Controle Financeiro')

    # Upload de arquivo
    uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.success("Arquivo carregado com sucesso!")
        st.dataframe(df)

        # Exibir estatísticas básicas
        if 'Valor' in df.columns:
            st.subheader("Resumo dos Valores")
            st.metric("Total", f"R$ {df['Valor'].sum():,.2f}")
            st.metric("Média", f"R$ {df['Valor'].mean():,.2f}")
            st.metric("Máximo", f"R$ {df['Valor'].max():,.2f}")
            st.metric("Mínimo", f"R$ {df['Valor'].min():,.2f}")
        else:
            st.warning("Coluna 'Valor' não encontrada no arquivo.")
