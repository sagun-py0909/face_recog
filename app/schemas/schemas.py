from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Person schemas
class PersonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class PersonCreate(PersonBase):
    pass

class PersonResponse(PersonBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# Attendance schemas
class AttendanceResponse(BaseModel):
    id: int
    person_id: int
    person_name: str
    timestamp: datetime
    confidence_score: Optional[float]
    
    class Config:
        orm_mode = True

# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Face recognition schemas
class CheckinRequest(BaseModel):
    image: str  # Base64 encoded image

class CheckinResponse(BaseModel):
    success: bool
    message: str
    person_name: Optional[str] = None
    confidence: Optional[float] = None

class AddPersonRequest(BaseModel):
    name: str
    frames: List[str]  # List of base64 encoded images

class AddPersonResponse(BaseModel):
    success: bool
    message: str
    person_id: Optional[int] = None
