import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import hashlib

# Configuração da página
st.set_page_config(page_title="Controle Financeiro Pro", layout="wide")

# Funções de autenticação
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_login(usuario, senha):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT, senha TEXT)")
    cursor.execute("SELECT senha FROM usuarios WHERE usuario=?", (usuario,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado and resultado[0] == hash_password(senha)

def registrar_usuario(usuario, senha):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO usuarios VALUES (?, ?)", (usuario, hash_password(senha)))
    conn.commit()
    conn.close()

# Login
st.sidebar.title("🔐 Login")
opcao = st.sidebar.radio("Acesso", ["Entrar", "Registrar"])
usuario = st.sidebar.text_input("Usuário")
senha = st.sidebar.text_input("Senha", type="password")

if opcao == "Registrar":
    if st.sidebar.button("Criar conta"):
        registrar_usuario(usuario, senha)
        st.sidebar.success("Conta criada com sucesso!")

if opcao == "Entrar":
    if st.sidebar.button("Entrar"):
        if verificar_login(usuario, senha):
            st.sidebar.success("Login realizado!")
            st.session_state["logado"] = True
        else:
            st.sidebar.error("Usuário ou senha inválidos")

# Se logado, mostra o app
if st.session_state.get("logado"):
    st.title("📊 Controle Financeiro Profissional")
    conn = sqlite3.connect("gastos.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            usuario TEXT, data TEXT, categoria TEXT, valor REAL, descricao TEXT
        )
    """)

    # Entrada de dados
    st.subheader("✍️ Adicionar gasto")
    with st.form("formulario"):
        data = st.date_input("Data", value=datetime.today())
        categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Saúde", "Outros"])
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao = st.text_input("Descrição")
        enviar = st.form_submit_button("Salvar")
        if enviar:
            cursor.execute("INSERT INTO gastos VALUES (?, ?, ?, ?, ?)",
                           (usuario, str(data), categoria, valor, descricao))
            conn.commit()
            st.success("Gasto salvo com sucesso!")

    # Visualização
    st.subheader("📈 Visualização de gastos")
    df = pd.read_sql_query("SELECT * FROM gastos WHERE usuario=?", conn, params=(usuario,))
    df["data"] = pd.to_datetime(df["data"])
    periodo = st.date_input("Filtrar por período", [df["data"].min(), df["data"].max()])
    df_filtrado = df[(df["data"] >= pd.to_datetime(periodo[0])) & (df["data"] <= pd.to_datetime(periodo[1]))]

    st.dataframe(df_filtrado)

    # Gráfico por categoria
    if not df_filtrado.empty:
        fig = px.pie(df_filtrado, names="categoria", values="valor", title="Distribuição por categoria")
        st.plotly_chart(fig, use_container_width=True)

        fig_bar = px.bar(df_filtrado.groupby("categoria")["valor"].sum().reset_index(),
                         x="categoria", y="valor", title="Total por categoria")
        st.plotly_chart(fig_bar, use_container_width=True)

    conn.close()
