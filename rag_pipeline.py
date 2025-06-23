from chromadb.config import Settings
import google.generativeai as genai
from dotenv import load_dotenv
import chromadb
import logging
import socket
import ollama
import os


# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Carregar variáveis de ambiente
load_dotenv()

# Constantes de configuração
GEMINI_MODEL = "gemini-2.0-flash"
OLLAMA_MODEL = "gemma3:1b"
EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_DB_PATH = "./vector_db"
COLLECTION_NAME = "pbl_assistant_collection"
TOP_K = 3  # Número de chunks de contexto a retornar

# 3. Checagem de conectividade
def check_internet_connection():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

def build_tutor_prompt(question: str, context: str, chat_history: str = "") -> str:
    return f"""# Contexto dos PDFs
{context}

# Histórico da Conversa
{chat_history}

# Pergunta do estudante
{question}

Sua tarefa é agir como um tutor educacional. NÃO forneça a resposta direta. Em vez disso,
utilize analogias, exemplos do cotidiano ou perguntas-guia para estimular o raciocínio do estudante,
ajudando-o a chegar à resposta por conta própria. Adapte a linguagem ao nível do estudante,
seja motivador, paciente e incentive a reflexão. Se não for possível ajudar com base no contexto, 
diga que não encontrou pistas suficientes.
"""

# 4. Gerador de resposta via Ollama (offline)
def get_ollama_response_stream(question: str, context: str, chat_history: str = ""):
    prompt = build_tutor_prompt(question, context, chat_history)
    messages = [
        {"role": "system", "content": "Você é um tutor educacional especializado em estimular o raciocínio dos estudantes. Use analogias, exemplos e perguntas-guia em vez de respostas diretas."},
        {"role": "user", "content": prompt},
    ]
    stream = ollama.chat(model=OLLAMA_MODEL, messages=messages, stream=True)
    for chunk in stream:
        content = chunk.get("message", {}).get("content", "")
        if content:
            yield content

# 5. Gerador de resposta via Gemini (online)
def get_gemini_response_stream(question: str, context: str, chat_history: str = ""):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        yield "[Erro] Chave da API do Gemini não encontrada no .env."
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = prompt = build_tutor_prompt(question, context, chat_history)
    try:
        response_stream = model.generate_content(prompt, stream=True)
        for chunk in response_stream:
            content = getattr(chunk, "text", None)
            if content:
                yield content
    except Exception as e:
        # Ao falhar, use uma exceção especial para identificar o erro e ativar o failover no pipeline
        raise RuntimeError(f"[Erro ao acessar Gemini]: {e}")

# 6. Pipeline híbrido com failover Gemini -> Ollama
def get_hybrid_response_stream(question: str, history: list = None):
    # a. Gerar embedding da pergunta
    try:
        emb_result = ollama.embeddings(model=EMBEDDING_MODEL, prompt=question)
        query_embedding = emb_result.get("embedding")
        if not query_embedding:
            yield "[Erro] Não foi possível gerar o embedding da pergunta."
            return
    except Exception as e:
        yield f"[Erro] Falha ao gerar embedding da pergunta: {e}"
        return

    # b. Consultar ChromaDB para os chunks mais relevantes
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH, settings=Settings(allow_reset=True))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
            include=["documents", "metadatas"]
        )
        chunks = []
        for idx, doc in enumerate(results.get("documents", [[]])[0]):
            meta = results.get("metadatas", [[]])[0][idx]
            fonte = meta.get("source", "desconhecido")
            chunks.append(f"[Fonte: {fonte}]\n{doc}")
        context = "\n\n".join(chunks)
    except Exception as e:
        yield f"[Erro] Não foi possível recuperar contexto do ChromaDB: {e}"
        return

    # c. Montar histórico da conversa
    chat_history = ""
    if history:
        # pegue os últimos 6 turnos (user/assistant) para não explodir o prompt
        for msg in history[-6:]:
            if msg["role"] == "user":
                chat_history += f"Aluno: {msg['content']}\n"
            else:
                chat_history += f"Tutor: {msg['content']}\n"

    # d. Decidir rota online/offline, com failover Gemini->Ollama
    if check_internet_connection():
        logging.info("Tentando Gemini (online)...")
        try:
            for chunk in get_gemini_response_stream(question, context, chat_history):
                yield chunk
        except Exception as e:
            logging.error(f"Gemini falhou: {e}. Fazendo failover para Ollama (offline).")
            for chunk in get_ollama_response_stream(question, context, chat_history):
                yield chunk
    else:
        logging.info("Usando Ollama (offline)")
        yield from get_ollama_response_stream(question, context, chat_history)