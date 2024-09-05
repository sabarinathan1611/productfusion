from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, JSON, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from .sendmail import send_email

# Configuration
DATABASE_URL = "postgresql://postgres:1234@localhost/productfusion"  
SECRET_KEY = "#&GACSG#T@e623weyg"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    profile = Column(JSON, default={}, nullable=False)
    status = Column(Integer, default=0, nullable=False)
    settings = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)
    organizations = relationship("Member", back_populates="user")

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(Integer, default=0, nullable=False)
    personal = Column(Boolean, default=False, nullable=True)
    settings = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)
    members = relationship("Member", back_populates="organization")

class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    status = Column(Integer, nullable=False, default=0)
    settings = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organizations")
    role = relationship("Role", back_populates="members")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    members = relationship("Member", back_populates="role")

# Create the database tables
Base.metadata.create_all(bind=engine)

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI app
app = FastAPI()

# Endpoints

@app.post("/signup/")
def signup(email: str, password: str, org_name: str, db: Session = Depends(get_db)):
    user = get_user(db, email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(password)
    new_user = User(email=email, hashed_password=hashed_password, created_at=int(datetime.utcnow().timestamp()))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_org = Organization(name=org_name, created_at=int(datetime.utcnow().timestamp()))
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    owner_role = Role(name="Owner", org_id=new_org.id)
    db.add(owner_role)
    db.commit()
    db.refresh(owner_role)

    new_member = Member(org_id=new_org.id, user_id=new_user.id, role_id=owner_role.id, created_at=int(datetime.utcnow().timestamp()))
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    send_email(to_email=email, message="Welcome to Our SaaS Platform",subject= "Thank you for signing up!")
    return {"msg": "User and organization created successfully"}

@app.post("/token/")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/reset-password/")
def reset_password(email: str, new_password: str, db: Session = Depends(get_db)):
    user = get_user(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    send_email(to_email=email, message="Password reset successful",subject= "Password reset ")
    
    return {"msg": "Password reset successful"}

@app.post("/invite-member/")
def invite_member(email: str, org_id: int, role_name: str, db: Session = Depends(get_db)):
    user = get_user(db, email)
    if not user:
        hashed_password = get_password_hash("temporarypassword")
        user = User(email=email, hashed_password=hashed_password, created_at=int(datetime.utcnow().timestamp()))
        db.add(user)
        db.commit()
        db.refresh(user)

    role = db.query(Role).filter(Role.name == role_name, Role.org_id == org_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found in the organization")
    
    new_member = Member(org_id=org_id, user_id=user.id, role_id=role.id, created_at=int(datetime.utcnow().timestamp()))
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    send_email(to_email=email, message="Member invited successfully",subject= "Member invited!")

    return {"msg": "Member invited successfully"}

@app.delete("/delete-member/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"msg": "Member deleted successfully"}

@app.put("/update-member-role/{member_id}")
def update_member_role(member_id: int, new_role_name: str, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    new_role = db.query(Role).filter(Role.name == new_role_name, Role.org_id == member.org_id).first()
    if not new_role:
        raise HTTPException(status_code=404, detail="Role not found in the organization")
    
    member.role_id = new_role.id
    db.commit()
    send_email(to_email=member.email, message="Member role updated successfully",subject= "Member role updated !")

    return {"msg": "Member role updated successfully"}

@app.get("/stats/role-wise-users/")
def role_wise_users(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    result = {role.name: db.query(Member).filter(Member.role_id == role.id).count() for role in roles}
    return result

@app.get("/stats/org-wise-members/")
def org_wise_members(db: Session = Depends(get_db)):
    organizations = db.query(Organization).all()
    result = {org.name: db.query(Member).filter(Member.org_id == org.id).count() for org in organizations}
    return result

@app.get("/stats/org-role-wise-users/")
def org_role_wise_users(db: Session = Depends(get_db), from_time: Optional[int] = None, to_time: Optional[int] = None, status: Optional[int] = None):
    query = db.query(Member)
    if from_time:
        query = query.filter(Member.created_at >= from_time)
    if to_time:
        query = query.filter(Member.created_at <= to_time)
    if status is not None:
        query = query.filter(Member.status == status)

    organizations = db.query(Organization).all()
    result = {}
    for org in organizations:
        org_roles = {}
        roles = db.query(Role).filter(Role.org_id == org.id).all()
        for role in roles:
            count = query.filter(Member.org_id == org.id, Member.role_id == role.id).count()
            org_roles[role.name] = count
        result[org.name] = org_roles
    return result
