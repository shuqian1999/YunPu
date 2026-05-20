from app.core.database import SessionLocal
from app.models.person import Person
from app.models.family_relation import FamilyRelation
from app.models.spouse_relation import SpouseRelation
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

print("\n=== FamilyRelations ===")
relations = db.query(FamilyRelation).all()
for r in relations:
    print(f"Relation: {r.id}, person_a: {r.person_a_id} -> person_b: {r.person_b_id}, relation: {r.relation}, nature: {r.relation_nature}")

print("\n=== SpouseRelations ===")
relations = db.query(SpouseRelation).all()
for r in relations:
    print(f"Relation: {r.id}, person_a: {r.person_a_id} -> person_b: {r.person_b_id}, relation: {r.relation}, nature: {r.relation_nature}")

db.close()