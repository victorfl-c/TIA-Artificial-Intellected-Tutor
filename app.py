import streamlit as st
import requests
import uuid

BACKEND_URL = "http://localhost:8000"

if "conversations" not in st.session_state:
    st.session_state["conversations"] = {}
if "current_conversation_id" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state["current_conversation_id"] = new_id
    st.session_state["conversations"][new_id] = []
if "conversation_titles" not in st.session_state:
    st.session_state["conversation_titles"] = {}

def extrair_tema(mensagem):
    # Pega as 5 primeiras palavras como título/tema
    return " ".join(mensagem.split()[:5]) + "..."

def start_new_conversation():
    new_id = str(uuid.uuid4())
    st.session_state["current_conversation_id"] = new_id
    st.session_state["conversations"][new_id] = []
    st.session_state["conversation_titles"][new_id] = "Nova conversa"

def switch_conversation(conv_id):
    st.session_state["current_conversation_id"] = conv_id

with st.sidebar:
    st.title("Assistente Virtual")
    st.header("Adicionar Conteúdo")
    uploaded_files = st.file_uploader(
        "Selecione PDF(s) para upload", type=["pdf"], accept_multiple_files=True
    )
    if st.button("Processar Arquivos") and uploaded_files:
        files = [
            ("files", (file.name, file.getbuffer(), "application/pdf"))
            for file in uploaded_files
        ]
        with st.spinner("Enviando arquivos e reprocessando base..."):
            response = requests.post(f"{BACKEND_URL}/upload", files=files)
            if response.status_code == 200:
                st.success("Arquivos enviados e base reprocessada com sucesso!")
            else:
                st.error(f"Erro ao processar arquivos: {response.text}")

    st.divider()
    if st.button("🆕 Nova Conversa"):
        start_new_conversation()
    
    st.header("Histórico")
    for conv_id in st.session_state["conversations"]:
        # Extrai o tema da primeira mensagem, se não houver, mostra "Nova conversa"
        tema = st.session_state["conversation_titles"].get(conv_id)
        conv = st.session_state["conversations"][conv_id]
        if not tema and conv:
            tema = extrair_tema(conv[0]["content"])
            st.session_state["conversation_titles"][conv_id] = tema
        if not tema:
            tema = "Nova conversa"
        if st.button(f"🗂 {tema}", key=f"conv-btn-{conv_id}"):
            switch_conversation(conv_id)

st.title("👩‍🏫 TIA")
current_conv_id = st.session_state["current_conversation_id"]
conversation = st.session_state["conversations"][current_conv_id]

# Exibe histórico (mensagens user e assistant)
for msg in conversation:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Digite sua pergunta...")

if user_input:
    # Se for a primeira mensagem da conversa, define o tema
    if len(conversation) == 0:
        st.session_state["conversation_titles"][current_conv_id] = extrair_tema(user_input)

    # Adiciona mensagem do usuário ao histórico
    conversation.append({"role": "user", "content": user_input})
    
    # NOVO: Exibe a mensagem do usuário na tela imediatamente
    with st.chat_message("user"):
        st.markdown(user_input)

    # Agora, o código continua para obter e mostrar a resposta do assistente
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            def stream_response():
                response = requests.post(
                    f"{BACKEND_URL}/ask-stream",
                    json={
                        "question": user_input,
                        "history": conversation  # Envia o histórico da conversa
                    },
                    stream=True,
                )
                buffer = ""
                for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        buffer += chunk
                        yield chunk
                # Adiciona a resposta completa ao histórico ao final do stream
                conversation.append({"role": "assistant", "content": buffer})
                st.session_state["conversations"][current_conv_id] = conversation

            st.write_stream(stream_response)