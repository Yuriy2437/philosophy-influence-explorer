"""Provider-independent interface for structured answer generation."""

from __future__ import annotations

from typing import Protocol

from philosophy_influence_explorer.generation.contracts import GroundedAnswer
from philosophy_influence_explorer.workflows.evidence import EvidencePacket


class AnswerGenerator(Protocol):
    """Generate an answer using the supplied question and evidence."""

    def generate(
        self,
        *,
        query_text: str,
        evidence: EvidencePacket,
    ) -> GroundedAnswer:
        """Return structured output or raise an error."""
        ...
