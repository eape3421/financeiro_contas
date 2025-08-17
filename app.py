import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import speech_recognition as sr
from PIL import Image
import os

st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.markdown("## 📊 Controle Financeiro Pessoal")
st.markdown("Gerencie seus gastos, visualize gráficos e envie relatórios por e-mail.")
st.markdown("---")

# Abas principais
aba1, aba2, aba3, aba4 = st.tabs(["📁 Planilha", "💸 Gráficos", "🎙️ Voz & 📷 Imagem", "📧 E-mail"])

# Variável para armazenar dados manuais
dados_digitados = pd.DataFrame(columns=["Data", "Categoria", "Valor", "Descrição", "Imagem"])

with aba1:
    st.subheader("📁 Upload da planilha")
    uploaded_file = st.file_uploader("Envie sua planilha de gastos (.csv)", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        st.success("Planilha carregada com sucesso!")

        min_date = df['Data'].min()
        max_date = df['Data'].max()
        start_date, end_date = st.date_input("📅 Selecione o período", [min_date, max_date])
        df_filtrado = df[(df['Data'] >= pd.to_datetime(start_date)) & (df['Data'] <= pd.to_datetime(end_date))]
    else:
        df_filtrado = pd.DataFrame()

    st.markdown("### ✍️ Adicionar gasto manualmente com foto")
    with st.form("formulario_manual"):
        data_manual = st.date_input("Data do gasto", value=datetime.today())
        categoria_manual = st.text_input("Categoria")
        valor_manual = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao_manual = st.text_input("Descrição")
        foto_manual = st.camera_input("📷 Tire uma foto do comprovante")
        enviar_manual = st.form_submit_button("Adicionar")

        if enviar_manual:
            if foto_manual:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                caminho_imagem = f"comprovante_{timestamp}.png"
                img = Image.open(foto_manual)
                img.save(caminho_imagem)
            else:
                caminho_imagem = ""

            novo_dado = pd.DataFrame({
                "Data": [data_manual],
                "Categoria": [categoria_manual],
                "Valor": [valor_manual],
                "Descrição": [descricao_manual],
                "Imagem": [caminho_imagem]
            })
            dados_digitados = pd.concat([dados_digitados, novo_dado], ignore_index=True)
            st.success("Gasto adicionado com sucesso!")
            st.dataframe(dados_digitados)

    # Combinar dados da planilha com os digitados
    if not df_filtrado.empty:
        df_completo = pd.concat([df_filtrado, dados_digitados], ignore_index=True)
    else:
        df_completo = dados_digitados

with aba2:
    if not df_completo.empty:
        st.subheader("💸 Gastos por categoria")
        categoria_total = df_completo.groupby("Categoria")["Valor"].sum()
        fig, ax = plt.subplots()
        categoria_total.plot(kind="bar", ax=ax)
        st.pyplot(fig)
    else:
        st.warning("Adicione dados manualmente ou envie uma planilha na aba '📁 Planilha'.")

with aba3:
    col1, col2 = st.columns(2)

    with col1:
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

    with col2:
        st.subheader("📷 Captura rápida de comprovante")
        foto = st.camera_input("Tire uma foto do comprovante")
        if foto:
            img = Image.open(foto)
            st.image(img, caption="Comprovante capturado", use_column_width=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho = f"comprovante_{timestamp}.png"
            img.save(caminho)
            st.success(f"Imagem salva como {caminho}")

with aba4:
    st.subheader("📧 Enviar relatório por e-mail")
    destinatario = st.text_input("E-mail do destinatário")
    if st.button("Enviar"):
        if not df_completo.empty:
            try:
                msg = MIMEMultipart()
                msg['From'] = "seuemail@gmail.com"
                msg['To'] = destinatario
                msg['Subject'] = "Relatório Financeiro"

                corpo = f"Relatório de gastos:\n\n{df_completo.drop(columns='Imagem').to_string(index=False)}"
                msg.attach(MIMEText(corpo, 'plain'))

                # Anexar imagens
                imagens = df_completo["Imagem"].dropna().unique()
                for caminho in imagens:
                    if caminho and os.path.exists(caminho):
                        with open(caminho, "rb") as f:
                            parte = MIMEBase('application', 'octet-stream')
                            parte.set_payload(f.read())
                            encoders.encode_base64(parte)
                            parte.add_header('Content-Disposition', f'attachment; filename={os.path.basename(caminho)}')
                            msg.attach(parte)

                servidor = smtplib.SMTP('smtp.gmail.com', 587)
                servidor.starttls()
                servidor.login("seuemail@gmail.com", "sua_senha_de_app")
                servidor.send_message(msg)
                servidor.quit()
                st.success("Relatório enviado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao enviar e-mail: {e}")
        else:
            st.warning("Adicione dados ou carregue uma planilha para enviar o relatório.")
