import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import speech_recognition as sr
from PIL import Image
import sqlite3

# Conexão com o banco de dados
conn = sqlite3.connect("financeiro.db", check_same_thread=False)
cursor = conn.cursor()

# Criação da tabela de metas
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

st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.title("📊 Controle Financeiro Pessoal")
st.markdown("Gerencie seus gastos, visualize gráficos e envie relatórios por e-mail.")

# Upload de planilha
uploaded_file = st.file_uploader("📁 Envie sua planilha de gastos (.csv)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    st.success("Planilha carregada com sucesso!")
else:
    df = pd.DataFrame(columns=["Data", "Categoria", "Descrição", "Valor"])
    st.info("Nenhum arquivo enviado. Você pode adicionar gastos manualmente abaixo.")

# Formulário manual
st.subheader("📝 Adicionar gasto manualmente")
with st.form("formulario_manual"):
    data = st.date_input("Data do gasto", value=datetime.today())
    categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Moradia"])
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    enviar = st.form_submit_button("Adicionar")

    if enviar:
        novo_gasto = pd.DataFrame([{
            "Data": data,
            "Categoria": categoria,
            "Descrição": descricao,
            "Valor": valor
        }])
        df = pd.concat([df, novo_gasto], ignore_index=True)
        st.success("Gasto adicionado com sucesso!")

# Filtro por período
if not df.empty:
    min_date = df['Data'].min()
    max_date = df['Data'].max()
    start_date, end_date = st.date_input("📅 Selecione o período", [min_date, max_date])
    df_filtrado = df[(df['Data'] >= pd.to_datetime(start_date)) & (df['Data'] <= pd.to_datetime(end_date))]
else:
    df_filtrado = pd.DataFrame(columns=["Data", "Categoria", "Descrição", "Valor"])

# Indicadores principais
st.subheader("📌 Indicadores")
col1, col2, col3 = st.columns(3)
col1.metric("Total gasto", f"R$ {df_filtrado['Valor'].sum():.2f}")
col2.metric("Média por gasto", f"R$ {df_filtrado['Valor'].mean():.2f}")
categoria_top = categoria_total.idxmax()
col3.metric("Categoria mais cara", f"{categoria_top} - R$ {categoria_total.max():.2f}")

    # Gráfico de gastos por categoria
st.subheader("💸 Gastos por categoria")
categoria_total = df_filtrado.groupby("Categoria")["Valor"].sum()
fig, ax = plt.subplots()
categoria_total.plot(kind="bar", ax=ax)
st.pyplot(fig)
    
st.subheader("📊 Comparativo com metas mensais")

categoria_total = df_filtrado.groupby("Categoria")["Valor"].sum()

for categoria, meta in metas.items():
    gasto = categoria_total.get(categoria, 0)
    percentual = (gasto / meta) * 100 if meta > 0 else 0
    cor = "🟢" if gasto <= meta else "🔴"
    st.write(f"{cor} {categoria}: R$ {gasto:.2f} / Meta: R$ {meta:.2f} ({percentual:.1f}%)")

estouradas = [cat for cat, meta in metas.items() if categoria_total.get(cat, 0) > meta]
if estouradas:
    st.warning(f"⚠️ Você ultrapassou a meta nas categorias: {', '.join(estouradas)}")
# Gráfico de pizza
st.subheader("🍕 Distribuição de gastos por categoria")
fig2, ax2 = plt.subplots()
ax2.pie(categoria_total, labels=categoria_total.index, autopct='%1.1f%%', startangle=90)
ax2.axis('equal')
st.pyplot(fig2)
# Evolução dos gastos ao longo do tempo
st.subheader("📉 Evolução dos gastos")
df_evolucao = df_filtrado.groupby("Data")["Valor"].sum().reset_index()
fig3, ax3 = plt.subplots()
ax3.plot(df_evolucao["Data"], df_evolucao["Valor"], marker='o')
ax3.set_xlabel("Data")
ax3.set_ylabel("Valor (R$)")
st.pyplot(fig3)
# Filtro por categoria
st.subheader("🔍 Filtrar por categoria")
categoria_selecionada = st.selectbox("Escolha uma categoria", df_filtrado["Categoria"].unique())
df_categoria = df_filtrado[df_filtrado["Categoria"] == categoria_selecionada]

st.write(f"Gastos na categoria **{categoria_selecionada}**:")
st.dataframe(df_categoria)

# Metas mensais por categoria (formulário interativo)
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

# Comparativo com metas
st.subheader("📊 Comparativo com metas mensais")

categoria_total = df_filtrado.groupby("Categoria")["Valor"].sum()

for categoria, meta in metas.items():
    gasto = categoria_total.get(categoria, 0)
    percentual = (gasto / meta) * 100 if meta > 0 else 0
    cor = "🟢" if gasto <= meta else "🔴"
    st.write(f"{cor} {categoria}: R$ {gasto:.2f} / Meta: R$ {meta:.2f} ({percentual:.1f}%)")

# Alerta de estouro de orçamento
estouradas = [cat for cat, meta in metas.items() if categoria_total.get(cat, 0) > meta]
if estouradas:
    st.warning(f"⚠️ Você ultrapassou a meta nas categorias: {', '.join(estouradas)}")


# Comparativo com metas
st.subheader("🎯 Comparativo com metas mensais")

for categoria, meta in metas.items():
    gasto = categoria_total.get(categoria, 0)
    percentual = (gasto / meta) * 100 if meta > 0 else 0
    cor = "🟢" if gasto <= meta else "🔴"
    st.write(f"{cor} {categoria}: R$ {gasto:.2f} / Meta: R$ {meta:.2f} ({percentual:.1f}%)")

# Alerta de estouro de orçamento
estouradas = [cat for cat, meta in metas.items() if categoria_total.get(cat, 0) > meta]
if estouradas:
    st.warning(f"⚠️ Você ultrapassou a meta nas categorias: {', '.join(estouradas)}")


    # Exportar CSV
    st.subheader("📥 Exportar dados")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Baixar como CSV",
        data=csv,
        file_name="gastos_financeiros.csv",
        mime="text/csv"
    )

# Registro por voz
st.subheader("🎙️ Adicionar gasto por voz")
if st.button("Gravar"):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Fale agora...")
        audio = r.listen(source)
    try:
        texto = r.recognize_google(audio, language="pt-BR")
        st.success(f"Você disse: {texto}")
    except:
        st.error("Não foi possível reconhecer a fala.")

# Registro por imagem
st.subheader("📷 Adicionar comprovante por imagem")
imagem = st.file_uploader("Envie uma imagem", type=["jpg", "png"])
if imagem:
    img = Image.open(imagem)
    st.image(img, caption="Comprovante enviado", use_column_width=True)

# Envio por e-mail
st.subheader("📧 Enviar relatório por e-mail")
destinatario = st.text_input("E-mail do destinatário")
if st.button("Enviar"):
    try:
        msg = MIMEMultipart()
        msg['From'] = "seuemail@gmail.com"
        msg['To'] = destinatario
        msg['Subject'] = "Relatório Financeiro"
        corpo = f"Relatório de gastos entre {start_date} e {end_date}:\n\n{df_filtrado.to_string(index=False)}"
        msg.attach(MIMEText(corpo, 'plain'))
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login("seuemail@gmail.com", "sua_senha_de_app")  # Senha de app
        servidor.send_message(msg)
        servidor.quit()
        st.success("Relatório enviado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
