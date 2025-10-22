from __future__ import annotations

from typing import Sequence
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate

from blockguard.vectorstore.faiss_store import VectorStore
from blockguard.schemas.audit import AuditFindingOut


SYSTEM_PROMPT = """
You are BlockGuard's ReportGenerator. Summarize audit findings clearly for compliance teams.
Provide an executive summary, key findings (with severities), and recommended next steps.
"""


@dataclass
class ReportGenerator:
    name: str = "ReportGenerator"

    def __post_init__(self) -> None:
        self.vs = VectorStore()
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

    async def run(self, findings: Sequence[AuditFindingOut]) -> str:
        # Retrieve supportive context
        context_docs = self.vs.similarity_search("blockchain compliance risk controls", k=4)
        context_text = "\n\n".join(doc.page_content for doc in context_docs)

        findings_text = "\n".join(
            f"- [{f.severity.upper()}] {f.finding_type} {f.rule_name or ''} for tx {f.transaction_id} (score={f.score})"
            for f in findings
        )

        prompt = self.prompt.format_messages(system=SYSTEM_PROMPT, context=context_text, findings=findings_text)
        # Placeholder: in real system, call an LLM. Here we just assemble a report string.
        report = (
            "# BlockGuard Audit Report\n\n" + "\n\n".join(m.content if hasattr(m, "content") else str(m) for m in prompt)
        )
        return report
