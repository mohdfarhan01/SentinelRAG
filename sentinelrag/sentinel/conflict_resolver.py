from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from .models import Document


@dataclass
class ConflictGroup:
    title: str
    current: List[Document]
    superseded: List[Document]


class ConflictResolver:
    """Deterministic. Operates ONLY on documents that already passed the
    Authorization Gatekeeper -- it never sees, and cannot leak, anything
    the user is not authorized to access.

    Groups authorized documents by title (their logical document family)
    and picks the version with the latest effective_date that has already
    taken effect. Two authorized, equally current documents that disagree
    are a genuine conflict -- resolved does NOT guess between them; both
    are surfaced so the answer stage can disclose the disagreement honestly.
    """

    def __init__(self) -> None:
        self.last_superseded: List[Document] = []
        self.last_conflicts: List[ConflictGroup] = []

    def resolve(self, authorized_docs: List[Document], today: Optional[date] = None) -> List[Document]:
        today = today or date.today()
        self.last_superseded = []
        self.last_conflicts = []

        groups: Dict[str, List[Document]] = {}
        for doc in authorized_docs:
            groups.setdefault(doc.title, []).append(doc)

        resolved: List[Document] = []

        for title, docs in groups.items():
            applicable = [d for d in docs if d.status == "active" and d.effective_date_obj <= today]
            if not applicable:
                continue

            latest_date = max(d.effective_date_obj for d in applicable)
            current = [d for d in applicable if d.effective_date_obj == latest_date]
            superseded = [d for d in applicable if d.effective_date_obj < latest_date]
            self.last_superseded.extend(superseded)

            if len(current) > 1:
                # Same effective date, disagreeing content: not something a
                # date comparison can resolve. Surface both rather than
                # silently pick one.
                self.last_conflicts.append(ConflictGroup(title, current, superseded))
                resolved.extend(current)
            else:
                resolved.append(current[0])

        return resolved
