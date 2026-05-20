from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
import json
import csv
from io import StringIO

router = APIRouter(prefix="/data", tags=["数据管理"])


@router.get("/export/json")
async def export_data_json(
    db: Session = Depends(get_db)
):
    from app.models.person import Person
    from app.models.event import Event
    from app.models.reminder import Reminder
    from app.models.family_relation import FamilyRelation
    from app.models.spouse_relation import SpouseRelation
    
    persons = db.query(Person).all()
    events = db.query(Event).all()
    reminders = db.query(Reminder).all()
    family_relations = db.query(FamilyRelation).all()
    spouse_relations = db.query(SpouseRelation).all()
    
    data = {
        "persons": [person.to_dict() for person in persons],
        "events": [event.to_dict() for event in events],
        "reminders": [reminder.to_dict() for reminder in reminders],
        "family_relations": [relation.to_dict() for relation in family_relations],
        "spouse_relations": [relation.to_dict() for relation in spouse_relations],
        "exported_at": datetime.now().isoformat()
    }
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    return StreamingResponse(
        StringIO(json_str),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=yunpu_data.json"}
    )


@router.get("/export/csv")
async def export_data_csv(
    db: Session = Depends(get_db)
):
    from app.models.person import Person
    
    persons = db.query(Person).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["ID", "姓名", "昵称", "性别", "出生日期", "逝世日期", "国家", "故乡", "现居地"])
    
    for person in persons:
        writer.writerow([
            person.id,
            f"{person.first_name or ''}{person.last_name or ''}",
            person.nickname or "",
            person.gender or "",
            person.birth_date.isoformat() if person.birth_date else "",
            person.death_date.isoformat() if person.death_date else "",
            person.country or "",
            person.hometown or "",
            person.residence or ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=yunpu_persons.csv"}
    )


@router.post("/import/json")
async def import_data_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的JSON文件")
    
    imported_count = 0
    
    for person_data in data.get("persons", []):
        from app.models.person import Person
        person_data.pop('id', None)
        person_data.pop('created_at', None)
        person_data.pop('updated_at', None)
        person_data.pop('user_id', None)
        person = Person(**person_data)
        db.add(person)
        imported_count += 1
    
    db.commit()
    
    return {"message": f"成功导入 {imported_count} 条数据"}