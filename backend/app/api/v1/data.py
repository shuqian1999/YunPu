from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
import json
import csv
from io import StringIO

router = APIRouter(prefix="/data", tags=["数据管理"])


@router.get("/export/json")
async def export_data_json(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.person import Person
    from app.models.event import Event
    from app.models.reminder import Reminder
    from app.models.family_member import FamilyMember
    from app.models.family_relation import FamilyRelation
    
    persons = db.query(Person).filter(Person.user_id == current_user.id).all()
    events = db.query(Event).filter(Event.user_id == current_user.id).all()
    reminders = db.query(Reminder).filter(Reminder.user_id == current_user.id).all()
    family_members = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).all()
    family_relations = db.query(FamilyRelation).filter(FamilyRelation.user_id == current_user.id).all()
    
    data = {
        "persons": [person.to_dict() for person in persons],
        "events": [event.to_dict() for event in events],
        "reminders": [reminder.to_dict() for reminder in reminders],
        "family_members": [member.to_dict() for member in family_members],
        "family_relations": [relation.to_dict() for relation in family_relations],
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.person import Person
    
    persons = db.query(Person).filter(Person.user_id == current_user.id).all()
    
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
    current_user: User = Depends(get_current_user),
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
        # 移除可能存在的id字段，让数据库自动生成
        person_data.pop('id', None)
        person_data.pop('created_at', None)
        person_data.pop('updated_at', None)
        person = Person(**person_data, user_id=current_user.id)
        db.add(person)
        imported_count += 1
    
    db.commit()
    
    return {"message": f"成功导入 {imported_count} 条数据"}