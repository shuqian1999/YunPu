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
        path = self._find_path(from_member, to_member)
        if not path:
            return None
        
        return self._path_to_relation(path)
    
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
                    queue.append((parent_member, path + [parent_relation]))
            
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
                    queue.append((child_member, path + [child_relation]))
        
        return None
    
    def _path_to_relation(self, path: List[FamilyRelation]) -> Dict:
        if not path:
            return {'name': '我', 'level': 0, 'path': '', 'is_blood': True}
        
        is_blood = all(r.relation_nature == 'qin' for r in path)
        
        if len(path) == 1:
            relation = path[0]
            if relation.parent_type == 'father':
                return {'name': '父亲', 'level': 1, 'path': 'father', 'is_blood': is_blood}
            else:
                return {'name': '母亲', 'level': 1, 'path': 'mother', 'is_blood': is_blood}
        
        return {
            'name': self._generate_relation_name(path),
            'level': len(path),
            'path': '->'.join([r.parent_type for r in path]),
            'is_blood': is_blood
        }
    
    def _generate_relation_name(self, path: List[FamilyRelation]) -> str:
        relations = []
        for r in path:
            if r.parent_type == 'father':
                relations.append('父')
            else:
                relations.append('母')
        
        if len(relations) == 2:
            if relations == ['父', '父']:
                return '祖父'
            elif relations == ['父', '母']:
                return '祖母'
            elif relations == ['母', '父']:
                return '外祖父'
            else:
                return '外祖母'
        elif len(relations) == 3:
            prefix = '曾'
            if relations[-2:] == ['父', '父']:
                return f'{prefix}祖父'
            elif relations[-2:] == ['父', '母']:
                return f'{prefix}祖母'
            elif relations[-2:] == ['母', '父']:
                return f'{prefix}外祖父'
            else:
                return f'{prefix}外祖母'
        else:
            return '远亲'
    
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