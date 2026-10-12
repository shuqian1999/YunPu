"""
社会关系服务（阶段2）

存储约定见 app.models.social_relation：
- 无向类型：归一化存储 (min_id, max_id)，双向都显示 type.name
- 有向类型：(a, b) = "a 是 b 的 type.name"；从 a 视角称对方用 reverse_name，
  从 b 视角称对方用 name
"""
from datetime import date as date_type
from typing import Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.social_relation import SocialRelation, SocialRelationType


class SocialService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _display_name(p: Person) -> str:
        full = f"{p.last_name or ''}{p.first_name or ''}".strip()
        return full or p.nickname or "未命名"

    def _get_type(self, type_id: int) -> SocialRelationType:
        t = self.db.query(SocialRelationType).filter(
            SocialRelationType.id == type_id
        ).first()
        if not t:
            raise ValueError("关系类型不存在")
        return t

    def _get_person(self, person_id: int) -> Person:
        p = self.db.query(Person).filter(Person.id == person_id).first()
        if not p:
            raise ValueError(f"人物不存在：{person_id}")
        return p

    # ------------------------------------------------------------------
    # 关系类型 CRUD
    # ------------------------------------------------------------------
    def list_types(self) -> List[Dict]:
        rows = self.db.query(SocialRelationType).order_by(
            SocialRelationType.is_preset.desc(), SocialRelationType.id
        ).all()
        result = []
        for t in rows:
            item = t.to_dict()
            item["relation_count"] = self.db.query(SocialRelation).filter(
                SocialRelation.type_id == t.id
            ).count()
            result.append(item)
        return result

    def create_type(
        self,
        name: str,
        directed: bool = False,
        reverse_name: Optional[str] = None,
        color: str = "#fa8c16",
    ) -> Dict:
        name = (name or "").strip()
        if not name:
            raise ValueError("关系类型名称不能为空")
        if len(name) > 20:
            raise ValueError("关系类型名称最长 20 个字")
        if self.db.query(SocialRelationType).filter(
            SocialRelationType.name == name
        ).first():
            raise ValueError(f"关系类型已存在：{name}")
        if directed and not (reverse_name or "").strip():
            raise ValueError("有向关系类型必须填写反向称谓（如：老师 / 学生）")

        t = SocialRelationType(
            name=name,
            directed=1 if directed else 0,
            reverse_name=reverse_name.strip() if directed else None,
            color=color or "#fa8c16",
            is_preset=0,
        )
        self.db.add(t)
        self.db.commit()
        self.db.refresh(t)
        item = t.to_dict()
        item["relation_count"] = 0
        return item

    def update_type(self, type_id: int, data: Dict) -> Dict:
        """data 为已 exclude_unset 的字段字典"""
        t = self._get_type(type_id)

        if "name" in data and data["name"] is not None:
            new_name = data["name"].strip()
            if not new_name:
                raise ValueError("关系类型名称不能为空")
            if new_name != t.name:
                dup = self.db.query(SocialRelationType).filter(
                    SocialRelationType.name == new_name,
                    SocialRelationType.id != type_id,
                ).first()
                if dup:
                    raise ValueError(f"关系类型已存在：{new_name}")
                t.name = new_name

        new_directed = t.directed
        if "directed" in data and data["directed"] is not None:
            new_directed = 1 if data["directed"] else 0

        new_reverse = t.reverse_name
        if "reverse_name" in data and data["reverse_name"] is not None:
            new_reverse = data["reverse_name"].strip() or None
        # directed 由 True 转 False 时反向称谓失去意义
        if new_directed == 0:
            new_reverse = None

        if new_directed != t.directed:
            in_use = self.db.query(SocialRelation).filter(
                SocialRelation.type_id == type_id
            ).count()
            if in_use:
                raise ValueError("该类型下已有关系记录，不能改变其有向/无向属性")
            if new_directed == 1 and not new_reverse:
                raise ValueError("有向关系类型必须填写反向称谓（如：老师 / 学生）")
            t.directed = new_directed
        t.reverse_name = new_reverse

        if "color" in data and data["color"]:
            t.color = data["color"]

        self.db.commit()
        self.db.refresh(t)
        item = t.to_dict()
        item["relation_count"] = self.db.query(SocialRelation).filter(
            SocialRelation.type_id == t.id
        ).count()
        return item

    def delete_type(self, type_id: int):
        t = self._get_type(type_id)
        if t.is_preset:
            raise ValueError("预设关系类型不能删除（可改名后使用）")
        in_use = self.db.query(SocialRelation).filter(
            SocialRelation.type_id == type_id
        ).count()
        if in_use:
            raise ValueError(f"该类型下还有 {in_use} 条关系，请先删除相关关系")
        self.db.delete(t)
        self.db.commit()

    # ------------------------------------------------------------------
    # 关系实例 CRUD
    # ------------------------------------------------------------------
    def list_for_person(self, person_id: int) -> List[Dict]:
        self._get_person(person_id)
        rows = self.db.query(SocialRelation).filter(
            or_(
                SocialRelation.person_a_id == person_id,
                SocialRelation.person_b_id == person_id,
            )
        ).all()

        type_ids = {r.type_id for r in rows}
        other_ids = set()
        introducer_ids = set()
        for r in rows:
            other_ids.add(
                r.person_b_id if r.person_a_id == person_id else r.person_a_id
            )
            if r.introducer_id:
                introducer_ids.add(r.introducer_id)
        people = {
            p.id: p for p in self.db.query(Person).filter(
                Person.id.in_(list(other_ids | introducer_ids | {person_id}))
            ).all()
        } if (other_ids or introducer_ids) else {}
        types = {
            t.id: t for t in self.db.query(SocialRelationType).filter(
                SocialRelationType.id.in_(list(type_ids))
            ).all()
        } if type_ids else {}

        result = []
        for r in rows:
            t = types.get(r.type_id)
            if not t:
                continue
            other_id = (
                r.person_b_id if r.person_a_id == person_id else r.person_a_id
            )
            other = people.get(other_id)
            if not other:
                continue

            if not t.directed:
                direction = "none"
                relation_name = t.name
            elif r.person_a_id == person_id:
                # 我是对方的 type.name（我是老师）→ 对方是我的 reverse_name（学生）
                direction = "forward"
                relation_name = t.reverse_name or t.name
            else:
                # 对方是我的 type.name（老师）
                direction = "reverse"
                relation_name = t.name

            introducer = None
            if r.introducer_id and r.introducer_id in people:
                introducer = {
                    "id": r.introducer_id,
                    "name": self._display_name(people[r.introducer_id]),
                }

            result.append({
                "relation_id": r.id,
                "other": {"id": other.id, "name": self._display_name(other)},
                "type": {
                    "id": t.id,
                    "name": t.name,
                    "reverse_name": t.reverse_name,
                    "directed": t.directed,
                    "color": t.color,
                },
                "direction": direction,
                "relation_name": relation_name,
                "closeness": r.closeness,
                "start_date": r.start_date.isoformat() if r.start_date else None,
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "introducer": introducer,
            })

        # 进行中在前 → 亲密度高在前 → 开始日新在前 → id
        result.sort(key=lambda x: (
            0 if x["end_date"] is None else 1,
            -(x["closeness"] or 0),
            x["start_date"] is None,
            x["relation_id"],
        ))
        return result

    def _validate_and_normalize(
        self,
        *,
        type_obj: SocialRelationType,
        person_a_id: int,
        person_b_id: int,
        closeness: Optional[int],
        start_date: Optional[date_type],
        end_date: Optional[date_type],
        introducer_id: Optional[int],
        exclude_relation_id: Optional[int] = None,
    ):
        """全部校验通过后返回归一化的 (a_id, b_id)"""
        if person_a_id == person_b_id:
            raise ValueError("不能与自己建立关系")
        self._get_person(person_a_id)
        self._get_person(person_b_id)

        if closeness is not None and not (1 <= closeness <= 5):
            raise ValueError("亲密度必须在 1-5 之间")

        if start_date and end_date and end_date < start_date:
            raise ValueError("关系结束日期不能早于开始日期")

        if introducer_id is not None:
            self._get_person(introducer_id)
            if introducer_id in (person_a_id, person_b_id):
                raise ValueError("介绍人不能是关系当事人本人")

        # 无向归一化；有向保留输入方向
        if type_obj.directed:
            a_id, b_id = person_a_id, person_b_id
        else:
            a_id, b_id = sorted((person_a_id, person_b_id))

        # 同两人同类型的既有段（排除自身）
        q = self.db.query(SocialRelation).filter(
            SocialRelation.type_id == type_obj.id
        )
        if type_obj.directed:
            q = q.filter(
                SocialRelation.person_a_id == a_id,
                SocialRelation.person_b_id == b_id,
            )
        else:
            q = q.filter(
                or_(
                    (SocialRelation.person_a_id == a_id)
                    & (SocialRelation.person_b_id == b_id),
                    (SocialRelation.person_a_id == b_id)
                    & (SocialRelation.person_b_id == a_id),
                )
            )
        if exclude_relation_id is not None:
            q = q.filter(SocialRelation.id != exclude_relation_id)
        existing = q.all()

        for r in existing:
            if r.start_date == start_date and r.end_date == end_date:
                raise ValueError("完全相同的社会关系已存在，请勿重复添加")
            if end_date is None and r.end_date is None:
                raise ValueError("两人的这一关系已有一条进行中的记录")
            # 时间区间重叠（双方四日期齐全才判断；半开区间）
            if r.start_date and r.end_date and start_date and end_date:
                if start_date <= r.end_date and r.start_date <= end_date:
                    raise ValueError("新关系的时间区间与已有记录重叠")

        return a_id, b_id

    def create_relation(
        self,
        person_a_id: int,
        person_b_id: int,
        type_id: int,
        closeness: Optional[int] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
        introducer_id: Optional[int] = None,
    ) -> Dict:
        t = self._get_type(type_id)
        a_id, b_id = self._validate_and_normalize(
            type_obj=t,
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            closeness=closeness,
            start_date=start_date,
            end_date=end_date,
            introducer_id=introducer_id,
        )
        rel = SocialRelation(
            person_a_id=a_id,
            person_b_id=b_id,
            type_id=type_id,
            closeness=closeness,
            start_date=start_date,
            end_date=end_date,
            introducer_id=introducer_id,
        )
        self.db.add(rel)
        self.db.commit()
        self.db.refresh(rel)
        return rel.to_dict()

    def update_relation(self, relation_id: int, data: Dict) -> Dict:
        """data 为已 exclude_unset 的字段字典（显式传 null 可清空可空字段）"""
        rel = self.db.query(SocialRelation).filter(
            SocialRelation.id == relation_id
        ).first()
        if not rel:
            raise ValueError("关系记录不存在")

        type_id = data.get("type_id", rel.type_id)
        t = self._get_type(type_id)
        a_in = data.get("person_a_id", rel.person_a_id)
        b_in = data.get("person_b_id", rel.person_b_id)
        closeness = data.get("closeness", rel.closeness)
        start_date = data.get("start_date", rel.start_date)
        end_date = data.get("end_date", rel.end_date)
        introducer_id = data.get("introducer_id", rel.introducer_id)

        a_id, b_id = self._validate_and_normalize(
            type_obj=t,
            person_a_id=a_in,
            person_b_id=b_in,
            closeness=closeness,
            start_date=start_date,
            end_date=end_date,
            introducer_id=introducer_id,
            exclude_relation_id=relation_id,
        )

        rel.type_id = type_id
        rel.person_a_id = a_id
        rel.person_b_id = b_id
        rel.closeness = closeness
        rel.start_date = start_date
        rel.end_date = end_date
        rel.introducer_id = introducer_id
        self.db.commit()
        self.db.refresh(rel)
        return rel.to_dict()

    def delete_relation(self, relation_id: int):
        rel = self.db.query(SocialRelation).filter(
            SocialRelation.id == relation_id
        ).first()
        if not rel:
            raise ValueError("关系记录不存在")
        self.db.delete(rel)
        self.db.commit()
