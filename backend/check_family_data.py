
from app.core.database import SessionLocal
from app.models.person import Person
from app.models.family_member import FamilyMember
from app.models.family_relation import FamilyRelation
from app.models.user import User

db = SessionLocal()

print("=== Users ===")
users = db.query(User).all()
for u in users:
    print(f"User: {u.id}, {u.username}")

print("\n=== Persons ===")
persons = db.query(Person).all()
for p in persons:
    print(f"Person: {p.id}, {p.last_name}{p.first_name}, is_me: {p.is_me}")

print("\n=== FamilyMembers ===")
members = db.query(FamilyMember).all()
for m in members:
    print(f"Member: {m.id}, person_id: {m.person_id}, user_id: {m.user_id}")

print("\n=== FamilyRelations ===")
relations = db.query(FamilyRelation).all()
for r in relations:
    print(f"Relation: {r.id}, parent: {r.parent_id} -> child: {r.child_id}, type: {r.parent_type}")

db.close()

