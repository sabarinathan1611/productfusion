from sqlalchemy.orm import Session
from .models import Role

def create_initial_roles(db: Session):
    roles = [
        {"name": "Owner", "description": "Organization owner"},
        {"name": "Admin", "description": "Organization admin"},
        {"name": "Member", "description": "Organization member"}
    ]

    for role in roles:
        # Check if role already exists
        db_role = db.query(Role).filter(Role.name == role["name"]).first()
        if not db_role:
            new_role = Role(name=role["name"], description=role["description"])
            db.add(new_role)
    db.commit()
