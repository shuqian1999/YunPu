# -*- coding: utf-8 -*-
from datetime import date as date_type

from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.person import Person
from app.models.family_relation import FamilyRelation
from app.models.spouse_relation import SpouseRelation
from app.models.enums.relation_enums import (
    FamilyRelationType, RelationNature,
    SpouseRelationType, SpouseRelationNature,
)
from app.services.kinship_rules import (
    U, D, M,
    MALE, FEMALE,
    resolve_kinship,
)
from typing import Dict, List, Optional, Tuple
from collections import deque, defaultdict


class GenderType:
    """性别取值（Person.gender 为整型，1=男，2=女）"""
    MALE = MALE
    FEMALE = FEMALE


# 路径搜索边界
MAX_PATH_HOP = 5      # 称谓路径最大跳数（支持五跳姻亲）
ENUMERATE_CAP = 40    # 两人之间最多保留的候选路径数
BFS_LAYER_CAP = 4000  # 全图 BFS 每层展开上限（防极端稠密图）
GROUP_PATTERN_CAP = 4 # 每人在分组 BFS 中保留的不同路径模式数
ALT_NAME_CAP = 2      # 备用称谓数量上限


# 关系持有者的性别要求
_FAMILY_HOLDER_GENDER = {
    FamilyRelationType.FATHER: GenderType.MALE,
    FamilyRelationType.MOTHER: GenderType.FEMALE,
    FamilyRelationType.SON: GenderType.MALE,
    FamilyRelationType.DAUGHTER: GenderType.FEMALE,
}
_SPOUSE_HOLDER_GENDER = {
    SpouseRelationType.HUSBAND: GenderType.MALE,
    SpouseRelationType.WIFE: GenderType.FEMALE,
    SpouseRelationType.CONCUBINE: GenderType.FEMALE,
}


class _RelationView:
    """创建接口的响应视图：单行存储仍向调用方呈现 forward/reverse 两份语义"""

    def __init__(self, data: Dict):
        self._data = data

    def to_dict(self) -> Dict:
        return dict(self._data)


