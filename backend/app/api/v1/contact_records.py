from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.contact_record import ContactRecord
from app.models.person import Person
from app.schemas.contact_record import (
    ContactRecordCreate,
    ContactRecordUpdate,
    ContactRecordResponse,
    CONTACT_TYPES,
)

router = APIRouter(prefix="/contact-records", tags=["交往记录"])


def _sync_last_contact(db: Session, person_id: int):
    """根据人物的全部交往记录，重算最近联系时间并写回 Person。"""
    latest_date = db.query(sa_func.max(ContactRecord.contact_date)).filter(
        ContactRecord.person_id == person_id
    ).scalar()

    person = db.query(Person).filter(Person.id == person_id).first()
    if person:
        person.last_contact_at = (
            datetime.combine(latest_date, datetime.min.time()) if latest_date else None
        )


@router.get("", response_model=List[ContactRecordResponse])
def list_contact_records(
    person_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(ContactRecord)
    if person_id:
        query = query.filter(ContactRecord.person_id == person_id)

    records = (
        query.order_by(ContactRecord.contact_date.desc(), ContactRecord.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return records


@router.post("", response_model=ContactRecordResponse, status_code=status.HTTP_201_CREATED)
def create_contact_record(
    payload: ContactRecordCreate,
    db: Session = Depends(get_db),
):
    if payload.contact_type not in CONTACT_TYPES:
        raise HTTPException(status_code=400, detail="无效的互动方式")

    person = db.query(Person).filter(Person.id == payload.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="人物不存在")

    record = ContactRecord(**payload.model_dump())
    db.add(record)
    db.flush()
    _sync_last_contact(db, payload.person_id)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{record_id}", response_model=ContactRecordResponse)
def update_contact_record(
    record_id: int,
    payload: ContactRecordUpdate,
    db: Session = Depends(get_db),
):
    record = db.query(ContactRecord).filter(ContactRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="交往记录不存在")

    data = payload.model_dump(exclude_unset=True)
    if "contact_type" in data and data["contact_type"] not in CONTACT_TYPES:
        raise HTTPException(status_code=400, detail="无效的互动方式")

    affected_persons = {record.person_id}
    if "person_id" in data and data["person_id"] is not None:
        new_person = db.query(Person).filter(Person.id == data["person_id"]).first()
        if not new_person:
            raise HTTPException(status_code=404, detail="人物不存在")
        affected_persons.add(data["person_id"])

    for key, value in data.items():
        setattr(record, key, value)

    db.flush()
    for pid in affected_persons:
        _sync_last_contact(db, pid)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    record = db.query(ContactRecord).filter(ContactRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="交往记录不存在")

    person_id = record.person_id
    db.delete(record)
    db.flush()
    _sync_last_contact(db, person_id)
    db.commit()
