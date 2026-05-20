from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.person import Person
from app.models.family_relation import FamilyRelation
from app.models.spouse_relation import SpouseRelation
from app.models.enums.relation_enums import (
    FamilyRelationType, RelationNature, 
    SpouseRelationType, SpouseRelationNature
)
from typing import Dict, List, Optional, Tuple
from collections import deque


class FamilyService:
    """家族关系服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_family_relation(
        self, 
        person_a_id: int, 
        person_b_id: int, 
        relation: int,
        relation_nature: int = 0
    ) -> Tuple[FamilyRelation, FamilyRelation]:
        """
        创建家庭关系，同时创建正向和反向两条记录
        
        Args:
            person_a_id: 人物A的ID
            person_b_id: 人物B的ID  
            relation: 关系类型 (0:父, 1:母, 2:子, 3:女)
            relation_nature: 关系性质 (0:亲, 1:继, 2:养, 3:义, 4:干)
        
        Returns:
            (正向关系, 反向关系) 元组
        """
        # 获取反向关系类型
        reverse_relation = self._get_reverse_relation(relation)
        
        # 创建正向关系
        forward = FamilyRelation(
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            relation=relation,
            relation_nature=relation_nature
        )
        self.db.add(forward)
        
        # 创建反向关系
        reverse = FamilyRelation(
            person_a_id=person_b_id,
            person_b_id=person_a_id,
            relation=reverse_relation,
            relation_nature=relation_nature
        )
        self.db.add(reverse)
        
        self.db.commit()
        self.db.refresh(forward)
        self.db.refresh(reverse)
        
        return forward, reverse
    
    def create_spouse_relation(
        self,
        person_a_id: int,
        person_b_id: int,
        relation: int,
        relation_nature: int = 0
    ) -> Tuple[SpouseRelation, SpouseRelation]:
        """
        创建配偶关系，同时创建正向和反向两条记录
        
        Args:
            person_a_id: 人物A的ID
            person_b_id: 人物B的ID
            relation: 关系类型 (0:丈夫, 1:妻子, 2:姨太太, 3:男朋友, 4:女朋友)
            relation_nature: 关系性质 (0:现任, 1:前任)
        
        Returns:
            (正向关系, 反向关系) 元组
        """
        # 获取反向关系类型
        reverse_relation = self._get_reverse_spouse_relation(relation)
        
        # 创建正向关系
        forward = SpouseRelation(
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            relation=relation,
            relation_nature=relation_nature
        )
        self.db.add(forward)
        
        # 创建反向关系
        reverse = SpouseRelation(
            person_a_id=person_b_id,
            person_b_id=person_a_id,
            relation=reverse_relation,
            relation_nature=relation_nature
        )
        self.db.add(reverse)
        
        self.db.commit()
        self.db.refresh(forward)
        self.db.refresh(reverse)
        
        return forward, reverse
    
    def delete_family_relation(self, person_a_id: int, person_b_id: int):
        """删除家庭关系（同时删除正反向记录）"""
        self.db.query(FamilyRelation).filter(
            or_(
                (FamilyRelation.person_a_id == person_a_id) & (FamilyRelation.person_b_id == person_b_id),
                (FamilyRelation.person_a_id == person_b_id) & (FamilyRelation.person_b_id == person_a_id)
            )
        ).delete(synchronize_session=False)
        self.db.commit()
    
    def delete_spouse_relation(self, person_a_id: int, person_b_id: int):
        """删除配偶关系（同时删除正反向记录）"""
        self.db.query(SpouseRelation).filter(
            or_(
                (SpouseRelation.person_a_id == person_a_id) & (SpouseRelation.person_b_id == person_b_id),
                (SpouseRelation.person_a_id == person_b_id) & (SpouseRelation.person_b_id == person_a_id)
            )
        ).delete(synchronize_session=False)
        self.db.commit()
    
    def get_relations_to_me(self) -> List[Dict]:
        """
        获取所有与"我"的亲属关系
        
        Returns:
            包含人物信息和关系名称的列表
        """
        # 找到"我"
        me = self.db.query(Person).filter(Person.is_me == True).first()
        if not me:
            return []
        
        relations = []
        
        # 获取家庭关系（父母子女）
        family_relations = self.db.query(FamilyRelation).filter(
            FamilyRelation.person_a_id == me.id
        ).all()
        
        for rel in family_relations:
            person = self.db.query(Person).filter(Person.id == rel.person_b_id).first()
            if person:
                relations.append({
                    "person_id": person.id,
                    "name": person.nickname or f"{person.last_name or ''}{person.first_name or ''}",
                    "relation_name": self._get_relation_name(rel.relation, rel.relation_nature, "to_me"),
                    "relation_type": rel.relation,
                    "relation_nature": rel.relation_nature,
                    "gender": person.gender,
                    "birth_date": person.birth_date.isoformat() if person.birth_date else None
                })
        
        # 获取配偶关系
        spouse_relations = self.db.query(SpouseRelation).filter(
            SpouseRelation.person_a_id == me.id
        ).all()
        
        for rel in spouse_relations:
            person = self.db.query(Person).filter(Person.id == rel.person_b_id).first()
            if person:
                relations.append({
                    "person_id": person.id,
                    "name": person.nickname or f"{person.last_name or ''}{person.first_name or ''}",
                    "relation_name": self._get_spouse_relation_name(rel.relation, "to_me"),
                    "relation_type": f"spouse_{rel.relation}",
                    "relation_nature": rel.relation_nature,
                    "gender": person.gender,
                    "birth_date": person.birth_date.isoformat() if person.birth_date else None
                })
        
        return relations
    
    def calculate_relation_between(self, person_a_id: int, person_b_id: int) -> Optional[Dict]:
        """
        计算两人之间的关系
        
        Args:
            person_a_id: 人物A的ID
            person_b_id: 人物B的ID
        
        Returns:
            关系信息字典，包含relation_name, level, is_blood等
        """
        if person_a_id == person_b_id:
            return {"relation_name": "自己", "level": 0, "is_blood": True}
        
        # 首先检查是否有直接关系
        # 1. 检查家庭关系
        direct = self.db.query(FamilyRelation).filter(
            or_(
                (FamilyRelation.person_a_id == person_a_id) & (FamilyRelation.person_b_id == person_b_id),
                (FamilyRelation.person_a_id == person_b_id) & (FamilyRelation.person_b_id == person_a_id)
            )
        ).first()
        
        if direct:
            if direct.person_a_id == person_a_id:
                return {
                    "relation_name": self._get_relation_name(direct.relation, direct.relation_nature, "from_a"),
                    "level": 1,
                    "is_blood": direct.relation_nature == RelationNature.BIOLOGICAL
                }
            else:
                return {
                    "relation_name": self._get_relation_name(direct.relation, direct.relation_nature, "from_b"),
                    "level": 1,
                    "is_blood": direct.relation_nature == RelationNature.BIOLOGICAL
                }
        
        # 2. 检查配偶关系
        spouse = self.db.query(SpouseRelation).filter(
            or_(
                (SpouseRelation.person_a_id == person_a_id) & (SpouseRelation.person_b_id == person_b_id),
                (SpouseRelation.person_a_id == person_b_id) & (SpouseRelation.person_b_id == person_a_id)
            )
        ).first()
        
        if spouse:
            is_from_a = spouse.person_a_id == person_a_id
            return {
                "relation_name": self._get_spouse_relation_name(spouse.relation, "from_a" if is_from_a else "from_b"),
                "level": 1,
                "is_blood": False
            }
        
        # 3. 使用BFS查找间接关系
        return self._find_indirect_relation(person_a_id, person_b_id)
    
    def _find_indirect_relation(self, person_a_id: int, person_b_id: int) -> Optional[Dict]:
        """使用BFS查找两人之间的间接关系"""
        queue = deque()
        visited = {person_a_id}
        
        # 初始节点：[person_id, [(relation_type, direction), ...]]
        queue.append((person_a_id, []))
        
        while queue:
            current_id, path = queue.popleft()
            
            # 探索家庭关系（父母）
            parent_relations = self.db.query(FamilyRelation).filter(
                FamilyRelation.person_b_id == current_id,
                FamilyRelation.relation.in_([FamilyRelationType.FATHER, FamilyRelationType.MOTHER])
            ).all()
            
            for rel in parent_relations:
                if rel.person_a_id not in visited:
                    new_path = path + [(rel.relation, rel.relation_nature, "up")]
                    if rel.person_a_id == person_b_id:
                        return self._path_to_relation_name(new_path, person_b_id, "up")
                    visited.add(rel.person_a_id)
                    queue.append((rel.person_a_id, new_path))
            
            # 探索家庭关系（子女）
            child_relations = self.db.query(FamilyRelation).filter(
                FamilyRelation.person_a_id == current_id,
                FamilyRelation.relation.in_([FamilyRelationType.SON, FamilyRelationType.DAUGHTER])
            ).all()
            
            for rel in child_relations:
                if rel.person_b_id not in visited:
                    new_path = path + [(rel.relation, rel.relation_nature, "down")]
                    if rel.person_b_id == person_b_id:
                        return self._path_to_relation_name(new_path, person_b_id, "down")
                    visited.add(rel.person_b_id)
                    queue.append((rel.person_b_id, new_path))
            
            # 探索配偶关系
            spouse_relations = self.db.query(SpouseRelation).filter(
                or_(
                    SpouseRelation.person_a_id == current_id,
                    SpouseRelation.person_b_id == current_id
                )
            ).all()
            
            for rel in spouse_relations:
                next_id = rel.person_b_id if rel.person_a_id == current_id else rel.person_a_id
                if next_id not in visited:
                    new_path = path + [(rel.relation, rel.relation_nature, "spouse")]
                    if next_id == person_b_id:
                        return self._path_to_relation_name(new_path, person_b_id, "spouse")
                    visited.add(next_id)
                    queue.append((next_id, new_path))
        
        return None
    
    def _path_to_relation_name(self, path: List, target_id: int, last_direction: str) -> Dict:
        """将路径转换为关系名称"""
        if not path:
            return {"relation_name": "未知", "level": 0, "is_blood": False}
        
        person_b = self.db.query(Person).filter(Person.id == target_id).first()
        is_blood = all(p[1] == RelationNature.BIOLOGICAL for p in path)
        
        # 根据路径长度和模式确定关系
        if len(path) == 1:
            # 直接关系（通常在上面已经处理）
            pass
        
        elif len(path) == 2:
            # 祖父/祖母/兄弟姐妹/叔伯姑舅姨
            if path[0][2] == "up" and path[1][2] == "up":
                # 祖父/祖母
                p1_type = path[0][0]
                p2_type = path[1][0]
                if p1_type == FamilyRelationType.FATHER and p2_type == FamilyRelationType.FATHER:
                    return {"relation_name": "祖父", "level": 2, "is_blood": is_blood}
                elif p1_type == FamilyRelationType.FATHER and p2_type == FamilyRelationType.MOTHER:
                    return {"relation_name": "祖母", "level": 2, "is_blood": is_blood}
                elif p1_type == FamilyRelationType.MOTHER and p2_type == FamilyRelationType.FATHER:
                    return {"relation_name": "外祖父", "level": 2, "is_blood": is_blood}
                elif p1_type == FamilyRelationType.MOTHER and p2_type == FamilyRelationType.MOTHER:
                    return {"relation_name": "外祖母", "level": 2, "is_blood": is_blood}
            
            elif path[0][2] == "up" and path[1][2] == "down":
                # 兄弟姐妹
                gender = person_b.gender if person_b else 1
                if gender == 1:
                    return {"relation_name": "哥哥/弟弟", "level": 1, "is_blood": is_blood}
                else:
                    return {"relation_name": "姐姐/妹妹", "level": 1, "is_blood": is_blood}
            
            elif path[0][2] == "down" and path[1][2] == "down":
                # 孙辈
                gender = person_b.gender if person_b else 1
                if gender == 1:
                    return {"relation_name": "孙子", "level": 2, "is_blood": is_blood}
                else:
                    return {"relation_name": "孙女", "level": 2, "is_blood": is_blood}
        
        elif len(path) == 3:
            if path[0][2] == "up" and path[1][2] == "up" and path[2][2] == "up":
                # 曾祖辈
                return {"relation_name": "曾祖辈", "level": 3, "is_blood": is_blood}
            
            elif path[0][2] == "up" and path[1][2] == "up" and path[2][2] == "down":
                # 叔伯姑舅姨
                parent_type = path[1][0]
                gender = person_b.gender if person_b else 1
                if parent_type == FamilyRelationType.FATHER:
                    if gender == 1:
                        return {"relation_name": "叔叔/伯伯", "level": 2, "is_blood": is_blood}
                    else:
                        return {"relation_name": "姑姑", "level": 2, "is_blood": is_blood}
                else:
                    if gender == 1:
                        return {"relation_name": "舅舅", "level": 2, "is_blood": is_blood}
                    else:
                        return {"relation_name": "阿姨", "level": 2, "is_blood": is_blood}
            
            elif path[0][2] == "up" and path[1][2] == "spouse" and path[2][2] == "up":
                # 配偶的父母 = 公婆/岳父母
                gender = person_b.gender if person_b else 1
                if gender == 1:
                    return {"relation_name": "公公", "level": 2, "is_blood": False}
                else:
                    return {"relation_name": "婆婆", "level": 2, "is_blood": False}
            
            elif path[0][2] == "down" and path[1][2] == "down" and path[2][2] == "down":
                # 曾孙辈
                return {"relation_name": "曾孙辈", "level": 3, "is_blood": is_blood}
        
        elif len(path) == 4:
            if path[0][2] == "down" and path[1][2] == "spouse" and path[2][2] == "spouse" and path[3][2] == "down":
                # 配偶的子女 = 继子继女
                gender = person_b.gender if person_b else 1
                if gender == 1:
                    return {"relation_name": "继子", "level": 2, "is_blood": False}
                else:
                    return {"relation_name": "继女", "level": 2, "is_blood": False}
        
        # 默认返回远亲
        return {
            "relation_name": "远亲",
            "level": len(path),
            "is_blood": is_blood
        }
    
    def get_family_tree(self) -> Dict:
        """
        获取家族树结构
        
        Returns:
            包含节点和边的字典，用于D3.js可视化
        """
        nodes = []
        edges = []
        
        # 获取所有人物
        persons = self.db.query(Person).all()
        for person in persons:
            nodes.append({
                "id": person.id,
                "name": person.nickname or f"{person.last_name or ''}{person.first_name or ''}",
                "gender": person.gender,
                "birth_date": person.birth_date.isoformat() if person.birth_date else None,
                "death_date": person.death_date.isoformat() if person.death_date else None,
                "is_me": person.is_me
            })
        
        # 获取所有家庭关系
        family_relations = self.db.query(FamilyRelation).filter(
            FamilyRelation.relation.in_([FamilyRelationType.FATHER, FamilyRelationType.MOTHER])
        ).all()
        
        for rel in family_relations:
            edges.append({
                "source": rel.person_a_id,
                "target": rel.person_b_id,
                "relation_type": rel.relation,
                "relation_nature": rel.relation_nature
            })
        
        # 获取所有配偶关系
        spouse_relations = self.db.query(SpouseRelation).all()
        
        for rel in spouse_relations:
            edges.append({
                "source": rel.person_a_id,
                "target": rel.person_b_id,
                "relation_type": f"spouse_{rel.relation}",
                "relation_nature": rel.relation_nature,
                "is_spouse": True
            })
        
        return {"nodes": nodes, "edges": edges}
    
    def _get_reverse_relation(self, relation: int) -> int:
        """获取反向关系类型"""
        reverse_map = {
            FamilyRelationType.FATHER: FamilyRelationType.SON,
            FamilyRelationType.MOTHER: FamilyRelationType.DAUGHTER,
            FamilyRelationType.SON: FamilyRelationType.FATHER,
            FamilyRelationType.DAUGHTER: FamilyRelationType.MOTHER
        }
        return reverse_map.get(relation, relation)
    
    def _get_reverse_spouse_relation(self, relation: int) -> int:
        """获取反向配偶关系类型"""
        reverse_map = {
            SpouseRelationType.HUSBAND: SpouseRelationType.WIFE,
            SpouseRelationType.WIFE: SpouseRelationType.HUSBAND,
            SpouseRelationType.CONCUBINE: SpouseRelationType.HUSBAND,
            SpouseRelationType.BOYFRIEND: SpouseRelationType.GIRLFRIEND,
            SpouseRelationType.GIRLFRIEND: SpouseRelationType.BOYFRIEND
        }
        return reverse_map.get(relation, relation)
    
    def _get_relation_name(self, relation: int, relation_nature: int, direction: str) -> str:
        """获取关系名称"""
        # 关系性质前缀
        nature_prefix = {
            RelationNature.BIOLOGICAL: "",
            RelationNature.STEP: "继",
            RelationNature.ADOPTIVE: "养",
            RelationNature.SWORN: "义",
            RelationNature.FOSTER: "干"
        }
        prefix = nature_prefix.get(relation_nature, "")
        
        # 基础关系名称
        if direction == "to_me":
            relation_names = {
                FamilyRelationType.FATHER: "父亲",
                FamilyRelationType.MOTHER: "母亲",
                FamilyRelationType.SON: "儿子",
                FamilyRelationType.DAUGHTER: "女儿"
            }
        else:  # from_a
            relation_names = {
                FamilyRelationType.FATHER: "父亲",
                FamilyRelationType.MOTHER: "母亲",
                FamilyRelationType.SON: "儿子",
                FamilyRelationType.DAUGHTER: "女儿"
            }
        
        name = relation_names.get(relation, "未知")
        return f"{prefix}{name}" if prefix else name
    
    def _get_spouse_relation_name(self, relation: int, direction: str) -> str:
        """获取配偶关系名称"""
        if direction == "to_me" or direction == "from_a":
            relation_names = {
                SpouseRelationType.HUSBAND: "丈夫",
                SpouseRelationType.WIFE: "妻子",
                SpouseRelationType.CONCUBINE: "姨太太",
                SpouseRelationType.BOYFRIEND: "男朋友",
                SpouseRelationType.GIRLFRIEND: "女朋友"
            }
        else:  # from_b
            relation_names = {
                SpouseRelationType.HUSBAND: "妻子",
                SpouseRelationType.WIFE: "丈夫",
                SpouseRelationType.CONCUBINE: "妻子",
                SpouseRelationType.BOYFRIEND: "女朋友",
                SpouseRelationType.GIRLFRIEND: "男朋友"
            }
        
        return relation_names.get(relation, "配偶")
