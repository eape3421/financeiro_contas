import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import speech_recognition as sr
from PIL import Image
import io

st.set_page_config(page_title="Controle Financeiro", layout="wide")

st.title("📊 Controle Financeiro Pessoal")
st.markdown("Gerencie seus gastos, visualize gráficos e envie relatórios por e-mail.")

# Upload de planilha
uploaded_file = st.file_uploader("📁 Envie sua planilha de gastos (.csv)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    st.success("Planilha carregada com sucesso!")

    # Filtro por período
    min_date = df['Data'].min()
    max_date = df['Data'].max()
    start_date, end_date = st.date_input("📅 Selecione o período", [min_date, max_date])

    df_filtrado = df[(df['Data'] >= pd.to_datetime(start_date)) & (df['Data'] <= pd.to_datetime(end_date))]

    # Gráfico de gastos por categoria
    st.subheader("💸 Gastos por categoria")
    categoria_total = df_filtrado.groupby("Categoria")["Valor"].sum()
    fig, ax = plt.subplots()
    categoria_total.plot(kind="bar", ax=ax)
    st.pyplot(fig)

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
            servidor.login("seuemail@gmail.com", "sua_senha_de_app")  # Senha criada às 00:05
            servidor.send_message(msg)
            servidor.quit()
            st.success("Relatório enviado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao enviar e-mail: {e}")

