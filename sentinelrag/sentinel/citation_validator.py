from __future__ import annotations

import re
from typing import List

from .models import Document


def validate_citations(answer: str, evidence: List[Document]) -> str:
    """Strips any [DOC-xxx]-style citation that does not correspond to a
    document actually present in the authorized evidence supplied for
    this call. Guards against the model hallucinating a citation or
    referencing a document it never actually saw.

    Shared by both the deterministic answer path and the agentic loop --
    citation validation must not diverge between them.
    """
    valid_ids = {d.document_id for d in evidence}
    cited_ids = set(re.findall(r"\[([A-Za-z0-9\-]+)\]", answer))
    for bad_id in cited_ids - valid_ids:
        answer = answer.replace(f"[{bad_id}]", "[unverified citation removed]")
    return answer
