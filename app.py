import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sqlite3

# 🔗 Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 🎯 Banco de dados local para metas
conn_sqlite = sqlite3.connect("financeiro.db", check_same_thread=False)
cursor = conn_sqlite.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS metas (
        categoria TEXT PRIMARY KEY,
        valor REAL
    )
""")
conn_sqlite.commit()



# 🎯 Banco de dados para metas
conn = sqlite3.connect("financeiro.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS metas (
        categoria TEXT PRIMARY KEY,
        valor REAL
    )
""")
conn.commit()

def salvar_meta(categoria, valor):
    cursor.execute("""
        INSERT INTO metas (categoria, valor)
        VALUES (?, ?)
        ON CONFLICT(categoria) DO UPDATE SET valor=excluded.valor
    """, (categoria, valor))
    conn.commit()

def carregar_metas():
    cursor.execute("SELECT categoria, valor FROM metas")
    return dict(cursor.fetchall())

# 🧠 Funções principais
def filtrar_por_periodo(df):
    if df.empty:
        return pd.DataFrame(columns=["Data", "Categoria", "Descrição", "Valor"])
    min_date = df['Data'].min()
    max_date = df['Data'].max()
    start_date, end_date = st.date_input("📅 Selecione o período", [min_date, max_date])
    return df[(df['Data'] >= pd.to_datetime(start_date)) & (df['Data'] <= pd.to_datetime(end_date))]

def mostrar_indicadores(df_filtrado):
    st.subheader("📌 Indicadores")
    categoria_total = df_filtrado.groupby("Categoria")["Valor"].sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total gasto", f"R$ {df_filtrado['Valor'].sum():.2f}")
    col2.metric("📈 Média por gasto", f"R$ {df_filtrado['Valor'].mean():.2f}")
    if not categoria_total.empty:
        categoria_top = categoria_total.idxmax()
        col3.metric("🔥 Categoria mais cara", f"{categoria_top} - R$ {categoria_total.max():.2f}")
    else:
        col3.metric("🔥 Categoria mais cara", "Nenhum dado disponível")
    return categoria_total

def mostrar_graficos(df_filtrado, categoria_total):
    st.subheader("📊 Gastos por categoria")
    fig = px.bar(categoria_total.reset_index(), x="Categoria", y="Valor", title="Gastos por Categoria", color="Categoria")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📉 Evolução dos gastos")
    df_evolucao = df_filtrado.groupby("Data")["Valor"].sum().reset_index()
    fig2 = px.line(df_evolucao, x="Data", y="Valor", markers=True, title="Evolução dos Gastos")
    st.plotly_chart(fig2, use_container_width=True)

def comparar_metas(df_filtrado):
    st.subheader("📊 Comparativo com metas")
    categoria_total = df_filtrado.groupby("Categoria")["Valor"].sum()
    metas_salvas = carregar_metas()
    for categoria, meta in metas_salvas.items():
        gasto = categoria_total.get(categoria, 0)
        percentual = (gasto / meta) * 100 if meta > 0 else 0
        cor = "🟢" if gasto <= meta else "🔴"
        st.write(f"{cor} {categoria}: R$ {gasto:.2f} / Meta: R$ {meta:.2f} ({percentual:.1f}%)")

    estouradas = [cat for cat, meta in metas_salvas.items() if categoria_total.get(cat, 0) > meta]
    if estouradas:
        st.warning(f"⚠️ Você ultrapassou a meta nas categorias: {', '.join(estouradas)}")

def exportar_e_enviar(df_filtrado, df):
    st.subheader("📥 Exportar dados")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Baixar como CSV", data=csv, file_name="gastos_financeiros.csv", mime="text/csv")

    st.subheader("📧 Enviar relatório por e-mail")
    destinatario = st.text_input("E-mail do destinatário")
    if st.button("Enviar"):
        try:
            msg = MIMEMultipart()
            msg['From'] = "seuemail@gmail.com"
            msg['To'] = destinatario
            msg['Subject'] = "Relatório Financeiro"
            corpo = f"Relatório de gastos:\n\n{df_filtrado.to_string(index=False)}"
            msg.attach(MIMEText(corpo, 'plain'))
            servidor = smtplib.SMTP('smtp.gmail.com', 587)
            servidor.starttls()
            servidor.login("seuemail@gmail.com", "sua_senha_de_app")
            servidor.send_message(msg)
            servidor.quit()
            st.success("Relatório enviado com sucesso!")
            st.toast("📤 E-mail enviado!")
        except Exception as e:
            st.error(f"Erro ao enviar e-mail: {e}")

# 🚀 Interface principal
st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.title("📊 Controle Financeiro Pessoal")
st.markdown("Gerencie seus gastos, visualize gráficos e envie relatórios por e-mail.")

df = conn.read(worksheet="Sheet1")
df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
st.success("✅ Dados carregados do Google Sheets com sucesso!")


# 📝 Formulário manual
st.subheader("📝 Adicionar gasto manualmente")
with st.form("formulario_manual"):
    data = st.date_input("Data do gasto", value=datetime.today())
    categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Moradia"])
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    enviar = st.form_submit_button("Adicionar")
    if enviar:
        novo_gasto = pd.DataFrame([{ "Data": data, "Categoria": categoria, "Descrição": descricao, "Valor": valor }])
        df = pd.concat([df, novo_gasto], ignore_index=True)
        st.success("Gasto adicionado com sucesso!")

# 🔍 Filtro e abas
df_filtrado = filtrar_por_periodo(df)
aba1, aba2, aba3 = st.tabs(["📊 Visão Geral", "🎯 Metas", "📥 Exportar & Extras"])

with aba1:
    categoria_total = mostrar_indicadores(df_filtrado)
    mostrar_graficos(df_filtrado, categoria_total)

with aba2:
    st.subheader("🎯 Defina suas metas mensais")
    metas_salvas = carregar_metas()
    metas = {}
    categorias = ["Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Moradia"]
    with st.form("form_metas"):
        for categoria in categorias:
            valor_inicial = metas_salvas.get(categoria, 0.0)
            metas[categoria] = st.number_input(f"Meta para {categoria} (R$)", min_value=0.0, step=10.0, value=valor_inicial, key=f"meta_{categoria}")
        enviar_metas = st.form_submit_button("Salvar metas")
        if enviar_metas:
            for categoria, valor in metas.items():
                salvar_meta(categoria, valor)
            st.success("✅ Metas salvas com sucesso!")
            st.balloons()
    comparar_metas(df_filtrado)

with aba3:
    exportar_e_enviar(df_filtrado, df)
