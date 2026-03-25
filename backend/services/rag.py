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
MODEL       = "mistral:latest"
TOP_K       = 6


SYSTEM_PROMPT = """You are ClimaRisk AI, an emergency response assistant.

STRICT INSTRUCTIONS:
1. PRIORITY: If the user is in immediate danger (Flood/Fire), lead with DIRECT ACTION STEPS (Evacuation, Safety, Emergency numbers). 
2. SECONDARY: Only mention administrative organizations (DDFIP, DGPR, etc.) if specifically asked about "authorities" or "management."
3. NO NOISE: Do not explain what "Yellow" or "Orange" means unless the user asks for the "Risk Level."
4. SOURCE: Cite every instruction as (Source: Folder / Filename).
5. LANGUAGE: Respond in the same language as the user.

Context from documents:
{context}
"""


print(f"⏳ Loading Embedding Model: {EMBED_MODEL}...")
_embeddings = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL,
    model_kwargs={"device": "cuda"},
    encode_kwargs={"normalize_embeddings": True},
)

if not CHROMA_DIR.exists():
    print("⚠️ Warning: ChromaDB directory not found.")
    _vectorstore = None
else:
    print(f"⏳ Connecting to ChromaDB at {CHROMA_DIR}...")
    _vectorstore = Chroma(
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION,
        embedding_function=_embeddings,
    )
    print(f"✅ RAG Engine Ready — {_vectorstore._collection.count()} chunks loaded.")


def clean_source_name(source) -> str:

    if isinstance(source, list):
        return " / ".join(source).replace(".md", "")
    
    name = str(source).split("/")[-1].split("\\")[-1].replace(".md", "")
    if "__" in name:
        return name.replace("__", " / ")
    return name


def add_query_prefix(question: str) -> str:
    return f"query: {question}"

def format_docs(docs) -> str:
    # This provides the context block the LLM sees
    return "\n\n---\n\n".join([
        f"[Source: {clean_source_name(d.metadata.get('source', 'unknown'))}]\n"
        f"{d.page_content.replace('passage: ', '', 1)}"
        for d in docs
    ])

# --- Core Logic ---

def retrieve(query: str, top_k: int = TOP_K) -> List[dict]:
    if _vectorstore is None: return []
    prefixed = add_query_prefix(query)
    # Use relevance scores to filter out garbage matches
    results = _vectorstore.similarity_search_with_relevance_scores(prefixed, k=top_k)
    
    return [
        {
            "content": doc.page_content.replace("passage: ", "", 1),
            "source":  clean_source_name(doc.metadata.get("source", "unknown")),
            "score":   round(score, 3),
        }
        for doc, score in results
    ]


def translate_query_if_needed(query: str) -> str:

    return f"{query} inondation crue incendie feu évacuation secours"    

def build_chain(zone_context: str = ""):
    if _vectorstore is None:
        raise RuntimeError("Vectorstore not initialized.")

    # Optimized Retriever with prefixing
    base_retriever = _vectorstore.as_retriever(
        search_type="mmr", 
        search_kwargs={"k": TOP_K, "fetch_k": 20, "lambda_mult": 0.5}
        )
    retriever = RunnableLambda(lambda q: base_retriever.invoke(add_query_prefix(translate_query_if_needed(q))))

    # Ensure URL is clean and model is correct
    llm = ChatOllama(model=MODEL, base_url=OLLAMA_URL.rstrip("/"), temperature=0.0) 

    system = SYSTEM_PROMPT
    if zone_context:
        system += f"\n\nCurrent zone context: {zone_context}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{question}"),
    ])

    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

async def stream_answer(question: str, zone_context: str = "") -> AsyncIterator[str]:
    try:
        chain = build_chain(zone_context)
        async for token in chain.astream(question):
            yield token
    except Exception as e:
        yield f"⚠️ Error: {str(e)}"

if __name__ == "__main__":
    async def _test():
        # Corrected: sys.argv to get the actual string
        q = sys.argv if len(sys.argv) > 1 else "What is the flood evacuation protocol?"
        print(f"\n🔍 Testing RAG with: {q}\n")
        async for token in stream_answer(q):
            print(token, end="", flush=True)
        print("\n")

    asyncio.run(_test())