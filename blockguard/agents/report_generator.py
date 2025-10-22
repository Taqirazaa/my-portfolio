from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence, Optional, List, Dict, Any
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional
    ChatOpenAI = None  # type: ignore

from fastembed import TextEmbedding

from blockguard.config import settings
from blockguard.schemas.audit import AuditFindingOut


SYSTEM_PROMPT = """
You are BlockGuard's ReportGenerator. Summarize audit findings clearly for compliance teams.
Provide an executive summary, key findings (with severities), and recommended next steps.
Keep it concise and actionable.
"""


class _FastEmbedEmbeddings(Embeddings):
    """LangChain Embeddings wrapper around fastembed.TextEmbedding."""

    def __init__(self, model_name: str) -> None:
        self._embedder = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [list(vec) for vec in self._embedder.embed(texts)]

    def embed_query(self, text: str) -> List[float]:
        return list(next(iter(self._embedder.embed([text]))))


@dataclass
class ReportGenerator:
    name: str = "ReportGenerator"
    vectorstore_dir: Optional[str] = None
    knowledge_base_dir: Optional[str] = None
    embedding_model: Optional[str] = None
    llm_model_name: str = "gpt-4o-mini"

    def __post_init__(self) -> None:
        self.vectorstore_dir = self.vectorstore_dir or settings.vectorstore_dir
        self.knowledge_base_dir = self.knowledge_base_dir or settings.knowledge_base_dir
        self.embedding_model = self.embedding_model or settings.embedding_model
        self._embeddings = _FastEmbedEmbeddings(self.embedding_model)
        self._vectorstore: Optional[FAISS] = None
        self.prompt = ChatPromptTemplate.from_template(
            """
{system}

Context:
{context}

Findings:
{findings}

Write a concise markdown report.
            """
        )

    # --- New public API ---
    def load_vectorstore(self) -> None:
        """Load a local FAISS index; build from knowledge base if missing."""
        vs_path = Path(self.vectorstore_dir)
        vs_path.mkdir(parents=True, exist_ok=True)
        index_file = vs_path / "index.faiss"
        store_file = vs_path / "index.pkl"
        if index_file.exists() and store_file.exists():
            # Load existing
            self._vectorstore = FAISS.load_local(
                self.vectorstore_dir, self._embeddings, allow_dangerous_deserialization=True
            )
            return

        # Build from knowledge base
        kb = Path(self.knowledge_base_dir)
        documents: List[Document] = []
        if kb.exists():
            splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
            files: List[Path] = []
            files.extend(kb.rglob("*.md"))
            files.extend(kb.rglob("*.mdx"))
            files.extend(kb.rglob("*.txt"))
            for f in files:
                try:
                    text = f.read_text(encoding="utf-8")
                except Exception:
                    continue
                for chunk in splitter.split_text(text):
                    documents.append(Document(page_content=chunk, metadata={"source": str(f)}))

        if not documents:
            documents = [Document(page_content="BlockGuard initialization document.")]

        self._vectorstore = FAISS.from_documents(documents, self._embeddings)
        self._vectorstore.save_local(self.vectorstore_dir)

    def generate_report(self, tx_data: Sequence[Dict[str, Any]] | Dict[str, Any], context: str = "") -> str:
        """Generate a markdown audit report using an LLM.

        If OPENAI_API_KEY is not set, falls back to a templated summary.
        """
        if self._vectorstore is None:
            self.load_vectorstore()

        # Retrieve additional context if none was provided
        if not context and self._vectorstore is not None:
            docs = self._vectorstore.similarity_search("blockchain compliance risk controls", k=4)
            context = "\n\n".join(doc.page_content for doc in docs)

        if isinstance(tx_data, dict):
            items = [tx_data]
        else:
            items = list(tx_data)
        tx_text = "\n".join(f"- tx {d.get('tx_hash') or d.get('tx_id')}: {d}" for d in items)

        messages = self.prompt.format_messages(system=SYSTEM_PROMPT, context=context, findings=tx_text)

        # Use OpenAI LLM if key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if ChatOpenAI is not None and api_key:
            llm = ChatOpenAI(model=self.llm_model_name, temperature=0.2)
            resp = llm.invoke(messages)
            return getattr(resp, "content", str(resp))

        # Fallback: assemble a deterministic report without external calls
        return (
            "# BlockGuard Audit Report\n\n" + "\n\n".join(m.content if hasattr(m, "content") else str(m) for m in messages)
        )

    # --- Back-compat for orchestrator ---
    async def run(self, findings: Sequence[AuditFindingOut]) -> str:  # pragma: no cover - thin wrapper
        items = [
            {
                "tx_hash": f.transaction_id,
                "finding_type": f.finding_type,
                "rule_name": f.rule_name,
                "severity": f.severity,
                "score": f.score,
                "details": f.details,
            }
            for f in findings
        ]
        return self.generate_report(items, context="")
