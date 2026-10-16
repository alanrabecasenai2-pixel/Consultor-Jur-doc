import os
import streamlit as st
from openai import AzureOpenAI
import PyPDF2

# Configuração da página do Streamlit
st.set_page_config(
    page_title="ChatBot RAG - Microsoft Foundry",
    page_icon="🤖",
    layout="wide"
)

# 1. CSS Customizado para estilizar a borda da aplicação e o chat
st.markdown("""
    <style>
    /* Borda estilizada ao redor do container principal */
    .main .block-container {
        border: 2px solid #4A90E2;
        border-radius: 12px;
        padding: 2rem;
        background-color: #FAFAFA;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    
    /* Estilização da barra lateral */
    [data-testid="stSidebar"] {
        background-color: #F0F2F6;
        border-right: 1px solid #E0E0E0;
    }
    
    /* Títulos e cabeçalhos */
    h1, h2, h3 {
        color: #2C3E50;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Configuração da API (Microsoft Foundry / Azure OpenAI)
API_KEY = "6t2pTNsmNafDyo53MDAFIrvvQRBZXP7dLcr5j3TLxMS34LQVq3ZUJQQJ99CHACHYHv6XJ3w3AAAAACOGT7os"
DEPLOYMENT_NAME = "gpt-4.1-mini"
ENDPOINT = "https://marcelomaffeis-05082026-resource.services.ai.azure.com/"

# Inicializando o cliente AzureOpenAI
# O Azure OpenAI geralmente requer uma versão de API recente, como '2024-02-01' ou similar
try:
    client = AzureOpenAI(
        api_key=API_KEY,
        api_version="2024-02-01-preview",
        azure_endpoint=ENDPOINT
    )
except Exception as e:
    st.error(f"Erro ao inicializar o cliente Azure OpenAI: {e}")

# Inicialização do st.session_state para histórico e contexto do arquivo
if "messages" not in st.session_state:
    st.session_state.messages = []

if "document_text" not in st.session_state:
    st.session_state.document_text = ""

# 3. Upload de Arquivos na Barra Lateral e Sistema RAG Básico
with st.sidebar:
    st.header("📄 Base de Conhecimento (RAG)")
    st.markdown("Envie um arquivo PDF ou TXT para alimentar o contexto do ChatBot.")
    
    uploaded_file = st.file_uploader("Escolha um arquivo", type=["pdf", "txt"])
    
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        extracted_text = ""
        
        if file_extension == "txt":
            try:
                extracted_text = uploaded_file.getvalue().decode("utf-8")
            except Exception:
                extracted_text = uploaded_file.getvalue().decode("latin-1")
                
        elif file_extension == "pdf":
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
            except Exception as e:
                st.error(f"Erro ao ler o PDF: {e}")
                
        if extracted_text:
            st.session_state.document_text = extracted_text
            st.success(f"Arquivo '{uploaded_file.name}' carregado e processado com sucesso!")
        else:
            st.warning("O arquivo parece estar vazio ou o texto não pôde ser extraído.")
            
    if st.session_state.document_text:
        if st.button("Limpar Documento Carregado"):
            st.session_state.document_text = ""
            st.rerun()

# 4. Interface Principal de Chat
st.title("🤖 ChatBot Acadêmico - Microsoft Foundry")
st.markdown("Converse com o assistente baseado no seu documento enviado.")

# Exibição do histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada do usuário
if prompt := st.chat_input("Faça uma pergunta sobre o documento ou geral..."):
    # Adiciona a mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Construção do Prompt com Lógica RAG
    system_prompt = (
        "Você é um assistente virtual prestativo e acadêmico. "
        "Responda à pergunta do usuário com base no contexto fornecido abaixo. "
        "Se a resposta não estiver presente no contexto, utilize seu conhecimento geral "
        "mas avise que a informação não consta no documento carregado."
    )
    
    context_content = st.session_state.document_text
    
    # Montagem das mensagens para a API do Azure OpenAI
    messages_payload = [
        {"role": "system", "content": system_prompt}
    ]
    
    if context_content:
        messages_payload.append({
            "role": "system", 
            "content": f"--- CONTEXTO DO DOCUMENTO ---\n{context_content}\n-----------------------------"
        })
        
    # Adiciona o histórico recente da conversa para manter o fluxo
    for msg in st.session_state.messages:
        messages_payload.append({"role": msg["role"], "content": msg["content"]})
        
    # Chamada ao modelo no Azure
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Pensando...")
        
        try:
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=messages_payload,
                temperature=0.3,
                max_tokens=800
            )
            bot_response = response.choices[0].message.content
            message_placeholder.markdown(bot_response)
            
            # Salva a resposta no histórico
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            
        except Exception as e:
            error_msg = f"Ocorreu um erro ao comunicar com a API do Azure OpenAI: {e}"
            message_placeholder.error(error_msg)
