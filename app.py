import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import speech_recognition as sr
from PIL import Image

st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.markdown("## 📊 Controle Financeiro Pessoal")
st.markdown("Gerencie seus gastos, visualize gráficos e envie relatórios por e-mail.")
st.markdown("---")

# Abas principais
aba1, aba2, aba3, aba4 = st.tabs(["📁 Planilha", "💸 Gráficos", "🎙️ Voz & 📷 Imagem", "📧 E-mail"])

# Variável para armazenar dados manuais
dados_digitados = pd.DataFrame(columns=["Data", "Categoria", "Valor", "Descrição"])
df_completo = pd.DataFrame(columns=["Data", "Categoria", "Valor", "Descrição"])
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

    st.markdown("### ✍️ Adicionar gasto manualmente")
    with st.form("formulario_manual"):
        data_manual = st.date_input("Data do gasto", value=datetime.today())
        categorias_opcoes = [
            "Transporte", "Alimentação", "Cartão de crédito", "Cartão de débito",
            "PIX", "Lazer", "Saúde", "Receita"
        ]
        categoria_manual = st.selectbox("Categoria", categorias_opcoes)
        valor_manual = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao_manual = st.text_input("Descrição")
        enviar_manual = st.form_submit_button("Adicionar")
        if enviar_manual:
            novo_dado = pd.DataFrame({
                "Data": [data_manual],
                "Categoria": [categoria_manual],
                "Valor": [valor_manual],
                "Descrição": [descricao_manual]
            })
            dados_digitados = pd.concat([dados_digitados, novo_dado], ignore_index=True)
            st.success("Gasto adicionado com sucesso!")
    st.dataframe(dados_digitados)
    st.markdown("### 📤 Exportar dados para Excel")
if st.button("Exportar Excel"):
    df_completo.to_excel("relatorio_financeiro.xlsx", index=False)
    st.success("Arquivo 'relatorio_financeiro.xlsx' gerado com sucesso!")

    # Combinar dados da planilha com os digitados
    if not df_filtrado.empty:
        df_completo = pd.concat([df_filtrado, dados_digitados], ignore_index=True)
    else:
        df_completo = dados_digitados

with aba2:
    if not df_completo.empty:
        st.subheader("📊 Dashboard Financeiro")

        total_receita = df_completo[df_completo["Categoria"] == "Receita"]["Valor"].sum()
        total_despesa = df_completo[df_completo["Categoria"] != "Receita"]["Valor"].sum()
        saldo = total_receita - total_despesa
        economia_percentual = (saldo / total_receita * 100) if total_receita > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Receita", f"R$ {total_receita:.2f}")
        col2.metric("📉 Despesa", f"R$ {total_despesa:.2f}")
        col3.metric("📊 Saldo", f"R$ {saldo:.2f}")
        col4.metric("📈 Economia (%)", f"{economia_percentual:.1f}%")

        st.markdown("---")
        st.subheader("🎯 Meta de economia mensal")
        meta = st.number_input("Defina sua meta de economia (R$)", min_value=0.0, format="%.2f")
        if meta > 0:
            if saldo >= meta:
                st.success(f"✅ Meta atingida! Você economizou R$ {saldo:.2f}")
            else:
                st.error(f"⚠️ Meta não atingida. Faltam R$ {meta - saldo:.2f}")

        st.markdown("---")
        st.subheader("📊 Gastos por categoria (barra)")
        categoria_total = df_completo[df_completo["Categoria"] != "Receita"].groupby("Categoria")["Valor"].sum()
        fig_bar, ax_bar = plt.subplots()
        categoria_total.plot(kind="bar", ax=ax_bar)
        st.pyplot(fig_bar)

        st.subheader("🥧 Gastos por categoria (pizza)")
        fig_pie, ax_pie = plt.subplots()
        categoria_total.plot(kind="pie", ax=ax_pie, autopct="%1.1f%%")
        ax_pie.set_ylabel("")
        st.pyplot(fig_pie)
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
        st.subheader("📷 Adicionar comprovante por imagem")
        imagem = st.file_uploader("Envie uma imagem", type=["jpg", "png"])
        if imagem:
            img = Image.open(imagem)
            st.image(img, caption="Comprovante enviado", use_column_width=True)

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
                corpo = f"Relatório de gastos:\n\n{df_completo.to_string(index=False)}"
                msg.attach(MIMEText(corpo, 'plain'))
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
