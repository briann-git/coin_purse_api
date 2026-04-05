# helpers/kinds.py
from fastapi import HTTPException
from sqlalchemy.orm import Session

from helpers.db_utils import active_query
from models.models import TransactionKind


def resolve_kind_id_or_400(db: Session, kind_name: str):
    kind = active_query(db, TransactionKind).filter(TransactionKind.name == kind_name).first()
    if not kind:
        raise HTTPException(status_code=400, detail=f"Invalid transaction kind: {kind_name}")
    return kind.id
