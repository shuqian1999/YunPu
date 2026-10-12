from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.core.database import get_db
import json
import csv
from io import StringIO


def _parse_date(value):
    """导出文件中的日期为 ISO 字符串；兼容已经是 date 或为空的情况"""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _parse_datetime(value):
    """导出文件中的时间为 ISO 字符串；兼容已经是 datetime 或为空"""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)

router = APIRouter(prefix="/data", tags=["数据管理"])


@router.get("/export/json")
async def export_data_json(
    db: Session = Depends(get_db)
):
    from app.models.person import Person
    from app.models.event import Event
    from app.models.event_type import EventType
    from app.models.reminder import Reminder
    from app.models.family_relation import FamilyRelation
    from app.models.spouse_relation import SpouseRelation
    from app.models.social_relation import SocialRelation, SocialRelationType

    persons = db.query(Person).all()
    events = db.query(Event).all()
    event_types = db.query(EventType).all()
    reminders = db.query(Reminder).all()
    family_relations = db.query(FamilyRelation).all()
    spouse_relations = db.query(SpouseRelation).all()
    social_relation_types = db.query(SocialRelationType).all()
    social_relations = db.query(SocialRelation).all()

    data = {
        "persons": [person.to_dict() for person in persons],
        "event_types": [
            {"id": t.id, "name": t.name, "color": t.color, "icon": t.icon}
            for t in event_types
        ],
        "events": [event.to_dict() for event in events],
        "reminders": [reminder.to_dict() for reminder in reminders],
        "family_relations": [relation.to_dict() for relation in family_relations],
        "spouse_relations": [relation.to_dict() for relation in spouse_relations],
        "social_relation_types": [t.to_dict() for t in social_relation_types],
        "social_relations": [relation.to_dict() for relation in social_relations],
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
    
    from app.models.person import Person
    from app.models.event import Event
    from app.models.event_type import EventType
    from app.models.reminder import Reminder
    from app.models.family_relation import FamilyRelation
    from app.models.spouse_relation import SpouseRelation
    from app.models.social_relation import SocialRelation, SocialRelationType
    from app.services.social_service import SocialService

    skipped = []

    # 1) 人物：保留 文件id -> 新库id 映射，供关系行重引用
    person_id_map = {}
    pending_persons = []
    for person_data in data.get("persons", []):
        old_id = person_data.get("id")
        person_data.pop('id', None)
        person_data.pop('created_at', None)
        person_data.pop('updated_at', None)
        person_data.pop('user_id', None)
        # to_dict 输出的是 ISO 字符串，Date/DateTime 列必须转回对象
        person_data['birth_date'] = _parse_date(person_data.get('birth_date'))
        person_data['death_date'] = _parse_date(person_data.get('death_date'))
        person_data['last_contact_at'] = _parse_datetime(person_data.get('last_contact_at'))
        person = Person(**person_data)
        db.add(person)
        pending_persons.append((old_id, person))
    db.flush()
    new_persons = {p.id: p for _, p in pending_persons}
    for old_id, person in pending_persons:
        if old_id is not None:
            person_id_map[old_id] = person.id
    persons_imported = len(pending_persons)

    # 2) 事件类型：按名称幂等（event_types.name 唯一），供事件/提醒重映射
    event_type_id_map = {}
    existing_event_types = {t.name: t for t in db.query(EventType).all()}
    event_types_created = 0
    event_types_reused = 0
    for et_data in data.get("event_types", []):
        old_id = et_data.get("id")
        name = (et_data.get("name") or "").strip()
        if not name:
            continue
        et = existing_event_types.get(name)
        if et is None:
            et = EventType(
                name=name,
                color=et_data.get("color") or "#409EFF",
                icon=et_data.get("icon"),
            )
            db.add(et)
            db.flush()
            existing_event_types[name] = et
            event_types_created += 1
        else:
            event_types_reused += 1
        if old_id is not None:
            event_type_id_map[old_id] = et.id
    valid_event_type_ids = {t.id for t in db.query(EventType).all()}

    def _resolve_event_type(old_id):
        """文件中的事件类型 id -> 新库 id；无法对应时降级为 None（事件保留、分类丢失）"""
        if old_id is None:
            return None
        if old_id in event_type_id_map:
            return event_type_id_map[old_id]
        return old_id if old_id in valid_event_type_ids else None

    # 3) 家庭关系（单向边 父母->子女）：历史 SON/DAUGHTER(2/3) 反向行按启动迁移同口径翻转；
    #    (新a,新b) 已存在则跳过，守护 uq_family_relations_pair
    existing_family_pairs = {
        (r.person_a_id, r.person_b_id)
        for r in db.query(FamilyRelation).all()
    }
    family_imported = 0
    for row in data.get("family_relations", []):
        label = f"家庭关系(文件id={row.get('id')})"
        a_id = person_id_map.get(row.get("person_a_id"))
        b_id = person_id_map.get(row.get("person_b_id"))
        relation = row.get("relation")
        nature = row.get("relation_nature", 0)
        if not a_id or not b_id:
            skipped.append(f"{label}：引用的人物缺失，已跳过")
            continue
        if relation in (2, 3):
            # 旧格式反向行：a 是子女、b 是父母；父母角色按父母性别（未知按父亲）
            child_id, parent_id = a_id, b_id
            parent = new_persons.get(parent_id)
            a_id, b_id, relation = parent_id, child_id, (1 if parent and parent.gender == 2 else 0)
        if relation not in (0, 1):
            skipped.append(f"{label}：关系类型无效，已跳过")
            continue
        if nature not in (0, 1, 2, 3, 4):
            skipped.append(f"{label}：关系性质无效，已跳过")
            continue
        if a_id == b_id:
            skipped.append(f"{label}：当事人不能为同一人，已跳过")
            continue
        if (a_id, b_id) in existing_family_pairs:
            skipped.append(f"{label}：同一对亲子关系已存在，已跳过")
            continue
        db.add(FamilyRelation(
            person_a_id=a_id, person_b_id=b_id,
            relation=relation, relation_nature=nature,
        ))
        existing_family_pairs.add((a_id, b_id))
        family_imported += 1

    # 4) 配偶关系：每段双行 (a,b,X)/(b,a,反向X) 原样重映射；
    #    全字段相同跳过，现任段额外守护部分唯一索引 uq_spouse_current_pair
    existing_spouse = db.query(SpouseRelation).all()
    spouse_identity = {
        (r.person_a_id, r.person_b_id, r.relation, r.relation_nature,
         r.start_date, r.end_date)
        for r in existing_spouse
    }
    spouse_current_pairs = {
        (r.person_a_id, r.person_b_id)
        for r in existing_spouse if r.relation_nature == 0
    }
    spouse_imported = 0
    # 旧备份中的男女朋友(relation 3/4)已改属社会关系，收集后在第 8 步统一转换
    lover_rows = []
    for row in data.get("spouse_relations", []):
        label = f"配偶关系(文件id={row.get('id')})"
        a_id = person_id_map.get(row.get("person_a_id"))
        b_id = person_id_map.get(row.get("person_b_id"))
        relation = row.get("relation")
        nature = row.get("relation_nature", 0)
        if not a_id or not b_id:
            skipped.append(f"{label}：引用的人物缺失，已跳过")
            continue
        if relation in (3, 4):
            if a_id == b_id:
                skipped.append(f"{label}：关系数据无效，已跳过")
                continue
            try:
                lover_start = _parse_date(row.get("start_date"))
                lover_end = _parse_date(row.get("end_date"))
            except (ValueError, TypeError):
                skipped.append(f"{label}：日期格式无效，已跳过")
                continue
            # 恋人是无向类型，3/4 双行与方向都归一化（去重在第 8b 步）
            lover_rows.append((a_id, b_id, lover_start, lover_end))
            continue
        if relation not in (0, 1, 2) or nature not in (0, 1) or a_id == b_id:
            skipped.append(f"{label}：关系数据无效，已跳过")
            continue
        try:
            start_date = _parse_date(row.get("start_date"))
            end_date = _parse_date(row.get("end_date"))
        except (ValueError, TypeError):
            skipped.append(f"{label}：日期格式无效，已跳过")
            continue
        if start_date and end_date and end_date < start_date:
            skipped.append(f"{label}：结束日期早于开始日期，已跳过")
            continue
        if nature == 0 and end_date is not None:
            skipped.append(f"{label}：现任段不能有结束日期，已跳过")
            continue
        key = (a_id, b_id, relation, nature, start_date, end_date)
        if key in spouse_identity:
            skipped.append(f"{label}：相同的配偶关系段已存在，已跳过")
            continue
        if nature == 0 and (a_id, b_id) in spouse_current_pairs:
            skipped.append(f"{label}：两人已有现任配偶段，已跳过")
            continue
        db.add(SpouseRelation(
            person_a_id=a_id, person_b_id=b_id,
            relation=relation, relation_nature=nature,
            start_date=start_date, end_date=end_date,
        ))
        spouse_identity.add(key)
        if nature == 0:
            spouse_current_pairs.add((a_id, b_id))
        spouse_imported += 1

    # 5) 事件：person_id 可空（全局事件）；非空但映射缺失则跳过
    events_imported = 0
    for ev in data.get("events", []):
        label = f"事件(文件id={ev.get('id')})"
        title = (ev.get("title") or "").strip()
        try:
            event_date = _parse_date(ev.get("event_date"))
        except (ValueError, TypeError):
            event_date = None
        if not title or event_date is None:
            skipped.append(f"{label}：标题或日期缺失，已跳过")
            continue
        old_pid = ev.get("person_id")
        person_id = None if old_pid is None else person_id_map.get(old_pid)
        if old_pid is not None and not person_id:
            skipped.append(f"{label}：引用的人物缺失，已跳过")
            continue
        db.add(Event(
            person_id=person_id,
            event_type_id=_resolve_event_type(ev.get("event_type_id")),
            title=title,
            description=ev.get("description"),
            event_date=event_date,
            is_lunar=bool(ev.get("is_lunar")),
            location=ev.get("location"),
        ))
        events_imported += 1

    # 6) 提醒：同事件口径
    reminders_imported = 0
    for rm in data.get("reminders", []):
        label = f"提醒(文件id={rm.get('id')})"
        title = (rm.get("title") or "").strip()
        try:
            remind_date = _parse_date(rm.get("remind_date"))
        except (ValueError, TypeError):
            remind_date = None
        if not title or remind_date is None:
            skipped.append(f"{label}：标题或提醒日期缺失，已跳过")
            continue
        old_pid = rm.get("person_id")
        person_id = None if old_pid is None else person_id_map.get(old_pid)
        if old_pid is not None and not person_id:
            skipped.append(f"{label}：引用的人物缺失，已跳过")
            continue
        db.add(Reminder(
            person_id=person_id,
            event_type_id=_resolve_event_type(rm.get("event_type_id")),
            title=title,
            description=rm.get("description"),
            remind_date=remind_date,
            is_lunar=bool(rm.get("is_lunar")),
            repeat_type=rm.get("repeat_type") or "once",
            enabled=bool(rm.get("enabled", True)),
            location=rm.get("location"),
            remind_advance_days=rm.get("remind_advance_days") or 0,
            trans_event=bool(rm.get("trans_event")),
        ))
        reminders_imported += 1

    # 7) 社会关系类型：按名称幂等——预设/已存在的同名类型直接复用，缺失才新建
    type_id_map = {}
    type_obj_map = {}
    existing_types = {t.name: t for t in db.query(SocialRelationType).all()}
    types_created = 0
    types_reused = 0
    # 无向「恋人」按需确保（旧配偶 3/4 行、过渡版有向「男朋友」备份都会并入它）
    def get_lover_type():
        t = existing_types.get("恋人")
        if t is not None:
            return t, False
        t = SocialRelationType(
            name="恋人", directed=0, reverse_name=None,
            color="#ff6b81", is_preset=1,
        )
        db.add(t)
        db.flush()
        existing_types["恋人"] = t
        return t, True

    for type_data in data.get("social_relation_types", []):
        old_id = type_data.get("id")
        name = (type_data.get("name") or "").strip()
        if not name:
            continue
        if name == "男朋友":
            # 过渡版本（有向「男朋友/女朋友」）导出的备份：并入无向「恋人」
            lover_t, lover_created = get_lover_type()
            if lover_created:
                types_created += 1
            else:
                types_reused += 1
            if old_id is not None:
                type_id_map[old_id] = lover_t.id
                type_obj_map[lover_t.id] = lover_t
            continue
        t = existing_types.get(name)
        if t is None:
            t = SocialRelationType(
                name=name,
                directed=1 if type_data.get("directed") else 0,
                reverse_name=type_data.get("reverse_name"),
                color=type_data.get("color") or "#fa8c16",
                is_preset=1 if type_data.get("is_preset") else 0,
            )
            db.add(t)
            db.flush()
            existing_types[name] = t
            types_created += 1
        else:
            types_reused += 1
        if old_id is not None:
            type_id_map[old_id] = t.id
            type_obj_map[t.id] = t

    # 8) 社会关系：当事人/类型/介绍人全部重映射到新库 id；
    #    复用 SocialService 的归一化与 7 条校验，失败的行跳过并记录
    service = SocialService(db)
    relations_imported = 0
    for rel_data in data.get("social_relations", []):
        label = f"社会关系(文件id={rel_data.get('id')})"
        type_id = type_id_map.get(rel_data.get("type_id"))
        a_id = person_id_map.get(rel_data.get("person_a_id"))
        b_id = person_id_map.get(rel_data.get("person_b_id"))
        if not type_id or not a_id or not b_id:
            skipped.append(f"{label}：引用的人物或类型缺失，已跳过")
            continue

        introducer_old = rel_data.get("introducer_id")
        introducer_id = (
            person_id_map.get(introducer_old) if introducer_old is not None else None
        )
        try:
            closeness = rel_data.get("closeness")
            start_date = _parse_date(rel_data.get("start_date"))
            end_date = _parse_date(rel_data.get("end_date"))
            norm_a, norm_b = service._validate_and_normalize(
                type_obj=type_obj_map[type_id],
                person_a_id=a_id,
                person_b_id=b_id,
                closeness=closeness,
                start_date=start_date,
                end_date=end_date,
                introducer_id=introducer_id,
            )
        except (ValueError, TypeError) as exc:
            skipped.append(f"{label}：{exc}")
            continue

        db.add(SocialRelation(
            person_a_id=norm_a,
            person_b_id=norm_b,
            type_id=type_id,
            closeness=closeness,
            start_date=start_date,
            end_date=end_date,
            introducer_id=introducer_id,
        ))
        relations_imported += 1

    # 8b) 旧备份的男女朋友配偶段：转为无向预设社会关系「恋人」
    lovers_converted = 0
    if lover_rows:
        lover_type, _created = get_lover_type()
        lover_existing = {
            (r.person_a_id, r.person_b_id, r.start_date, r.end_date)
            for r in db.query(SocialRelation).filter(
                SocialRelation.type_id == lover_type.id
            ).all()
        }
        lover_seen = set()
        for raw_a, raw_b, lover_start, lover_end in lover_rows:
            # 无向归一化（a<b），3/4 双行在此折叠
            norm_pair = sorted((raw_a, raw_b))
            key = (norm_pair[0], norm_pair[1], lover_start, lover_end)
            if key in lover_existing or key in lover_seen:
                continue
            try:
                norm_a, norm_b = service._validate_and_normalize(
                    type_obj=lover_type,
                    person_a_id=raw_a,
                    person_b_id=raw_b,
                    closeness=None,
                    start_date=lover_start,
                    end_date=lover_end,
                    introducer_id=None,
                )
            except (ValueError, TypeError) as exc:
                skipped.append(f"恋人关系：{exc}")
                continue
            db.add(SocialRelation(
                person_a_id=norm_a,
                person_b_id=norm_b,
                type_id=lover_type.id,
                closeness=None,
                start_date=lover_start,
                end_date=lover_end,
                introducer_id=None,
            ))
            lover_seen.add(key)
            lovers_converted += 1
        relations_imported += lovers_converted

    db.commit()

    total_skipped = len(skipped)
    message = (
        f"成功导入 {persons_imported} 位人物、{family_imported} 条家庭关系、"
        f"{spouse_imported} 条配偶关系、{relations_imported} 条社会关系、"
        f"{events_imported} 个事件、{reminders_imported} 个提醒"
    )
    if event_types_created or event_types_reused:
        message += f"（事件类型新建 {event_types_created} 个、复用 {event_types_reused} 个）"
    if types_created or types_reused:
        message += f"（社会关系类型新建 {types_created} 个、复用 {types_reused} 个）"
    if lovers_converted:
        message += f"；旧版男女朋友关系已自动转为「恋人」{lovers_converted} 条"
    if total_skipped:
        message += f"；{total_skipped} 条数据因问题被跳过，详见结果明细"
    return {
        "message": message,
        "persons_imported": persons_imported,
        "event_types_created": event_types_created,
        "event_types_reused": event_types_reused,
        "family_relations_imported": family_imported,
        "spouse_relations_imported": spouse_imported,
        "events_imported": events_imported,
        "reminders_imported": reminders_imported,
        "social_types_created": types_created,
        "social_types_reused": types_reused,
        "social_relations_imported": relations_imported,
        "lovers_converted": lovers_converted,
        "total_skipped": total_skipped,
        "skipped_details": skipped[:50],
    }