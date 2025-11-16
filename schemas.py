"""
Database Schemas for Lily — Your AI Recruiter

Each Pydantic model represents a collection in the database.
Collection name = lowercase of class name.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class Role(BaseModel):
    title: str = Field(..., description="Role title")
    department: Optional[str] = Field(None, description="Department or team")
    location: Optional[str] = Field(None, description="Office/Remote")
    level: Optional[str] = Field(None, description="Seniority level")
    description: str = Field(..., description="Role description")
    requirements: List[str] = Field(default_factory=list, description="Key requirements/skills")
    created_at: Optional[datetime] = None

class Applicant(BaseModel):
    name: str
    email: EmailStr
    resume_text: Optional[str] = None
    selected_role_id: Optional[str] = None
    status: str = Field("applied", description="applied|interviewing|completed")
    created_at: Optional[datetime] = None

class Message(BaseModel):
    sender: str = Field(..., description="lily|candidate")
    text: str
    timestamp: Optional[datetime] = None

class Interview(BaseModel):
    applicant_id: str
    role_id: str
    mode: str = Field("chat", description="chat|voice|coding")
    messages: List[Message] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class Result(BaseModel):
    interview_id: str
    communication: int = Field(0, ge=0, le=100)
    problem_solving: int = Field(0, ge=0, le=100)
    technical: int = Field(0, ge=0, le=100)
    summary: str = Field("", description="Feedback summary")
    created_at: Optional[datetime] = None
