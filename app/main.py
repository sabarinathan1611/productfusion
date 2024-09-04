from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, crud, auth, database, email
from .database import engine, get_db
from .dependencies import get_db_session
from .roles import create_initial_roles

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@app.on_event("startup")
def on_startup():
    db = next(get_db_session())
    create_initial_roles(db)
@app.post("/signup/", response_model=schemas.UserCreate)
def signup(user: schemas.UserCreate, organization: schemas.OrganizationCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = crud.create_user(db=db, user=user)
    
    # Create organization and assign user as owner
    new_organization = crud.create_organization(db=db, organization=organization, owner_id=new_user.id)
    
    # Send welcome email
    email.send_email(user.email, "Welcome to our SaaS!", "Thanks for signing up!")
    
    return new_user

@app.post("/signin/")
def signin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = auth.authenticate_user(db=db, email=form_data.username, password=form_data.password)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/reset-password/")
def reset_password(email: str, new_password: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.password = auth.pwd_context.hash(new_password)
    db.commit()
    
    email.send_email(email, "Password Reset Successful", "Your password has been updated successfully.")
    
    return {"msg": "Password reset successfully"}

@app.post("/invite-member/")
def invite_member(member: schemas.MemberCreate, db: Session = Depends(get_db)):
    # Invite member to organization
    new_member = crud.add_member(db=db, member=member)
    
    # Send invite email
    invite_email = crud.get_user_by_id(db=db, user_id=member.user_id).email
    email.send_email(invite_email, "You've been invited!", "Join the organization.")
    
    return new_member

@app.delete("/delete-member/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    deleted_member = crud.delete_member(db=db, member_id=member_id)
    
    if not deleted_member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return {"msg": "Member deleted successfully"}

@app.put("/update-member-role/{member_id}")
def update_member_role(member_id: int, role_id: int, db: Session = Depends(get_db)):
    updated_member = crud.update_member_role(db=db, member_id=member_id, role_id=role_id)
    
    if not updated_member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return {"msg": "Member role updated successfully"}

@app.get("/stats/role-wise-users/")
def role_wise_users(db: Session = Depends(get_db)):
    stats = crud.get_role_wise_users(db=db)
    return stats

@app.get("/stats/org-wise-members/")
def org_wise_members(db: Session = Depends(get_db)):
    stats = crud.get_org_wise_members(db=db)
    return stats

@app.get("/stats/org-role-wise-users/")
def org_role_wise_users(db: Session = Depends(get_db), from_time: int = None, to_time: int = None, status: int = None):
    stats = crud.get_org_role_wise_users(db=db, from_time=from_time, to_time=to_time, status=status)
    return stats
