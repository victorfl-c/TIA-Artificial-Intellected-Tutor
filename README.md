# 👩‍🏫 TIA — Tutor de Inteligência Artificial

TIA (Tutor de Inteligência Artificial) é um sistema de apoio ao estudo baseado em IA, capaz de responder perguntas dos estudantes utilizando o conteúdo de PDFs enviados pelos próprios usuários. O sistema combina técnicas de RAG (Retrieval-Augmented Generation) e pode operar totalmente offline (usando modelos locais via Ollama) ou online (usando o Google Gemini, se disponível).

---

## ✨ Funcionalidades

- **Chat com histórico e múltiplas conversas**
- **Upload de PDFs:** expanda a base de conhecimento facilmente pela interface web
- **Respostas pedagógicas:** o tutor não entrega respostas prontas, mas utiliza analogias, exemplos do cotidiano e perguntas-guia para incentivar o raciocínio e a autonomia do estudante
- **Base de conhecimento local:** seus arquivos e dados permanecem em sua máquina
- **Failover automático:** utiliza Gemini (online) se disponível, ou Ollama (offline) se não houver conexão
- **Pipeline RAG:** busca trechos relevantes dos PDFs para dar contexto às respostas

---

> 💡 **Nota pedagógica**  
> O TIA foi projetado para **não dar respostas diretas**. Seu objetivo é atuar como um tutor, promovendo a reflexão e a construção autônoma do conhecimento, usando exemplos, analogias e perguntas orientadoras.

---

## 🏗️ Arquitetura

- **Frontend:** Streamlit (interface web)
- **Backend:** FastAPI (API para chat e upload)
- **Pipeline de Ingestão:** Processamento de PDFs, geração de embeddings com Ollama e armazenamento no ChromaDB
- **Pipeline RAG:** Recuperação de contexto dos PDFs, montagem de prompt pedagógico e resposta via LLM (Gemini ou Ollama)

---

## 🚀 Como usar

1. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

2. **Baixe e rode o Ollama**
   - Instale o [Ollama](https://ollama.com/)
   - Baixe os modelos necessários:
     ```bash
     ollama pull nomic-embed-text
     ollama pull gemma3:1b
     ```

3. **(Opcional) Configure o Gemini**
   - Crie um arquivo `.env` com a chave da API Gemini:
     ```
     GOOGLE_API_KEY=sua_chave_aqui
     ```

4. **Execute a ingestão inicial (opcional)**
   - Coloque PDFs em `./knowledge_base/` e rode:
     ```bash
     python ingest.py
     ```

5. **Inicie os servidores**
   - Backend (FastAPI):
     ```bash
     uvicorn main:app --reload
     ```
   - Frontend (Streamlit):
     ```bash
     streamlit run app.py
     ```
   - O frontend estará em [http://localhost:8501](http://localhost:8501)
   - O backend FastAPI estará em [http://localhost:8000](http://localhost:8000)

---

## 📂 Estrutura do Projeto

```
/project-root
│
├── app.py                # Frontend Streamlit
├── main.py               # Backend FastAPI
├── ingest.py             # Pipeline de ingestão de PDFs
├── rag_pipeline.py       # Pipeline de RAG híbrido
├── knowledge_base/       # PDFs enviados pelos usuários
├── vector_db/            # Banco vetorial persistente (ChromaDB)
├── .env                  # (Opcional) API Key do Gemini
└── requirements.txt      # Dependências
```

---

## ⚙️ Tecnologias Utilizadas

- **Python 3.10+**
- **Streamlit** (interface web)
- **FastAPI** (API backend)
- **Ollama** (LLM/embeddings local)
- **ChromaDB** (banco vetorial)
- **LangChain Community**
- **Google Generative AI (Gemini)**

---

## 🔒 Privacidade & Segurança

- Todos os arquivos e embeddings ficam locais (offline), exceto ao usar Gemini.
- Nenhum dado do usuário é enviado para terceiros, exceto quando a rota Gemini é utilizada.
- Recomenda-se rodar o sistema apenas em ambientes controlados.

---

## 🛠️ Problemas comuns

- **Respostas curtas ou sem contexto:** certifique-se de que PDFs já foram processados.
- **Gemini não funciona:** verifique conectividade e chave da API.
- **Ollama não responde/erro de modelo:** certifique-se de que o Ollama está rodando e que os modelos estão baixados.

---

## 📄 Licença

Este projeto está licenciado sob os termos da [Licença MIT](LICENSE).  
Consulte as licenças dos modelos Ollama e Gemini para uso comercial.

---

## 🤝 Contribuição

Sugestões, correções e melhorias são bem-vindas! Abra uma issue ou um pull request.
