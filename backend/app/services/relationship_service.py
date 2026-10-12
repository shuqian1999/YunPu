"""
通用关系图谱服务（不限定家族范围）

汇聚五类一级关系边：
- family  亲子（父母 -> 子女，去重，非亲生虚线）
- spouse  配偶/伴侣（无向去重，前任虚线）
- social  社会关系（朋友/同事/师生等；有向带箭头，过期段虚线，线宽映射亲密度）
- group   同分组（按分组成对，标注分组名/颜色）
- tag     同标签（按标签成对，标注标签名/颜色）

全局图只包含"直接关系"边，且对社会关系及同组/同标签这类可能膨胀的边设置总量上限。
"""
from typing import Dict, List, Optional, Set
from collections import defaultdict

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.family_relation import FamilyRelation
from app.models.spouse_relation import SpouseRelation
from app.models.social_relation import SocialRelation, SocialRelationType
from app.models.person_group import PersonGroup, PersonGroupMember
from app.models.tag import Tag, PersonTag
from app.models.enums.relation_enums import (
    FamilyRelationType, NATURE_LABELS, SPOUSE_ROLE_LABELS,
)
from app.services.family_service import FamilyService

# 同组/同标签边可能组合爆炸，设置保护性上限（亲属/配偶边不计入截断）
MAX_CLUSTER_EDGES = 1500
# 社会关系边保护性上限
MAX_SOCIAL_EDGES = 2000
# ego 环图社会扇区邻居上限
SOCIAL_NEIGHBOR_CAP = 100

# 各类关系的展示色（前端也有同口径常量，保持一致）
COLOR_FAMILY = "#8a94a6"
COLOR_FAMILY_NONBLOOD = "#b6bac2"
COLOR_SPOUSE = "#f56c6c"
COLOR_SPOUSE_EX = "#e6b8bc"
COLOR_SOCIAL = "#fa8c16"
COLOR_GROUP = "#13c2c2"
COLOR_TAG = "#722ed1"


