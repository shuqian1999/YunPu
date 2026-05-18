from sqlalchemy.orm import Session
from app.models.family_member import FamilyMember
from app.models.family_relation import FamilyRelation
from app.models.family_calculated_relation import FamilyCalculatedRelation
from app.models.person import Person
from typing import Dict, List, Optional
from collections import deque

class FamilyService:
    def __init__(self, db: Session):
        self.db = db
    
    def recalculate_all_relations(self, user_id: int):
        me_person = self.db.query(Person).filter(
            Person.user_id == user_id,
            Person.is_me == True
        ).first()
        
        if not me_person:
            return
        
        me_member = self.db.query(FamilyMember).filter(
            FamilyMember.person_id == me_person.id,
            FamilyMember.user_id == user_id
        ).first()
        
        if not me_member:
            return
        
        self.db.query(FamilyCalculatedRelation).filter(
            FamilyCalculatedRelation.user_id == user_id
        ).delete()
        
        all_members = self.db.query(FamilyMember).filter(
            FamilyMember.user_id == user_id
        ).all()
        
        for member in all_members:
            if member.id == me_member.id:
                continue
            
            relation = self._calculate_relation(me_member, member)
            if relation:
                calculated_relation = FamilyCalculatedRelation(
                    user_id=user_id,
                    person_id=member.person_id,
                    relation_name=relation['name'],
                    relation_level=relation['level'],
                    relation_path=relation['path'],
                    is_blood=relation['is_blood']
                )
                self.db.add(calculated_relation)
        
        self.db.commit()
    
    def _calculate_relation(self, from_member: FamilyMember, to_member: FamilyMember) -> Optional[Dict]:
        from_member_person = self.db.query(Person).filter(Person.id == from_member.person_id).first()
        to_member_person = self.db.query(Person).filter(Person.id == to_member.person_id).first()
        
        if not from_member_person or not to_member_person:
            return None
        
        is_direct_child = self._is_direct_child(from_member, to_member)
        if is_direct_child:
            gender = to_member_person.gender
            return {
                'name': '儿子' if gender == 1 else '女儿',
                'level': 1,
                'path': 'child',
                'is_blood': is_direct_child['is_blood']
            }
        
        is_direct_parent = self._is_direct_parent(from_member, to_member)
        if is_direct_parent:
            return {
                'name': '父亲' if is_direct_parent['parent_type'] == 'father' else '母亲',
                'level': 1,
                'path': 'parent',
                'is_blood': is_direct_parent['is_blood']
            }
        
        is_sibling = self._is_sibling(from_member, to_member)
        if is_sibling:
            gender = to_member_person.gender
            return {
                'name': '哥哥/弟弟' if gender == 1 else '姐姐/妹妹',
                'level': 1,
                'path': 'sibling',
                'is_blood': is_sibling['is_blood']
            }
        
        path = self._find_path(from_member, to_member)
        if path:
            return self._path_to_relation(path, from_member_person, to_member_person)
        
        return None
    
    def _is_direct_child(self, from_member: FamilyMember, to_member: FamilyMember) -> Optional[Dict]:
        relation = self.db.query(FamilyRelation).filter(
            FamilyRelation.parent_id == from_member.id,
            FamilyRelation.child_id == to_member.id,
            FamilyRelation.user_id == from_member.user_id
        ).first()
        
        if relation:
            return {'is_blood': relation.relation_nature == 'qin'}
        return None
    
    def _is_direct_parent(self, from_member: FamilyMember, to_member: FamilyMember) -> Optional[Dict]:
        relation = self.db.query(FamilyRelation).filter(
            FamilyRelation.parent_id == to_member.id,
            FamilyRelation.child_id == from_member.id,
            FamilyRelation.user_id == from_member.user_id
        ).first()
        
        if relation:
            return {'parent_type': relation.parent_type, 'is_blood': relation.relation_nature == 'qin'}
        return None
    
    def _is_sibling(self, member1: FamilyMember, member2: FamilyMember) -> Optional[Dict]:
        parents1 = self.db.query(FamilyRelation).filter(
            FamilyRelation.child_id == member1.id,
            FamilyRelation.user_id == member1.user_id
        ).all()
        
        parents2 = self.db.query(FamilyRelation).filter(
            FamilyRelation.child_id == member2.id,
            FamilyRelation.user_id == member2.user_id
        ).all()
        
        parent_ids1 = {p.parent_id for p in parents1}
        parent_ids2 = {p.parent_id for p in parents2}
        
        common_parents = parent_ids1 & parent_ids2
        if common_parents:
            is_blood = all(self.db.query(FamilyRelation).filter(
                FamilyRelation.parent_id == parent_id,
                FamilyRelation.child_id.in_([member1.id, member2.id]),
                FamilyRelation.relation_nature == 'qin'
            ).count() == 2 for parent_id in common_parents)
            return {'is_blood': is_blood}
        
        return None
    
    def _find_path(self, from_member: FamilyMember, to_member: FamilyMember) -> Optional[List]:
        queue = deque([(from_member, [])])
        visited = {from_member.id}
        
        while queue:
            current, path = queue.popleft()
            
            if current.id == to_member.id:
                return path
            
            parents = self.db.query(FamilyRelation).filter(
                FamilyRelation.child_id == current.id,
                FamilyRelation.user_id == current.user_id
            ).all()
            
            for parent_relation in parents:
                parent_member = self.db.query(FamilyMember).filter(
                    FamilyMember.id == parent_relation.parent_id
                ).first()
                if parent_member and parent_member.id not in visited:
                    visited.add(parent_member.id)
                    queue.append((parent_member, path + [('up', parent_relation)]))
            
            children = self.db.query(FamilyRelation).filter(
                FamilyRelation.parent_id == current.id,
                FamilyRelation.user_id == current.user_id
            ).all()
            
            for child_relation in children:
                child_member = self.db.query(FamilyMember).filter(
                    FamilyMember.id == child_relation.child_id
                ).first()
                if child_member and child_member.id not in visited:
                    visited.add(child_member.id)
                    queue.append((child_member, path + [('down', child_relation)]))
        
        return None
    
    def _path_to_relation(self, path: List, from_person: Person, to_person: Person) -> Dict:
        is_blood = all(step[1].relation_nature == 'qin' for step in path)
        
        if len(path) == 2:
            if path[0][0] == 'up' and path[1][0] == 'down':
                parent_relation = path[0][1]
                if parent_relation.parent_type == 'father':
                    if to_person.gender == 1:
                        return {'name': '哥哥/弟弟', 'level': 1, 'path': 'sibling', 'is_blood': is_blood}
                    else:
                        return {'name': '姐姐/妹妹', 'level': 1, 'path': 'sibling', 'is_blood': is_blood}
        
        if len(path) == 2:
            if path[0][0] == 'up' and path[1][0] == 'up':
                r1, r2 = path[0][1], path[1][1]
                if r1.parent_type == 'father' and r2.parent_type == 'father':
                    return {'name': '祖父', 'level': 2, 'path': 'grandfather', 'is_blood': is_blood}
                elif r1.parent_type == 'father' and r2.parent_type == 'mother':
                    return {'name': '祖母', 'level': 2, 'path': 'grandmother', 'is_blood': is_blood}
                elif r1.parent_type == 'mother' and r2.parent_type == 'father':
                    return {'name': '外祖父', 'level': 2, 'path': 'maternal_grandfather', 'is_blood': is_blood}
                elif r1.parent_type == 'mother' and r2.parent_type == 'mother':
                    return {'name': '外祖母', 'level': 2, 'path': 'maternal_grandmother', 'is_blood': is_blood}
        
        if len(path) == 2:
            if path[0][0] == 'down' and path[1][0] == 'down':
                r1, r2 = path[0][1], path[1][1]
                if to_person.gender == 1:
                    return {'name': '孙子', 'level': 2, 'path': 'grandson', 'is_blood': is_blood}
                else:
                    return {'name': '孙女', 'level': 2, 'path': 'granddaughter', 'is_blood': is_blood}
        
        if len(path) == 3:
            if path[0][0] == 'up' and path[1][0] == 'up' and path[2][0] == 'up':
                return {'name': '曾祖辈', 'level': 3, 'path': 'great_grandparent', 'is_blood': is_blood}
        
        if len(path) == 3:
            if path[0][0] == 'up' and path[1][0] == 'up' and path[2][0] == 'down':
                parent_relation = path[1][1]
                if parent_relation.parent_type == 'father':
                    if to_person.gender == 1:
                        return {'name': '叔叔/伯伯', 'level': 2, 'path': 'uncle', 'is_blood': is_blood}
                    else:
                        return {'name': '姑姑', 'level': 2, 'path': 'aunt', 'is_blood': is_blood}
                else:
                    if to_person.gender == 1:
                        return {'name': '舅舅', 'level': 2, 'path': 'maternal_uncle', 'is_blood': is_blood}
                    else:
                        return {'name': '阿姨', 'level': 2, 'path': 'maternal_aunt', 'is_blood': is_blood}
        
        if len(path) == 3:
            if path[0][0] == 'up' and path[1][0] == 'down' and path[2][0] == 'down':
                if to_person.gender == 1:
                    return {'name': '侄子', 'level': 2, 'path': 'nephew', 'is_blood': is_blood}
                else:
                    return {'name': '侄女', 'level': 2, 'path': 'niece', 'is_blood': is_blood}
        
        return {
            'name': '远亲',
            'level': len(path),
            'path': 'distant',
            'is_blood': is_blood
        }
    
    def add_family_member(self, user_id: int, person_id: int) -> FamilyMember:
        existing = self.db.query(FamilyMember).filter(
            FamilyMember.person_id == person_id,
            FamilyMember.user_id == user_id
        ).first()
        
        if existing:
            return existing
        
        member = FamilyMember(user_id=user_id, person_id=person_id)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def add_family_relation(self, user_id: int, parent_id: int, child_id: int, 
                           parent_type: str, relation_nature: str = "qin") -> FamilyRelation:
        relation = FamilyRelation(
            user_id=user_id,
            parent_id=parent_id,
            child_id=child_id,
            parent_type=parent_type,
            relation_nature=relation_nature
        )
        self.db.add(relation)
        self.db.commit()
        self.db.refresh(relation)
        return relation