from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class ToolContext:
    db: Session