class RelationshipService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 全局关系图
    # ------------------------------------------------------------------
    def get_graph(
        self,
        edge_types: Optional[List[str]] = None,
        importance_min: int = 0,
        alive_only: bool = False,
        keyword: Optional[str] = None
    ) -> Dict:
        types = set(edge_types) if edge_types else {"family", "spouse", "social", "group"}

        # 1) 基础人物集合（节点候选）
        q = self.db.query(Person)
        if importance_min and importance_min > 0:
            q = q.filter(Person.importance >= importance_min)
        if alive_only:
            q = q.filter(Person.death_date.is_(None))
        if keyword:
            like = f"%{keyword.strip()}%"
            q = q.filter(or_(
                Person.first_name.like(like),
                Person.last_name.like(like),
                Person.nickname.like(like)
            ))
        persons = q.all()
        allowed_ids: Set[int] = {p.id for p in persons}

        edges: List[Dict] = []
        truncated = False

        def pair_allowed(a: int, b: int) -> bool:
            return a in allowed_ids and b in allowed_ids

        # 2) 亲属边（父母 -> 子女）
        if "family" in types:
            rels = self.db.query(FamilyRelation).filter(
                FamilyRelation.relation.in_([
                    FamilyRelationType.FATHER,
                    FamilyRelationType.MOTHER
                ])
            ).all()
            for rel in rels:
                if not pair_allowed(rel.person_a_id, rel.person_b_id):
                    continue
                nonblood = rel.relation_nature != 0
                edges.append({
                    "id": f"f-{rel.id}",
                    "source": rel.person_a_id,
                    "target": rel.person_b_id,
                    "edge_type": "family",
                    "nature": rel.relation_nature,
                    "nature_label": NATURE_LABELS.get(rel.relation_nature, "亲"),
                    "dashed": nonblood,
                    "label": "" if not nonblood else NATURE_LABELS.get(rel.relation_nature, ""),
                    "color": COLOR_FAMILY_NONBLOOD if nonblood else COLOR_FAMILY
                })

        # 3) 配偶边（无向；按段去重，复婚可有多条）
        if "spouse" in types:
            seg_best = {}
            rels = self.db.query(SpouseRelation).all()
            for rel in rels:
                a, b = rel.person_a_id, rel.person_b_id
                if not pair_allowed(a, b):
                    continue
                pair = (a, b) if a < b else (b, a)
                key = (
                    pair,
                    rel.relation_nature,
                    rel.start_date.isoformat() if rel.start_date else None,
                    rel.end_date.isoformat() if rel.end_date else None,
                )
                if key not in seg_best or rel.id < seg_best[key].id:
                    seg_best[key] = rel
            for key, rel in seg_best.items():
                pair = key[0]
                is_ex = rel.relation_nature == 1
                edges.append({
                    "id": f"s-{rel.id}",
                    "source": pair[0],
                    "target": pair[1],
                    "edge_type": "spouse",
                    "nature": rel.relation_nature,
                    "dashed": is_ex,
                    "label": "前任" if is_ex else "伴侣",
                    "start_date": rel.start_date.isoformat() if rel.start_date else None,
                    "end_date": rel.end_date.isoformat() if rel.end_date else None,
                    "color": COLOR_SPOUSE_EX if is_ex else COLOR_SPOUSE
                })

        # 3.5) 社会关系边（有向带箭头；过期段虚线；线宽映射亲密度）
        if "social" in types:
            social_rels = self.db.query(SocialRelation).all()
            social_type_ids = {r.type_id for r in social_rels}
            social_types = {
                t.id: t for t in self.db.query(SocialRelationType).filter(
                    SocialRelationType.id.in_(list(social_type_ids))
                ).all()
            } if social_type_ids else {}
            social_budget = MAX_SOCIAL_EDGES
            for rel in social_rels:
                if social_budget <= 0:
                    truncated = True
                    break
                if not pair_allowed(rel.person_a_id, rel.person_b_id):
                    continue
                t = social_types.get(rel.type_id)
                if not t:
                    continue
                is_past = rel.end_date is not None
                # 有向边 a -> b；无向边存储已归一化，直接用
                base_label = t.name
                if t.directed and t.reverse_name:
                    base_label = f"{t.reverse_name}·{t.name}"
                # 亲密度映射线宽 0.8 ~ 2.6（无亲密度 0.8）
                width = 0.8 if not rel.closeness else 0.5 + rel.closeness * 0.42
                edges.append({
                    "id": f"o-{rel.id}",
                    "source": rel.person_a_id,
                    "target": rel.person_b_id,
                    "edge_type": "social",
                    "ref_id": t.id,
                    "directed": bool(t.directed),
                    "closeness": rel.closeness,
                    "dashed": is_past,
                    "label": ("前" + base_label) if is_past else base_label,
                    "type_name": t.name,
                    "start_date": rel.start_date.isoformat() if rel.start_date else None,
                    "end_date": rel.end_date.isoformat() if rel.end_date else None,
                    "width": round(width, 2),
                    "color": t.color or COLOR_SOCIAL
                })
                social_budget -= 1

        # 4) 同组 / 同标签边（共享同一分组/标签的成对人物）
        cluster_budget = MAX_CLUSTER_EDGES
        if "group" in types:
            groups = self.db.query(PersonGroup).all()
            for g in groups:
                if cluster_budget <= 0:
                    truncated = True
                    break
                members = self.db.query(PersonGroupMember.person_id).filter(
                    PersonGroupMember.group_id == g.id
                ).all()
                ids = sorted(m[0] for m in members if m[0] in allowed_ids)
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        if cluster_budget <= 0:
                            truncated = True
                            break
                        edges.append({
                            "id": f"g-{g.id}-{ids[i]}-{ids[j]}",
                            "source": ids[i],
                            "target": ids[j],
                            "edge_type": "group",
                            "ref_id": g.id,
                            "dashed": False,
                            "label": g.name or "同组",
                            "color": g.color or COLOR_GROUP
                        })
                        cluster_budget -= 1
                    if cluster_budget <= 0:
                        truncated = True
                        break

        if "tag" in types and cluster_budget > 0:
            tags = self.db.query(Tag).all()
            for t in tags:
                if cluster_budget <= 0:
                    truncated = True
                    break
                members = self.db.query(PersonTag.person_id).filter(
                    PersonTag.tag_id == t.id
                ).all()
                ids = sorted(m[0] for m in members if m[0] in allowed_ids)
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        if cluster_budget <= 0:
                            truncated = True
                            break
                        edges.append({
                            "id": f"t-{t.id}-{ids[i]}-{ids[j]}",
                            "source": ids[i],
                            "target": ids[j],
                            "edge_type": "tag",
                            "ref_id": t.id,
                            "dashed": False,
                            "label": t.name or "同标签",
                            "color": t.color or COLOR_TAG
                        })
                        cluster_budget -= 1
                    if cluster_budget <= 0:
                        truncated = True
                        break

        # 5) 节点：以候选人物为准，补充计算度数；无边的孤点也保留（Obsidian 风格）
        degree: Dict[int, int] = defaultdict(int)
        connected: Set[int] = set()
        for e in edges:
            degree[e["source"]] += 1
            degree[e["target"]] += 1
            connected.add(e["source"])
            connected.add(e["target"])

        nodes = []
        for p in persons:
            nodes.append({
                "id": p.id,
                "name": self._display_name(p),
                "avatar_url": p.avatar_url,
                "gender": p.gender,
                "death_date": p.death_date.isoformat() if p.death_date else None,
                "is_me": bool(p.is_me),
                "importance": p.importance or 1,
                "degree": degree.get(p.id, 0),
                "connected": p.id in connected
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "connected_node_count": len(connected),
                "truncated": truncated
            }
        }

    # ------------------------------------------------------------------
    # 个人中心网络（Ego Network，一级关系）
    # ------------------------------------------------------------------
    def get_ego_network(self, person_id: int) -> Dict:
        center = self.db.query(Person).filter(Person.id == person_id).first()
        if not center:
            return {"center": None, "nodes": [], "edges": [], "counts": {}}

        # neighbor_id -> {"categories": set(), "labels": [str]}
        neighbors: Dict[int, Dict] = defaultdict(
            lambda: {"categories": [], "labels": []}
        )

        def add_neighbor(pid: int, category: str, label: str):
            if pid == person_id:
                return
            slot = neighbors[pid]
            if category not in slot["categories"]:
                slot["categories"].append(category)
            if label and label not in slot["labels"]:
                slot["labels"].append(label)

        # 长辈（父亲/母亲）
        parent_rels = self.db.query(FamilyRelation).filter(
            FamilyRelation.person_b_id == person_id,
            FamilyRelation.relation.in_([
                FamilyRelationType.FATHER,
                FamilyRelationType.MOTHER
            ])
        ).all()
        parent_role = {0: "父亲", 1: "母亲"}
        for rel in parent_rels:
            nature = NATURE_LABELS.get(rel.relation_nature, "亲")
            base = parent_role.get(rel.relation, "长辈")
            label = base if rel.relation_nature == 0 else f"{nature}{base}"
            add_neighbor(rel.person_a_id, "parent", label)

        # 晚辈（儿子/女儿）
        child_rels = self.db.query(FamilyRelation).filter(
            FamilyRelation.person_a_id == person_id,
            FamilyRelation.relation.in_([
                FamilyRelationType.FATHER,
                FamilyRelationType.MOTHER
            ])
        ).all()
        for rel in child_rels:
            nature = NATURE_LABELS.get(rel.relation_nature, "亲")
            # 依据对方性别决定称谓
            other = self.db.query(Person).filter(Person.id == rel.person_b_id).first()
            base = "女儿" if other and other.gender == 2 else "儿子"
            label = base if rel.relation_nature == 0 else f"{nature}{base}"
            add_neighbor(rel.person_b_id, "child", label)

        # 配偶/伴侣
        spouse_rels = self.db.query(SpouseRelation).filter(
            or_(
                SpouseRelation.person_a_id == person_id,
                SpouseRelation.person_b_id == person_id
            )
        ).all()
        seen_seg = set()
        for rel in spouse_rels:
            if rel.person_a_id == person_id:
                other_id = rel.person_b_id
                # 本人是 a：对方称谓 = 行角色的反向
                other_role = FamilyService._get_reverse_spouse_relation(rel.relation)
            else:
                other_id = rel.person_a_id
                other_role = rel.relation
            # 按段去重（同一对人的现任/前任各算一段）
            seg_key = (
                other_id, rel.relation_nature,
                rel.start_date.isoformat() if rel.start_date else None,
                rel.end_date.isoformat() if rel.end_date else None,
            )
            if seg_key in seen_seg:
                continue
            seen_seg.add(seg_key)
            if rel.relation_nature == 1:
                label = "前任"
            else:
                label = SPOUSE_ROLE_LABELS.get(other_role, "伴侣")
            add_neighbor(other_id, "spouse", label)

        # 社会关系（朋友/同事/师生等，按段收集）
        social_rows = self.db.query(SocialRelation).filter(
            or_(
                SocialRelation.person_a_id == person_id,
                SocialRelation.person_b_id == person_id
            )
        ).all()
        social_type_ids = {r.type_id for r in social_rows}
        social_types = {
            t.id: t for t in self.db.query(SocialRelationType).filter(
                SocialRelationType.id.in_(list(social_type_ids))
            ).all()
        } if social_type_ids else {}
        social_new_count = 0
        social_has_more = False
        for rel in social_rows:
            t = social_types.get(rel.type_id)
            if not t:
                continue
            other_id = (
                rel.person_b_id if rel.person_a_id == person_id
                else rel.person_a_id
            )
            # 有向：中心是 a 时对方是我的 reverse_name；中心是 b 时对方是我的 name
            if t.directed:
                label = t.reverse_name if rel.person_a_id == person_id else t.name
            else:
                label = t.name
            if rel.end_date is not None:
                label = "前" + (label or t.name)
            is_new = not (
                other_id in neighbors and "social" in neighbors[other_id]["categories"]
            )
            if is_new:
                if social_new_count >= SOCIAL_NEIGHBOR_CAP:
                    social_has_more = True
                    break
                social_new_count += 1
            add_neighbor(other_id, "social", label)

        # 同分组
        my_groups = self.db.query(PersonGroupMember.group_id).filter(
            PersonGroupMember.person_id == person_id
        ).all()
        group_mate_cap = 60
        group_mate_count = 0
        group_has_more = False
        for (gid,) in my_groups:
            g = self.db.query(PersonGroup).filter(PersonGroup.id == gid).first()
            members = self.db.query(PersonGroupMember.person_id).filter(
                PersonGroupMember.group_id == gid
            ).all()
            for (pid,) in members:
                if pid == person_id:
                    continue
                is_new = not (pid in neighbors and "group" in neighbors[pid]["categories"])
                if is_new:
                    if group_mate_count >= group_mate_cap:
                        group_has_more = True
                        break
                    group_mate_count += 1
                add_neighbor(pid, "group", (g.name if g else "同组"))
            if group_has_more:
                break

        # 同标签
        my_tags = self.db.query(PersonTag.tag_id).filter(
            PersonTag.person_id == person_id
        ).all()
        tag_mate_cap = 60
        tag_mate_count = 0
        tag_has_more = False
        for (tid,) in my_tags:
            t = self.db.query(Tag).filter(Tag.id == tid).first()
            members = self.db.query(PersonTag.person_id).filter(
                PersonTag.tag_id == tid
            ).all()
            for (pid,) in members:
                if pid == person_id:
                    continue
                is_new = not (pid in neighbors and "tag" in neighbors[pid]["categories"])
                if is_new:
                    if tag_mate_count >= tag_mate_cap:
                        tag_has_more = True
                        break
                    tag_mate_count += 1
                add_neighbor(pid, "tag", (t.name if t else "同标签"))
            if tag_has_more:
                break

        # 组装节点
        category_order = {
            "parent": 0, "spouse": 1, "social": 2,
            "child": 3, "group": 4, "tag": 5
        }

        people = {
            p.id: p
            for p in self.db.query(Person).filter(Person.id.in_(list(neighbors.keys()))).all()
        } if neighbors else {}

        neighbor_ids = sorted(
            neighbors.keys(),
            key=lambda pid: (
                min(category_order[c] for c in neighbors[pid]["categories"]),
                self._display_name(people[pid]) if pid in people else str(pid)
            )
        )

        nodes = []
        edges = []
        counts = defaultdict(int)
        for pid in neighbor_ids:
            p = people.get(pid)
            if not p:
                continue
            info = neighbors[pid]
            # 一个人可能同时是配偶+同组，取最高优先级类别决定扇区
            primary = min(info["categories"], key=lambda c: category_order[c])
            counts[primary] += 1
            nodes.append({
                "id": p.id,
                "name": self._display_name(p),
                "avatar_url": p.avatar_url,
                "gender": p.gender,
                "death_date": p.death_date.isoformat() if p.death_date else None,
                "is_me": bool(p.is_me),
                "importance": p.importance or 1,
                "category": primary,
                "all_categories": info["categories"],
                "labels": info["labels"][:3]
            })
            edges.append({
                "id": f"e-{person_id}-{pid}",
                "source": person_id,
                "target": pid,
                "edge_type": primary,
                "label": " / ".join(info["labels"][:2]),
                "dashed": primary in ("group", "tag")
            })

        return {
            "center": self._center_dict(center),
            "nodes": nodes,
            "edges": edges,
            "counts": dict(counts),
            "has_more": {
                "social": social_has_more,
                "group": group_has_more,
                "tag": tag_has_more
            }
        }

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _display_name(person: Person) -> str:
        full = f"{person.last_name or ''}{person.first_name or ''}".strip()
        return full or person.nickname or "未命名"

    def _center_dict(self, p: Person) -> Dict:
        return {
            "id": p.id,
            "name": self._display_name(p),
            "avatar_url": p.avatar_url,
            "gender": p.gender,
            "death_date": p.death_date.isoformat() if p.death_date else None,
            "is_me": bool(p.is_me),
            "importance": p.importance or 1
        }
