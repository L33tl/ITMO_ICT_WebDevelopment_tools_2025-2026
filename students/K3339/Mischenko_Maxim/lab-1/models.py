from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import field_validator
from pydantic_core import PydanticCustomError
import re


class ParticipantType(Enum):
    programmer = "programmer"
    designer = "designer"
    manager = "manager"
    analyst = "analyst"


# Association table for many-to-many between Participant and Skill
class ParticipantSkillLink(SQLModel, table=True):
    participant_id: Optional[int] = Field(
        default=None, foreign_key="participant.id", primary_key=True
    )
    skill_id: Optional[int] = Field(
        default=None, foreign_key="skill.id", primary_key=True
    )
    proficiency_level: int = Field(default=1, ge=1, le=5)


# Association table for many-to-many between Team and Participant
class TeamParticipantLink(SQLModel, table=True):
    team_id: Optional[int] = Field(
        default=None, foreign_key="team.id", primary_key=True
    )
    participant_id: Optional[int] = Field(
        default=None, foreign_key="participant.id", primary_key=True
    )
    role: str = Field(default="member")


# Base models for POST requests (without table=True)
class SkillBase(SQLModel):
    name: str
    description: Optional[str] = ""


class TeamBase(SQLModel):
    name: str
    description: Optional[str] = ""


class ParticipantBase(SQLModel):
    name: str
    email: str = Field(max_length=255)
    phone: Optional[str] = None
    type: ParticipantType
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Simple email regex validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise PydanticCustomError(
                'email_error',
                'Invalid email format'
            )
        return v


class UserBase(SQLModel):
    username: str
    email: str = Field(max_length=255)
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Simple email regex validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise PydanticCustomError(
                'email_error',
                'Invalid email format'
            )
        return v


class TaskBase(SQLModel):
    title: str
    description: str
    requirements: str
    evaluation_criteria: str
    is_active: bool = True


class SubmissionBase(SQLModel):
    title: str
    description: str
    repository_url: Optional[str] = None
    demo_url: Optional[str] = None


# Table models with relationships
class Skill(SkillBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    participants: List["Participant"] = Relationship(
        back_populates="skills", link_model=ParticipantSkillLink
    )


class Team(TeamBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    participants: List["Participant"] = Relationship(
        back_populates="teams", link_model=TeamParticipantLink
    )
    submissions: List["Submission"] = Relationship(back_populates="team")


class Participant(ParticipantBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    skills: List[Skill] = Relationship(
        back_populates="participants", link_model=ParticipantSkillLink
    )
    teams: List[Team] = Relationship(
        back_populates="participants", link_model=TeamParticipantLink
    )
    submissions: List["Submission"] = Relationship(back_populates="participant")


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(nullable=False)
    created_at: Optional[str] = Field(default=None, nullable=True)
    updated_at: Optional[str] = Field(default=None, nullable=True)


class Task(TaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    submissions: List["Submission"] = Relationship(back_populates="task")


class Submission(SubmissionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: Optional[int] = Field(default=None, foreign_key="task.id")
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    participant_id: Optional[int] = Field(default=None, foreign_key="participant.id")
    
    task: Optional[Task] = Relationship(back_populates="submissions")
    team: Optional[Team] = Relationship(back_populates="submissions")
    participant: Optional[Participant] = Relationship(back_populates="submissions")


# Response models with nested relationships
class ParticipantWithSkills(ParticipantBase):
    id: int
    skills: List[Skill] = []


class ParticipantWithTeams(ParticipantBase):
    id: int
    teams: List[Team] = []


class TeamWithParticipants(TeamBase):
    id: int
    participants: List[Participant] = []


class SkillWithParticipants(SkillBase):
    id: int
    participants: List[Participant] = []


class TaskWithSubmissions(TaskBase):
    id: int
    submissions: List[Submission] = []


class SubmissionWithRelations(SubmissionBase):
    id: int
    task: Optional[Task] = None
    team: Optional[Team] = None
    participant: Optional[Participant] = None


# User response models
class UserResponse(UserBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserCreate(SQLModel):
    username: str
    email: str = Field(max_length=255)
    password: str
    full_name: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Simple email regex validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise PydanticCustomError(
                'email_error',
                'Invalid email format'
            )
        return v


class UserUpdate(SQLModel):
    email: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Simple email regex validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise PydanticCustomError(
                'email_error',
                'Invalid email format'
            )
        return v


class UserLogin(SQLModel):
    username: str
    password: str


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: Optional[str] = None
