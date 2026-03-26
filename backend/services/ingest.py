import sys
from pathlib import Path
from typing import List

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

MARKDOWN_DIR  = Path("/app/data/markdown")
CHROMA_DIR    = Path("/app/data/chroma")
COLLECTION    = "climarisk_docs"
EMBED_MODEL   = "intfloat/multilingual-e5-large"
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 150


def load_documents() -> List[Document]:
    loader = DirectoryLoader(
        str(MARKDOWN_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    return loader.load()


def split_documents(docs: List[Document]) -> List[Document]:
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#",   "header_1"),
            ("##",  "header_2"),
            ("###", "header_3"),
        ],
        strip_headers=False,
    )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )

    all_chunks = []
    for doc in docs:
        header_chunks = header_splitter.split_text(doc.page_content)
        for chunk in header_chunks:
            sub_chunks = text_splitter.create_documents(
                [chunk.page_content],
                metadatas=[{**doc.metadata, **chunk.metadata}],
            )
            all_chunks.extend(sub_chunks)

    return all_chunks


def add_passage_prefix(docs: List[Document]) -> List[Document]:

    for doc in docs:
        doc.page_content = "passage: " + doc.page_content
    return docs


def main():
    md_files = list(MARKDOWN_DIR.glob("*.md"))
    if not md_files:
        print(f"⚠️  No markdown files in {MARKDOWN_DIR}")
        print("Run python services/pdf_to_markdown.py first.")
        sys.exit(0)

    print(f"\n📚 Found {len(md_files)} markdown file(s)\n")

    print("⏳ Loading multilingual-e5-large (first run downloads ~560MB)...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print("✅ Embedding model ready\n")

    print("📄 Loading documents...")
    docs = load_documents()
    print(f"   {len(docs)} document(s) loaded")

    print("✂️  Splitting into chunks...")
    chunks = split_documents(docs)
    print(f"   {len(chunks)} chunks")

    print("🏷️  Adding passage prefixes...")
    chunks = add_passage_prefix(chunks)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    print("🧮 Embedding + storing in ChromaDB...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION,
    )

    print(f"\n{'='*50}")
    print(f"✅ Stored {len(chunks)} chunks")
    print(f"📁 ChromaDB : {CHROMA_DIR}")
    print(f"🗂️  Collection: {COLLECTION}")
    print(f"\nRAG system is ready!")


if __name__ == "__main__":
    main()