from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class OrganizationCreate(BaseModel):
    name: str
    personal: Optional[bool] = False

class MemberCreate(BaseModel):
    org_id: int
    user_id: int
    role_id: int

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    org_id: int