class FamilyService:
    """家族关系服务"""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 写入（含校验）
    # ------------------------------------------------------------------
    def create_family_relation(
        self,
        person_a_id: int,
        person_b_id: int,
        relation: int,
        relation_nature: int = 0
    ) -> Tuple[_RelationView, _RelationView]:
        """
        创建家庭关系。存储层只写一条 parent -> child 单向边。

        约定（入参语义不变）：(person_a, person_b, X) 表示 "person_a 是 person_b 的 X"
        relation: 0:父, 1:母, 2:子, 3:女
        relation_nature: 0:亲, 1:继, 2:养, 3:义, 4:干
        """
        if relation not in (r.value for r in FamilyRelationType):
            raise ValueError("家庭关系类型不合法")
        if relation_nature not in (n.value for n in RelationNature):
            raise ValueError("家庭关系性质不合法")
        if person_a_id == person_b_id:
            raise ValueError("不能与自己建立关系")

        person_a = self.db.query(Person).filter(Person.id == person_a_id).first()
        person_b = self.db.query(Person).filter(Person.id == person_b_id).first()
        if not person_a or not person_b:
            raise ValueError("关联的人物不存在")

        # 归一化为 (parent, child, 父母角色)
        if relation in (FamilyRelationType.FATHER, FamilyRelationType.MOTHER):
            parent, child = person_a, person_b
            parent_role = relation
        else:
            parent, child = person_b, person_a
            # 父母角色由父母本人性别决定；性别未知时按反向映射兜底
            if parent.gender == GenderType.FEMALE:
                parent_role = FamilyRelationType.MOTHER
            elif parent.gender == GenderType.MALE:
                parent_role = FamilyRelationType.FATHER
            else:
                parent_role = self._get_reverse_relation(relation)

        # 性别一致性（性别未填则不拦截）
        required_gender = _FAMILY_HOLDER_GENDER.get(relation)
        if required_gender and person_a.gender and person_a.gender != required_gender:
            raise ValueError("人物性别与所选关系不符")

        # 重复关系（双向查）
        exists = self.db.query(FamilyRelation).filter(
            or_(
                (FamilyRelation.person_a_id == person_a_id)
                & (FamilyRelation.person_b_id == person_b_id),
                (FamilyRelation.person_a_id == person_b_id)
                & (FamilyRelation.person_b_id == person_a_id),
            )
        ).first()
        if exists:
            raise ValueError("两人之间已存在家庭关系，请勿重复添加")

        # 亲生父母唯一性（同角色）
        if relation_nature == RelationNature.BIOLOGICAL:
            existing_bio = self.db.query(FamilyRelation).filter(
                FamilyRelation.person_b_id == child.id,
                FamilyRelation.relation == parent_role,
                FamilyRelation.relation_nature == RelationNature.BIOLOGICAL,
            ).first()
            if existing_bio:
                role_name = "亲生父亲" if parent_role == FamilyRelationType.FATHER else "亲生母亲"
                raise ValueError(f"{child.last_name or ''}{child.first_name or '该人物'}已有{role_name}")

        # 辈分环检测：新加入 parent -> child，若 parent 本就是 child 的晚辈，则成环
        if self._is_descendant(parent.id, child.id):
            raise ValueError("该关系会形成辈分环（晚辈不能成为长辈的父母）")

        row = FamilyRelation(
            person_a_id=parent.id,
            person_b_id=child.id,
            relation=parent_role,
            relation_nature=relation_nature,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)

        # 响应仍按入参方向呈现两份语义（共享同一存储行 id）
        forward = _RelationView({
            "id": row.id,
            "person_a_id": person_a_id,
            "person_b_id": person_b_id,
            "relation": relation,
            "relation_nature": relation_nature,
        })
        reverse = _RelationView({
            "id": row.id,
            "person_a_id": person_b_id,
            "person_b_id": person_a_id,
            "relation": self._get_reverse_relation(relation),
            "relation_nature": relation_nature,
        })
        return forward, reverse

    def create_spouse_relation(
        self,
        person_a_id: int,
        person_b_id: int,
        relation: int,
        relation_nature: int = 0,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> Tuple[_RelationView, _RelationView]:
        """
        创建配偶关系段，段内写正反向双行；同一对人可有多段（复婚）。
        relation: 0:丈夫, 1:妻子, 2:姨太太（男女朋友请在社会关系中维护）
        relation_nature: 0:现任, 1:前任
        """
        if relation not in (r.value for r in SpouseRelationType):
            raise ValueError("配偶关系类型不合法")
        if relation_nature not in (n.value for n in SpouseRelationNature):
            raise ValueError("配偶关系性质不合法")
        if person_a_id == person_b_id:
            raise ValueError("不能与自己建立关系")
        if start_date and end_date and end_date < start_date:
            raise ValueError("关系结束日期不能早于开始日期")
        if relation_nature == SpouseRelationNature.CURRENT and end_date:
            raise ValueError("现任关系不能填写结束日期（如需记录请改为前任）")

        person_a = self.db.query(Person).filter(Person.id == person_a_id).first()
        person_b = self.db.query(Person).filter(Person.id == person_b_id).first()
        if not person_a or not person_b:
            raise ValueError("关联的人物不存在")

        # 双方性别都要与角色一致
        gender_a = _SPOUSE_HOLDER_GENDER.get(relation)
        gender_b = _SPOUSE_HOLDER_GENDER.get(self._get_reverse_spouse_relation(relation))
        if gender_a and person_a.gender and person_a.gender != gender_a:
            raise ValueError("人物性别与所选配偶关系不符")
        if gender_b and person_b.gender and person_b.gender != gender_b:
            raise ValueError("对方性别与所选配偶关系不符")

        existing_rows = self.db.query(SpouseRelation).filter(
            or_(
                (SpouseRelation.person_a_id == person_a_id)
                & (SpouseRelation.person_b_id == person_b_id),
                (SpouseRelation.person_a_id == person_b_id)
                & (SpouseRelation.person_b_id == person_a_id),
            )
        ).all()
        # 折叠为段：(nature, start, end) -> rows
        segments = defaultdict(list)
        for r in existing_rows:
            segments[(r.relation_nature, r.start_date, r.end_date)].append(r)

        for (nat, sdate, edate), rows in segments.items():
            if relation_nature == SpouseRelationNature.CURRENT \
                    and nat == SpouseRelationNature.CURRENT:
                raise ValueError("两人已有现任配偶关系，请先将上一段标记为前任再添加")
            if nat == relation_nature and sdate == start_date and edate == end_date:
                raise ValueError("完全相同的配偶关系段已存在，请勿重复添加")
            # 时间段重叠（双方日期齐全才判断；半开区间）
            if sdate and edate and start_date and end_date:
                if start_date <= edate and sdate <= end_date:
                    raise ValueError("新关系段与已有关系段的时间区间重叠")

        reverse_relation = self._get_reverse_spouse_relation(relation)
        common = dict(relation_nature=relation_nature, start_date=start_date, end_date=end_date)
        forward = SpouseRelation(
            person_a_id=person_a_id, person_b_id=person_b_id, relation=relation, **common
        )
        reverse = SpouseRelation(
            person_a_id=person_b_id, person_b_id=person_a_id, relation=reverse_relation, **common
        )
        self.db.add(forward)
        self.db.add(reverse)
        self.db.commit()
        self.db.refresh(forward)
        self.db.refresh(reverse)

        fv = _RelationView({
            "id": forward.id,
            "person_a_id": person_a_id, "person_b_id": person_b_id,
            "relation": relation,
            "relation_nature": relation_nature,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        })
        rv = _RelationView({
            "id": reverse.id,
            "person_a_id": person_b_id, "person_b_id": person_a_id,
            "relation": reverse_relation,
            "relation_nature": relation_nature,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        })
        return fv, rv

    def _is_descendant(self, maybe_descendant_id: int, ancestor_id: int) -> bool:
        """maybe_descendant_id 是否为 ancestor_id 的晚辈（沿亲子边下行可达）"""
        queue = deque([ancestor_id])
        seen = {ancestor_id}
        while queue:
            cur = queue.popleft()
            rows = self.db.query(FamilyRelation).filter(
                FamilyRelation.person_a_id == cur,
                FamilyRelation.relation.in_([
                    FamilyRelationType.FATHER, FamilyRelationType.MOTHER
                ])
            ).all()
            for rel in rows:
                if rel.person_b_id == maybe_descendant_id:
                    return True
                if rel.person_b_id not in seen:
                    seen.add(rel.person_b_id)
                    queue.append(rel.person_b_id)
        return False

    def delete_family_relation(self, person_a_id: int, person_b_id: int):
        """删除家庭关系（单向存储后双向定位至多一行）"""
        self.db.query(FamilyRelation).filter(
            or_(
                (FamilyRelation.person_a_id == person_a_id) & (FamilyRelation.person_b_id == person_b_id),
                (FamilyRelation.person_a_id == person_b_id) & (FamilyRelation.person_b_id == person_a_id)
            )
        ).delete(synchronize_session=False)
        self.db.commit()

    def delete_spouse_relation(
        self,
        person_a_id: Optional[int] = None,
        person_b_id: Optional[int] = None,
        relation_id: Optional[int] = None,
    ):
        """
        删除配偶关系段（段内正反向两行同删）。
        - 指定 relation_id：按段行定位（多段场景必传）
        - 仅给两人 id：仅一段时删除，多段时报错要求指定段
        """
        if relation_id:
            row = self.db.query(SpouseRelation).filter(
                SpouseRelation.id == relation_id
            ).first()
            if not row:
                raise ValueError("关系段不存在或已被删除")
            self._delete_spouse_segment(row)
            self.db.commit()
            return

        if not person_a_id or not person_b_id:
            raise ValueError("缺少要删除的关系信息")
        rows = self.db.query(SpouseRelation).filter(
            or_(
                (SpouseRelation.person_a_id == person_a_id)
                & (SpouseRelation.person_b_id == person_b_id),
                (SpouseRelation.person_a_id == person_b_id)
                & (SpouseRelation.person_b_id == person_a_id),
            )
        ).all()
        if not rows:
            return
        segment_keys = {(r.relation_nature, r.start_date, r.end_date) for r in rows}
        if len(segment_keys) > 1:
            raise ValueError("两人存在多段配偶关系，请指定要删除的具体关系段")
        for r in rows:
            self.db.delete(r)
        self.db.commit()

    def _delete_spouse_segment(self, row: SpouseRelation):
        """按段内任一定位行删除正反向两行"""
        counterpart = self.db.query(SpouseRelation).filter(
            SpouseRelation.person_a_id == row.person_b_id,
            SpouseRelation.person_b_id == row.person_a_id,
            SpouseRelation.relation_nature == row.relation_nature,
            SpouseRelation.start_date == row.start_date,
            SpouseRelation.end_date == row.end_date,
        ).all()
        self.db.delete(row)
        for other in counterpart:
            self.db.delete(other)

    # ------------------------------------------------------------------
    # 查询：直接关系（人物详情 / to-me 共用）
    # ------------------------------------------------------------------
    def get_direct_relations(self, person_id: int) -> List[Dict]:
        """某人的全部直接关系（父母/子女/配偶段），内存图一次构建，无 N+1"""
        graph = self._load_graph()
        persons, parents_of, children_of, spouses_of = graph
        ego = persons.get(person_id)
        if not ego:
            return []

        def display_name(p):
            return self._display_name(p)

        result: List[Dict] = []

        for pid, nature, role in parents_of.get(person_id, []):
            other = persons.get(pid)
            if not other:
                continue
            info = self._name_from_steps([(U, nature, role, pid)], person_id, graph)
            outgoing = FamilyRelationType.SON if ego.gender == GenderType.MALE \
                else FamilyRelationType.DAUGHTER
            result.append(self._direct_item(
                other, info, int(outgoing), nature,
                name=display_name(other),
            ))

        for pid, nature, role in children_of.get(person_id, []):
            other = persons.get(pid)
            if not other:
                continue
            info = self._name_from_steps([(D, nature, role, pid)], person_id, graph)
            result.append(self._direct_item(
                other, info, int(role), nature,
                name=display_name(other),
            ))

        for pid, other_role, nature, start, end, row_id in spouses_of.get(person_id, []):
            other = persons.get(pid)
            if not other:
                continue
            info = self._name_from_steps([(M, nature, other_role, pid)], person_id, graph)
            item = self._direct_item(
                other, info, f"spouse_{int(other_role)}", nature,
                name=display_name(other),
            )
            item["relation_id"] = row_id
            item["start_date"] = start.isoformat() if start else None
            item["end_date"] = end.isoformat() if end else None
            result.append(item)

        return result

    @staticmethod
    def _direct_item(person, info, relation_type, nature, name: str) -> Dict:
        return {
            "person_id": person.id,
            "name": name,
            "relation_name": info["relation_name"],
            "alt_relation_names": info.get("alt_relation_names", []),
            "relation_type": relation_type,
            "relation_nature": nature,
            "gender": person.gender,
            "birth_date": person.birth_date.isoformat() if person.birth_date else None,
        }

    def get_relations_to_me(self) -> List[Dict]:
        """获取所有与"我"的直接亲属/配偶关系"""
        me_id = self._get_me_id()
        if not me_id:
            return []
        return self.get_direct_relations(me_id)

    # ------------------------------------------------------------------
    # 查询：两人之间的关系（多路径，含备用称谓）
    # ------------------------------------------------------------------
    def calculate_relation_between(self, person_a_id: int, person_b_id: int) -> Dict:
        """计算两人之间的关系称谓；同一对人有多条路径时返回主称谓 + 备用称谓"""
        if person_a_id == person_b_id:
            return {"relation_name": "自己", "level": 0, "is_blood": True,
                    "alt_relation_names": []}

        graph = self._load_graph()
        persons, parents_of, children_of, spouses_of = graph
        if person_a_id not in persons or person_b_id not in persons:
            return {"relation_name": "无关系", "level": -1, "is_blood": False,
                    "alt_relation_names": []}

        candidates = []

        def add_candidate(steps):
            if steps not in candidates:
                candidates.append(steps)

        # 1) 直接亲子/配偶（一跳，天然优先）
        for pid, nature, role in parents_of.get(person_b_id, []):
            if pid == person_a_id:
                add_candidate([(D, nature, role, person_b_id)])
        for pid, nature, role in parents_of.get(person_a_id, []):
            if pid == person_b_id:
                add_candidate([(U, nature, role, person_b_id)])
        for pid, other_role, nature, *_ in spouses_of.get(person_a_id, []):
            if pid == person_b_id:
                add_candidate([(M, nature, other_role, person_b_id)])

        # 2) 枚举至多 MAX_PATH_HOP 跳的所有简单路径（覆盖多重身份）
        for path in self._enumerate_paths(person_a_id, person_b_id, graph):
            add_candidate(path)

        if not candidates:
            return {"relation_name": "无关系", "level": -1, "is_blood": False,
                    "alt_relation_names": []}
        return self._choose_relation(candidates, person_a_id, graph)

    def _enumerate_paths(self, src_id: int, dst_id: int, graph) -> List[list]:
        """BFS 分层枚举 src -> dst 的所有简单路径（≤MAX_PATH_HOP 跳，有界截断）"""
        _, parents_of, children_of, spouses_of = graph
        found: List[list] = []
        # (当前节点, 路径节点集合, 已走步)
        frontier = [(src_id, frozenset({src_id}), [])]
        for _ in range(MAX_PATH_HOP):
            next_frontier = []
            for cur, seen, steps in frontier:
                for step in self._out_steps(cur, parents_of, children_of, spouses_of):
                    nid = step[3]
                    if nid in seen:
                        continue
                    nsteps = steps + [step]
                    if nid == dst_id:
                        if nsteps not in found:
                            found.append(nsteps)
                        if len(found) >= ENUMERATE_CAP:
                            return found
                    else:
                        next_frontier.append((nid, seen | {nid}, nsteps))
                        if len(next_frontier) >= BFS_LAYER_CAP:
                            break
            frontier = next_frontier
            if not frontier:
                break
        return found

    @staticmethod
    def _out_steps(cur, parents_of, children_of, spouses_of):
        """节点的所有出边步（配偶段现任优先、日期新者优先）"""
        steps = []
        for pid, nature, role in parents_of.get(cur, []):
            steps.append((U, nature, role, pid))
        for pid, nature, role in children_of.get(cur, []):
            steps.append((D, nature, role, pid))
        spouse_items = sorted(
            spouses_of.get(cur, []),
            key=lambda it: (it[2], it[3] is None, -(it[3].toordinal()) if it[3] else 0),
        )
        for pid, other_role, nature, _start, _end, _rid in spouse_items:
            steps.append((M, nature, other_role, pid))
        return steps

    @staticmethod
    def _path_score(steps: list) -> tuple:
        """路径排序：跳数少 > 血亲 > 婚姻步少 > 非血亲边少 > 前任婚姻少"""
        kinds = [s[0] for s in steps]
        m_count = kinds.count(M)
        ex_count = sum(
            1 for s in steps
            if s[0] == M and s[1] == SpouseRelationNature.EX
        )
        non_bio = sum(
            1 for s in steps
            if s[0] != M and s[1] != RelationNature.BIOLOGICAL
        )
        blood_rank = 0 if (m_count == 0 and non_bio == 0) else 1
        return (len(steps), blood_rank, m_count, non_bio, ex_count)

    def _choose_relation(self, candidates: List[list], ego_id: int, graph) -> Dict:
        resolved = [
            (self._path_score(steps), self._name_from_steps(steps, ego_id, graph))
            for steps in candidates
        ]
        resolved.sort(key=lambda x: x[0])
        primary = resolved[0][1]
        alt_names: List[str] = []
        for _score, info in resolved[1:]:
            name = info["relation_name"]
            if name in ("远亲", "无关系", primary["relation_name"]) or name in alt_names:
                continue
            alt_names.append(name)
            if len(alt_names) >= ALT_NAME_CAP:
                break
        return {
            "relation_name": primary["relation_name"],
            "level": primary["level"],
            "is_blood": primary["is_blood"],
            "alt_relation_names": alt_names,
        }

    # ------------------------------------------------------------------
    # 查询：按代差分组（家族页；多模式 BFS，保留多重身份）
    # ------------------------------------------------------------------
    def get_relations_grouped_by_generation(self) -> Dict:
        persons, parents_of, children_of, spouses_of = self._load_graph()
        me = persons.get(self._get_me_id())
        if not me:
            return {"me": None, "groups": [], "total": 0}

        graph = (persons, parents_of, children_of, spouses_of)

        # node -> {kinds 模式: steps}，每人最多保留 GROUP_PATTERN_CAP 种模式
        paths_by_node: Dict[int, Dict[tuple, list]] = {me.id: {(): []}}
        frontier = [(me.id, frozenset({me.id}), ())]

        for _ in range(MAX_PATH_HOP):
            next_frontier = []
            for cur, seen, kinds_sig in frontier:
                steps = paths_by_node[cur][kinds_sig]
                for step in self._out_steps(cur, parents_of, children_of, spouses_of):
                    nid = step[3]
                    if nid in seen or nid == me.id:
                        continue
                    new_sig = kinds_sig + (step[0],)
                    bucket = paths_by_node.setdefault(nid, {})
                    if new_sig in bucket:
                        continue
                    if len(bucket) >= GROUP_PATTERN_CAP:
                        continue
                    nsteps = steps + [step]
                    bucket[new_sig] = nsteps
                    next_frontier.append((nid, seen | {nid}, new_sig))
                    if len(next_frontier) >= BFS_LAYER_CAP:
                        break
            frontier = next_frontier
            if not frontier:
                break

        grouped: Dict[int, List[Dict]] = defaultdict(list)
        for person_id, bucket in paths_by_node.items():
            if person_id == me.id:
                continue
            person = persons.get(person_id)
            if not person:
                continue
            chosen = self._choose_relation(list(bucket.values()), me.id, graph)
            # 代差以主称谓路径为准
            gen_offset = chosen["level"]
            primary_steps = min(bucket.values(), key=self._path_score)
            last_nature = primary_steps[-1][1] if primary_steps else 0

            grouped[gen_offset].append({
                "id": person.id,
                "name": self._display_name(person),
                "avatar_url": person.avatar_url,
                "gender": person.gender,
                "birth_date": person.birth_date.isoformat() if person.birth_date else None,
                "death_date": person.death_date.isoformat() if person.death_date else None,
                "relation_name": chosen["relation_name"],
                "alt_relation_names": chosen["alt_relation_names"],
                "is_blood": chosen["is_blood"],
                "relation_nature": last_nature,
                "generation_offset": gen_offset,
            })

        result_groups = []
        for offset in sorted(grouped.keys(), reverse=True):
            people_in_group = sorted(
                grouped[offset],
                key=lambda p: (p["relation_name"], p["name"])
            )
            result_groups.append({
                "generation_offset": offset,
                "label": self._generation_label(offset),
                "count": len(people_in_group),
                "persons": people_in_group
            })

        return {
            "me": me.to_dict(),
            "groups": result_groups,
            "total": sum(g["count"] for g in result_groups)
        }

    # ------------------------------------------------------------------
    # 内存图加载
    # ------------------------------------------------------------------
    def _load_graph(self):
        """
        一次性载入全部人物与亲属/配偶边，构图：
        - persons:    id -> Person
        - parents_of: child_id -> [(parent_id, nature, 父母角色 FATHER/MOTHER)]
        - children_of: parent_id -> [(child_id, nature, 父母角色)]
        - spouses_of: holder_id -> [(other_id, 对方相对本人角色, nature,
                                     start_date, end_date, 行id)]
          配偶一行生成一个有向邻接项（段内双行即双向两项），多段自然保留
        """
        persons = {p.id: p for p in self.db.query(Person).all()}

        parents_of: Dict[int, List] = defaultdict(list)
        children_of: Dict[int, List] = defaultdict(list)
        family_rows = self.db.query(FamilyRelation).filter(
            FamilyRelation.relation.in_([
                FamilyRelationType.FATHER, FamilyRelationType.MOTHER
            ])
        ).all()
        for rel in family_rows:
            parents_of[rel.person_b_id].append(
                (rel.person_a_id, rel.relation_nature, rel.relation)
            )
            children_of[rel.person_a_id].append(
                (rel.person_b_id, rel.relation_nature, rel.relation)
            )

        spouses_of: Dict[int, List] = defaultdict(list)
        spouse_rows = self.db.query(SpouseRelation).all()
        for rel in spouse_rows:
            # (a, b, X) 表示 a 是 b 的 X：从 a 看 b 是 X 的反向角色
            spouses_of[rel.person_a_id].append((
                rel.person_b_id,
                self._get_reverse_spouse_relation(rel.relation),
                rel.relation_nature,
                rel.start_date,
                rel.end_date,
                rel.id,
            ))

        return persons, parents_of, children_of, spouses_of

    def _get_me_id(self) -> Optional[int]:
        me = self.db.query(Person.id).filter(Person.is_me == True).first()  # noqa: E712
        return me[0] if me else None

    # ------------------------------------------------------------------
    # 称谓：委托规则表引擎
    # ------------------------------------------------------------------
    def _name_from_steps(self, steps: List[tuple], ego_id: int, graph) -> Dict:
        return resolve_kinship(steps, ego_id, graph)

    # ------------------------------------------------------------------
    # 静态辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _generation_label(offset: int) -> str:
        """代差值转中文标签"""
        if offset >= 3:
            return f"高祖辈 (+{offset})"
        if offset == 2:
            return "祖辈"
        if offset == 1:
            return "父辈"
        if offset == 0:
            return "同辈"
        if offset == -1:
            return "子辈"
        if offset == -2:
            return "孙辈"
        return f"晚辈 ({offset})"

    @staticmethod
    def _display_name(person: Person) -> str:
        """统一人物显示名：姓+名 优先，没有才回退到昵称"""
        full = f"{person.last_name or ''}{person.first_name or ''}".strip()
        if full:
            return full
        return person.nickname or "未命名"

    @staticmethod
    def _get_reverse_relation(relation: int) -> int:
        """获取反向家庭关系类型"""
        reverse_map = {
            FamilyRelationType.FATHER: FamilyRelationType.SON,
            FamilyRelationType.MOTHER: FamilyRelationType.DAUGHTER,
            FamilyRelationType.SON: FamilyRelationType.FATHER,
            FamilyRelationType.DAUGHTER: FamilyRelationType.MOTHER
        }
        return reverse_map.get(relation, relation)

    @staticmethod
    def _get_reverse_spouse_relation(relation: int) -> int:
        """获取反向配偶关系类型"""
        reverse_map = {
            SpouseRelationType.HUSBAND: SpouseRelationType.WIFE,
            SpouseRelationType.WIFE: SpouseRelationType.HUSBAND,
            SpouseRelationType.CONCUBINE: SpouseRelationType.HUSBAND,
        }
        return reverse_map.get(relation, relation)
