from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.config import Settings
import chromadb
import logging
import ollama
import os

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Constantes de configuração
KNOWLEDGE_BASE_PATH = "./knowledge_base"
VECTOR_DB_PATH = "./vector_db"
EMBEDDING_MODEL = "nomic-embed-text"  # Modelo do Ollama para embeddings
COLLECTION_NAME = "pbl_assistant_collection"

def run_ingestion(overwrite=False):
    """
    Executa o processo de ingestão de dados:
    - Carrega PDFs da knowledge_base,
    - Divide em chunks,
    - Gera embeddings com Ollama,
    - Salva os vetores no ChromaDB de forma persistente.
    - Se overwrite=True, limpa toda a coleção antes de adicionar os novos dados.
    - Remove duplicatas de cada PDF antes de adicionar novamente.
    """
    os.makedirs(KNOWLEDGE_BASE_PATH, exist_ok=True)
    # a. Carregar documentos PDF
    documents = []
    for filename in os.listdir(KNOWLEDGE_BASE_PATH):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(KNOWLEDGE_BASE_PATH, filename)
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            # Adiciona um campo "source" para cada documento
            for doc in docs:
                doc.metadata["source"] = filename
            documents.extend(docs)

    if not documents:
        logging.warning("Nenhum documento PDF encontrado na pasta knowledge_base.")
        return

    # b. Dividir os documentos em chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    logging.info(f"Total de chunks gerados: {len(chunks)}")

    # c. Inicializar cliente ChromaDB com persistência
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH, settings=Settings(allow_reset=True))

    # d. Obter ou criar a coleção
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    if overwrite:
        logging.info("Limpando toda a coleção antes de adicionar os novos dados (overwrite=True).")
        collection.delete(where={})  # Remove todos os documentos

    # e. Para cada chunk, gerar embedding e preparar dados
    embeddings = []
    texts = []
    metadatas = []
    ids = []
    for idx, chunk in enumerate(chunks):
        text = chunk.page_content
        metadata = chunk.metadata
        source_file = metadata.get("source", f"unknown_{idx}")
        # Antes de adicionar, remove os chunks antigos deste arquivo se ainda não fez nesta execução
        # Vamos remover duplicatas do arquivo antes de adicionar os novos
        if not any(m.get("source", None) == source_file for m in metadatas):
            collection.delete(where={"source": source_file})
        try:
            emb_result = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
            vector = emb_result.get("embedding")
            if not vector:
                logging.warning(f"[Aviso] Não foi possível gerar embedding para o chunk {idx}. Pulando.")
                continue
            embeddings.append(vector)
            texts.append(text)
            metadatas.append(metadata)
            # Gera IDs únicos: source_nomearquivo_idx
            unique_id = f"{source_file}_{idx}"
            ids.append(unique_id)
        except Exception as e:
            logging.error(f"[Erro] Falha ao gerar embedding do chunk {idx}: {e}")

    # f. Adicionar os embeddings, textos e metadados à coleção
    if embeddings:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logging.info(f"Ingestão concluída: {len(embeddings)} chunks foram processados e armazenados no ChromaDB.")
    else:
        logging.warning("Nenhum embedding válido foi gerado. Nada foi armazenado.")

if __name__ == "__main__":
    # Você pode rodar sobrescrevendo toda a base com: run_ingestion(overwrite=True)
    run_ingestion(overwrite=True)