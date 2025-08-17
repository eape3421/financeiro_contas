import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import plotly.express as px
from io import BytesIO

# Carregar configurações de autenticação
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)


# Login
login_result = authenticator.login(location='main')

if login_result is not None and isinstance(login_result, tuple) and len(login_result) == 3:
    name, authentication_status, username = login_result

    if authentication_status is False:
        st.error('Usuário ou senha incorretos')
    elif authentication_status is None:
        st.warning('Por favor, insira seu usuário e senha')
    elif authentication_status:
        authenticator.logout('Logout', 'sidebar')
        st.sidebar.title(f'Bem-vindo, {name}!')
        st.title('📊 Controle Financeiro')

        # (continuação do seu código)
else:
    st.error("Erro ao autenticar. Verifique o config.yaml.")


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
        try:
            df = pd.read_excel(uploaded_file)
            st.success("Arquivo carregado com sucesso!")
            st.dataframe(df)

            # Filtros por data
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'])
                data_inicio = st.date_input("Data inicial", df['Data'].min())
                data_fim = st.date_input("Data final", df['Data'].max())
                df = df[(df['Data'] >= pd.to_datetime(data_inicio)) & (df['Data'] <= pd.to_datetime(data_fim))]

            # Estatísticas
            if 'Valor' in df.columns:
                st.subheader("Resumo dos Valores")
                st.metric("Total", f"R$ {df['Valor'].sum():,.2f}")
                st.metric("Média", f"R$ {df['Valor'].mean():,.2f}")
                st.metric("Máximo", f"R$ {df['Valor'].max():,.2f}")
                st.metric("Mínimo", f"R$ {df['Valor'].min():,.2f}")

                # Gráfico interativo
                if 'Data' in df.columns:
                    fig = px.line(df, x='Data', y='Valor', title='Evolução dos Valores')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Coluna 'Valor' não encontrada no arquivo.")

            # Exportar dados filtrados
            def to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Dados')
                return output.getvalue()

            excel_data = to_excel(df)
            st.download_button(
                label="📥 Baixar dados filtrados",
                data=excel_data,
                file_name="dados_filtrados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
