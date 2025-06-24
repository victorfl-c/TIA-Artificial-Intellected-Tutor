# 👩‍🏫 TIA — Documentação Técnica

## Visão Geral

TIA (Tutor de Inteligência Artificial) é um sistema de apoio ao estudo baseado em IA, capaz de responder perguntas dos estudantes utilizando o conteúdo de PDFs enviados pelos próprios usuários. O sistema combina técnicas de RAG (Retrieval-Augmented Generation), mantendo flexibilidade para operar totalmente offline (usando modelos locais via Ollama) ou online (usando o Google Gemini se disponível).

> 💡 **Nota pedagógica:**  
> O TIA foi projetado para **não dar respostas diretas**. Seu objetivo é atuar como um tutor, promovendo a reflexão e a construção autônoma do conhecimento pelo estudante através de exemplos, analogias e perguntas orientadoras.

---

## 🏗️ Arquitetura Detalhada

O sistema é composto por um frontend interativo, um backend que orquestra a lógica, um pipeline de ingestão de dados e o pipeline RAG híbrido que gera as respostas.

### 1. Frontend (`app.py`)
- **Framework:** Streamlit.
- **Funções principais:**
  - Interface de chat com histórico e suporte a múltiplas conversas.
  - Funcionalidade de upload de arquivos PDF para alimentar a base de conhecimento.
  - Comunicação com o backend FastAPI para enviar perguntas e arquivos.
  - Gerenciamento de estado: As conversas e seus títulos são mantidos no `st.session_state` do Streamlit.

### 2. Backend API (`main.py`)
- **Framework:** FastAPI.
- **Principais endpoints:**
  - `/ask-stream`: Recebe a pergunta e o histórico da conversa, retornando a resposta do tutor em formato de streaming para uma experiência interativa.
  - `/upload`: Gerencia o upload de múltiplos arquivos PDF, salvando-os na pasta `./knowledge_base/` e acionando o processo de reingestão da base de conhecimento.

### 3. Pipeline de Ingestão (`ingest.py`)
- **Função principal:** `run_ingestion()`.
- **Operação:**
  - Carrega documentos PDF da pasta `./knowledge_base/`.
  - Divide os documentos em chunks (fragmentos de texto) menores e com sobreposição, utilizando o `RecursiveCharacterTextSplitter` do LangChain.
  - Gera embeddings (vetores numéricos) para cada chunk localmente, usando o modelo `nomic-embed-text` via Ollama.
  - Armazena os vetores e os textos correspondentes em um banco de dados vetorial local e persistente (ChromaDB).
  - **Para evitar duplicatas:** Antes de adicionar os novos chunks de um PDF, o script remove todos os chunks antigos daquele arquivo (com base no campo `source` nos metadados).

### 4. Pipeline RAG Híbrido (`rag_pipeline.py`)
- **Fluxo principal:** `get_hybrid_response_stream(question, history)`.
- **Operação:**
  - Gera um embedding para a pergunta do usuário via Ollama.
  - Consulta o ChromaDB para recuperar os chunks de texto mais relevantes (Top-K) que servirão de contexto.
  - Monta um prompt detalhado contendo o contexto recuperado, o histórico recente da conversa e a pergunta do usuário. O prompt é construído pela função `build_tutor_prompt`, que instrui o modelo a agir como um tutor e não a dar respostas diretas.
  - **Lógica de Failover:** O sistema verifica a conectividade com a internet. Se houver conexão, tenta gerar a resposta com o modelo online (Google Gemini). Em caso de falha ou ausência de conexão, aciona o modelo local (Ollama) automaticamente.

---

## 🚀 Como Usar (Instalação e Execução)

1. **Instale as dependências**  
   ```bash
   pip install -r requirements.txt
   ```

2. **Baixe e rode o Ollama**  
   - Instale o [Ollama](https://ollama.com/) em sua máquina.
   - Baixe os modelos necessários via terminal:
     ```bash
     ollama pull nomic-embed-text
     ollama pull gemma3:1b
     ```

3. **(Opcional) Configure o Google Gemini**  
   - Crie um arquivo chamado `.env` na raiz do projeto.
   - Adicione sua chave da API do Gemini ao arquivo:
     ```
     GOOGLE_API_KEY=sua_chave_aqui
     ```

4. **Execute a ingestão de dados (opcional)**  
   - Para popular a base de conhecimento inicial, coloque arquivos PDF na pasta `./knowledge_base/`.
   - Execute o script de ingestão:
     ```bash
     python ingest.py
     ```

5. **Inicie os servidores**  
   - Inicie o servidor de backend (FastAPI) em um terminal:
     ```bash
     uvicorn main:app --reload
     ```
   - Inicie o servidor de frontend (Streamlit) em outro terminal:
     ```bash
     streamlit run app.py
     ```
   - Acesse a interface do TIA no seu navegador em [http://localhost:8501](http://localhost:8501).

---

## 📂 Estrutura de Pastas Recomendada

```
/project-root
│
├── app.py                # Frontend Streamlit
├── main.py               # Backend FastAPI
├── ingest.py             # Pipeline de ingestão de PDFs
├── rag_pipeline.py       # Pipeline de RAG híbrido
├── knowledge_base/       # PDFs enviados pelos usuários
├── vector_db/            # Banco vetorial persistente do ChromaDB
├── .env                  # Variáveis de ambiente (ex: API Key do Gemini)
└── requirements.txt      # Dependências do projeto
```

---

## ⚙️ Tecnologias Utilizadas

- **Python 3.10+**
- **streamlit:** Interface web do usuário
- **fastapi / uvicorn:** API backend
- **chromadb:** Armazenamento vetorial
- **langchain-community / langchain-text-splitters:** Carregamento e chunking de PDFs
- **google-generativeai:** Gemini LLM online
- **ollama:** LLM e embeddings locais
- **python-dotenv:** Carregamento de variáveis de ambiente
- **requests:** Comunicação frontend-backend

---

## Pontos Técnicos Relevantes

- **ChromaDB:** Armazena embeddings de chunks de texto dos PDFs, com persistência local.
- **Ollama:** Usado tanto para gerar embeddings quanto para respostas offline via LLM local.
- **Google Gemini:** Usado para respostas online, se chave e conexão disponíveis.
- **Prompt Único:** Função `build_tutor_prompt` garante que tanto Gemini quanto Ollama recebem o mesmo contexto e instrução.
- **Histórico de conversa:** Enviado junto à pergunta, permitindo que o tutor LLM mantenha contexto e continuidade pedagógica.
- **Failover automático:** Se Gemini não estiver disponível ou falhar, o sistema cai automaticamente para Ollama.
- **Logging:** Toda a aplicação usa logging padronizado para fácil diagnóstico.
- **Evita duplicatas na base:** Antes de adicionar chunks de um PDF, remove todos os chunks antigos daquele arquivo na coleção, considerando o campo `source` do metadata.

---

## Observações Finais

- O sistema foi desenhado para ser extensível e seguro: os PDFs e embeddings são mantidos localmente, a menos que Gemini seja usado.
- O prompt pedagógico pode ser facilmente customizado na função `build_tutor_prompt`.
- O histórico das conversas é mantido apenas na sessão do usuário (client-side), sem persistência de longo prazo.
- Se desejar autenticação, logging avançado, ou persistência de histórico, adapte os módulos correspondentes.

---

## 📄 Licença

Este projeto está licenciado sob os termos da Licença MIT. Consulte o arquivo [LICENSE](https://github.com/victorfl-c/TIA-Artificial-Intellected-Tutor/blob/main/LICENSE) para mais detalhes.
