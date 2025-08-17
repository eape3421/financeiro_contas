import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import streamlit_authenticator as stauth

# Configuração da página
st.set_page_config(page_title="Controle Financeiro Pro", layout="wide")

# Usuários e senhas
names = ["Eraldo"]
usernames = ["eraldo"]
passwords = ["senha123"]  # Substitua por sua senha real

# Criptografar senhas
hashed_passwords = stauth.Hasher(passwords).generate()

# Autenticação
authenticator = stauth.Authenticate(
    names,
    usernames,
    hashed_passwords,
    "financeiro_app",
    "abcdef",  # Chave secreta da sessão
    cookie_expiry_days=1
)

# Tela de login
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Bem-vindo, {name}!")

    st.title("📊 Controle Financeiro Profissional")

    # Conexão com banco de dados
    conn = sqlite3.connect("gastos.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            usuario TEXT,
            data TEXT,
            categoria TEXT,
            valor REAL,
            descricao TEXT
        )
    """)

    # Entrada de dados
    st.subheader("✍️ Adicionar gasto")
    with st.form("formulario"):
        data = st.date_input("Data", value=datetime.today())
        categoria = st.selectbox("Categoria", [
            "Alimentação", "Transporte", "Lazer", "Saúde", "Cartão de crédito",
            "Cartão de débito", "PIX", "Receita", "Outros"
        ])
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao = st.text_input("Descrição")
        enviar = st.form_submit_button("Salvar")
        if enviar:
            cursor.execute("INSERT INTO gastos VALUES (?, ?, ?, ?, ?)",
                           (username, str(data), categoria, valor, descricao))
            conn.commit()
            st.success("Gasto salvo com sucesso!")

    # Visualização
    st.subheader("📈 Visualização de gastos")
    df = pd.read_sql_query("SELECT * FROM gastos WHERE usuario=?", conn, params=(username,))
    df["data"] = pd.to_datetime(df["data"])

    if not df.empty:
        periodo = st.date_input("Filtrar por período", [df["data"].min(), df["data"].max()])
        df_filtrado = df[(df["data"] >= pd.to_datetime(periodo[0])) & (df["data"] <= pd.to_datetime(periodo[1]))]

        st.dataframe(df_filtrado)

        # KPIs
        total_receita = df_filtrado[df_filtrado["categoria"] == "Receita"]["valor"].sum()
        total_despesa = df_filtrado[df_filtrado["categoria"] != "Receita"]["valor"].sum()
        saldo = total_receita - total_despesa
        economia_percentual = (saldo / total_receita * 100) if total_receita > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Receita", f"R$ {total_receita:.2f}")
        col2.metric("📉 Despesa", f"R$ {total_despesa:.2f}")
        col3.metric("📊 Saldo", f"R$ {saldo:.2f}")
        col4.metric("📈 Economia (%)", f"{economia_percentual:.1f}%")

        # Meta de economia
        st.subheader("🎯 Meta de economia mensal")
        meta = st.number_input("Defina sua meta (R$)", min_value=0.0, format="%.2f")
        if meta > 0:
            if saldo >= meta:
                st.success(f"✅ Meta atingida! Você economizou R$ {saldo:.2f}")
            else:
                st.error(f"⚠️ Meta não atingida. Faltam R$ {meta - saldo:.2f}")

        # Gráficos
        st.subheader("📊 Gastos por categoria")
        df_despesas = df_filtrado[df_filtrado["categoria"] != "Receita"]
        if not df_despesas.empty:
            fig_pie = px.pie(df_despesas, names="categoria", values="valor", title="Distribuição por categoria")
            st.plotly_chart(fig_pie, use_container_width=True)

            fig_bar = px.bar(df_despesas.groupby("categoria")["valor"].sum().reset_index(),
                             x="categoria", y="valor", title="Total por categoria")
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para visualização.")

    conn.close()

elif authentication_status is False:
    st.error("Usuário ou senha incorretos.")
elif authentication_status is None:
    st.warning("Por favor, insira suas credenciais.")
