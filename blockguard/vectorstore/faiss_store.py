from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastembed import TextEmbedding

from blockguard.config import settings


class VectorStore:
    def __init__(self, persist_dir: str | None = None, embedding_model: str | None = None) -> None:
        self.persist_dir = persist_dir or settings.vectorstore_dir
        self.embedding_model_name = embedding_model or settings.embedding_model
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self._embedder = TextEmbedding(model_name=self.embedding_model_name)
        self._vectorstore: FAISS | None = None

    def _ensure_store(self) -> FAISS:
        if self._vectorstore is not None:
            return self._vectorstore
        # Initialize an empty FAISS store
        # LangChain FAISS expects a callable that maps List[str] -> List[Embedding]
        def _embed(texts: list[str]) -> list[list[float]]:
            return [list(vec) for vec in self._embedder.embed(texts)]

        self._vectorstore = FAISS.from_texts(["BlockGuard initialization"], embedding=_embed)
        return self._vectorstore

    def add_texts(self, texts: Iterable[str], metadatas: Iterable[dict] | None = None) -> None:
        store = self._ensure_store()
        docs = [Document(page_content=t, metadata=(m or {})) for t, m in zip(texts, metadatas or [])]
        store.add_documents(docs)

    def add_documents_from_dir(self, directory: str | None = None, chunk_size: int = 800, chunk_overlap: int = 120) -> int:
        directory = directory or settings.knowledge_base_dir
        path = Path(directory)
        if not path.exists():
            return 0
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        documents: List[Document] = []
        for file in path.rglob("*.{md,txt,mdx}"):
            text = file.read_text(encoding="utf-8")
            for chunk in splitter.split_text(text):
                documents.append(Document(page_content=chunk, metadata={"source": str(file)}))
        if not documents:
            return 0
        store = self._ensure_store()
        store.add_documents(documents)
        return len(documents)

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        store = self._ensure_store()
        return store.similarity_search(query, k=k)
