"""Explicit instruction variants for fixed-evidence evaluation only."""

from __future__ import annotations

from philosophy_influence_explorer.generation.gemini import SYSTEM_INSTRUCTION

BASELINE_INSTRUCTION_ID = "baseline"
CANDIDATE_INSTRUCTION_ID = "semantic-fidelity-v1"

INSTRUCTION_IDS = (
    BASELINE_INSTRUCTION_ID,
    CANDIDATE_INSTRUCTION_ID,
)

SEMANTIC_FIDELITY_ADDITION = (
    "Preserve the logical relationships and scope expressed in the passages, "
    "including negation, contrasts, conditions, and qualifications. "
    "Do not replace a relationship with a different one merely because "
    "the wording sounds similar. "
    "When explaining a rule or principle, distinguish what the passage "
    "establishes from what it leaves undecided. "
    "If the question requires a conclusion that the passage does not establish, "
    "state that limitation explicitly rather than implying that the supported "
    "point settles the whole question."
)


def resolve_system_instruction(instruction_id: str) -> str:
    """Resolve a known evaluation variant without external services."""
    if instruction_id == BASELINE_INSTRUCTION_ID:
        return SYSTEM_INSTRUCTION

    if instruction_id == CANDIDATE_INSTRUCTION_ID:
        return SYSTEM_INSTRUCTION + "\n\n" + SEMANTIC_FIDELITY_ADDITION

    raise ValueError("Unknown evaluation instruction ID.")
