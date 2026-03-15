import asyncio
import sys
from pathlib import Path
from typing import AsyncIterator, List

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

CHROMA_DIR  = Path("/app/data/chroma")
COLLECTION  = "climarisk_docs"
EMBED_MODEL = "intfloat/multilingual-e5-large"
OLLAMA_URL  = "http://ollama:11434"
MODEL       = "mistral"
TOP_K       = 5


def clean_source_name(source: str) -> str:
    # Strip full path, keep only filename
    name = source.split("/")[-1].split("\\")[-1]
    name = name.replace(".md", "")
    if "__" in name:
        folder, stem = name.split("__", 1)
        return f"{folder} / {stem}"
    return name

SYSTEM_PROMPT = """You are ClimaRisk AI, an emergency response assistant specialized in flood and wildfire risk management.
You have access to official emergency protocols and risk assessment documents.

Context from documents:
{context}

Rules:
- Be concise and direct — rescue agents need fast, clear answers
- Cite the source document when you use specific information
- If risk level is HIGH or CRITICAL, lead with urgency
- Answer in the same language as the question (French or English)
- Never invent information — if unsure, say so clearly
"""

_vectorstore = None
_embeddings  = None


def get_vectorstore() -> Chroma:
    global _vectorstore, _embeddings

    if _vectorstore is None:
        if not CHROMA_DIR.exists():
            raise RuntimeError("ChromaDB not found. Run python services/ingest.py first.")

        print("⏳ Loading multilingual-e5-large + ChromaDB...")
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cuda"},
            encode_kwargs={"normalize_embeddings": True},
        )
        _vectorstore = Chroma(
            persist_directory=str(CHROMA_DIR),
            collection_name=COLLECTION,
            embedding_function=_embeddings,
        )
        print(f"✅ ChromaDB ready — {_vectorstore._collection.count()} chunks")

    return _vectorstore


def add_query_prefix(question: str) -> str:
    """multilingual-e5 requires 'query: ' prefix at retrieval time."""
    return f"query: {question}"


def retrieve(query: str, top_k: int = TOP_K) -> List[dict]:
    try:
        vs      = get_vectorstore()
        prefixed = add_query_prefix(query)
        results = vs.similarity_search_with_relevance_scores(prefixed, k=top_k)
        return [
            {
                "content": doc.page_content.replace("passage: ", "", 1),
                "source":  clean_source_name(doc.metadata.get("source", "unknown")),
                "score":   round(score, 3),
            }
            for doc, score in results
        ]
    except RuntimeError:
        return []


def format_docs(docs) -> str:
    return "\n\n---\n\n".join([
        f"[Source: {clean_source_name(d.metadata.get('source', 'unknown'))}]\n{d.page_content.replace('passage: ', '', 1)}"
        for d in docs
    ])


def build_chain(zone_context: str = ""):
    vs        = get_vectorstore()

    # Wrap retriever to add query prefix for multilingual-e5
    base_retriever = vs.as_retriever(search_kwargs={"k": TOP_K})
    retriever = RunnableLambda(
        lambda q: base_retriever.invoke(add_query_prefix(q))
    )

    llm = ChatOllama(model=MODEL, base_url=OLLAMA_URL, temperature=0.1)

    system = SYSTEM_PROMPT
    if zone_context:
        system += f"\n\nCurrent zone context: {zone_context}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{question}"),
    ])

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


async def stream_answer(question: str, zone_context: str = "") -> AsyncIterator[str]:
    """Stream RAG answer tokens — called by routes/chat.py"""
    try:
        chain = build_chain(zone_context)
        async for token in chain.astream(question):
            yield token
    except RuntimeError as e:
        yield f"⚠️ {str(e)}"


# ── Standalone test ───────────────────────────────────────────────────────────

async def _test():
    question = sys.argv[1] if len(sys.argv) > 1 else "What is the flood evacuation protocol?"
    print(f"\n🔍 Question: {question}\n")

    chunks = retrieve(question)
    print(f"📚 Retrieved {len(chunks)} chunks:")
    for i, c in enumerate(chunks):
        print(f"  [{i+1}] {c['source']} (score: {c['score']})")

    print(f"\n🤖 Answer:\n{'='*50}\n")
    async for token in stream_answer(question):
        print(token, end="", flush=True)
    print("\n")


if __name__ == "__main__":
    asyncio.run(_test())