from fastapi import FastAPI, Depends, HTTPException, status, Query
from typing_extensions import TypedDict
from typing import Optional
from sqlmodel import Session, select
from datetime import datetime, timedelta

from models import (
    Participant, ParticipantBase, ParticipantWithSkills,
    Team, TeamBase, TeamWithParticipants,
    Skill, SkillBase, SkillWithParticipants,
    Task, TaskBase, TaskWithSubmissions,
    Submission, SubmissionBase, SubmissionWithRelations,
    ParticipantSkillLink, TeamParticipantLink,
    User, UserCreate, UserResponse, UserUpdate, UserLogin, Token,
    ParticipantType
)
from connection import get_session, init_db
from auth import (
    get_password_hash, verify_password, create_access_token,
    authenticate_user, get_current_user, get_current_active_user,
    get_current_superuser, ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI()


def get_pagination_filter(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    name: Optional[str] = Query(None, description="Filter by participant name (partial match)"),
    email: Optional[str] = Query(None, description="Filter by exact email"),
    phone: Optional[str] = Query(None, description="Filter by phone number (partial match)"),
    type: Optional[ParticipantType] = Query(None, description="Filter by participant type")
):
    """Dependency for pagination and filtering parameters"""
    return {
        "skip": skip,
        "limit": limit,
        "name": name,
        "email": email,
        "phone": phone,
        "type": type
    }


def get_team_filter(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    name: Optional[str] = Query(None, description="Filter by team name (partial match)"),
    description: Optional[str] = Query(None, description="Filter by team description (partial match)")
):
    """Dependency for team pagination and filtering parameters"""
    return {
        "skip": skip,
        "limit": limit,
        "name": name,
        "description": description
    }


@app.on_event("startup")
def on_startup():
    """Initialize database on startup"""
    init_db()


@app.get('/', tags=["General"])
def hello():
    return 'Hackathon Management System API'


@app.post("/register", response_model=UserResponse, tags=["Authentication"])
def register(user: UserCreate, session: Session = Depends(get_session)):
    """Register a new user."""
    existing_user = session.exec(select(User).where(User.username == user.username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    existing_email = session.exec(select(User).where(User.email == user.email)).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.post("/login", response_model=Token, tags=["Authentication"])
def login(user_data: UserLogin, session: Session = Depends(get_session)):
    """Login user and return JWT token."""
    user = authenticate_user(session, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse, tags=["Users"])
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@app.get("/users", response_model=list[UserResponse], tags=["Users"])
def read_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """Get list of all users (admin only)."""
    users = session.exec(select(User)).all()
    return users


@app.put("/users/me", response_model=UserResponse, tags=["Users"])
def update_user_me(
    user_update: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update current user profile."""
    user_data = user_update.model_dump(exclude_unset=True, exclude={"password"})
    
    # Handle password update separately
    if user_update.password:
        current_user.hashed_password = get_password_hash(user_update.password)
    
    for key, value in user_data.items():
        setattr(current_user, key, value)
    
    current_user.updated_at = datetime.utcnow().isoformat()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@app.put("/users/me/password", tags=["Users"])
def change_password(
    old_password: str,
    new_password: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Change user password."""
    # Verify old password
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    current_user.updated_at = datetime.utcnow().isoformat()
    session.add(current_user)
    session.commit()
    return {"message": "Password updated successfully"}


@app.get("/participants", response_model=list[Participant], tags=["Participants"])
def participants_list(
    pagination: dict = Depends(get_pagination_filter),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> list[Participant]:
    """Get participants with pagination and filtering"""
    query = select(Participant)
    
    if pagination["name"]:
        query = query.where(Participant.name.ilike(f"%{pagination['name']}%"))
    if pagination["email"]:
        query = query.where(Participant.email == pagination["email"])
    if pagination["phone"]:
        query = query.where(Participant.phone.ilike(f"%{pagination['phone']}%"))
    if pagination["type"]:
        query = query.where(Participant.type == pagination["type"])
    
    query = query.offset(pagination["skip"]).limit(pagination["limit"])
    
    participants = session.exec(query).all()
    return participants


@app.get("/participant/{participant_id}", response_model=ParticipantWithSkills, tags=["Participants"])
def participant_get(
    participant_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> Participant:
    """Get participant by ID with skills"""
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@app.post("/participant", tags=["Participants"])
def participant_create(
    participant: ParticipantBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> TypedDict('Response', {"status": int, "data": Participant}):
    """Create a new participant"""
    db_participant = Participant.model_validate(participant)
    session.add(db_participant)
    session.commit()
    session.refresh(db_participant)
    return {"status": 200, "data": db_participant}


@app.patch("/participant/{participant_id}", tags=["Participants"])
def participant_update(
    participant_id: int,
    participant: ParticipantBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> Participant:
    """Update participant partially"""
    db_participant = session.get(Participant, participant_id)
    if not db_participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    participant_data = participant.model_dump(exclude_unset=True)
    for key, value in participant_data.items():
        setattr(db_participant, key, value)

    session.add(db_participant)
    session.commit()
    session.refresh(db_participant)
    return db_participant


@app.delete("/participant/{participant_id}", tags=["Participants"])
def participant_delete(
    participant_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete participant"""
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    session.delete(participant)
    session.commit()
    return {"status": 200, "message": "Participant deleted successfully"}


@app.get("/teams", response_model=list[Team], tags=["Teams"])
def teams_list(
    filter_params: dict = Depends(get_team_filter),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> list[Team]:
    """Get teams with pagination and filtering"""
    query = select(Team)
    
    if filter_params["name"]:
        query = query.where(Team.name.ilike(f"%{filter_params['name']}%"))
    if filter_params["description"]:
        query = query.where(Team.description.ilike(f"%{filter_params['description']}%"))
    
    query = query.offset(filter_params["skip"]).limit(filter_params["limit"])
    
    teams = session.exec(query).all()
    return teams


@app.get("/team/{team_id}", response_model=TeamWithParticipants, tags=["Teams"])
def team_get(
    team_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> TeamWithParticipants:
    """Get team by ID with participants"""
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    _ = team.participants
    return team


@app.post("/team", tags=["Teams"])
def team_create(
    team: TeamBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> TypedDict('Response', {"status": int, "data": Team}):
    """Create a new team"""
    db_team = Team.model_validate(team)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return {"status": 200, "data": db_team}


@app.patch("/team/{team_id}", tags=["Teams"])
def team_update(
    team_id: int,
    team: TeamBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> Team:
    """Update team partially"""
    db_team = session.get(Team, team_id)
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")

    team_data = team.model_dump(exclude_unset=True)
    for key, value in team_data.items():
        setattr(db_team, key, value)

    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@app.delete("/team/{team_id}", tags=["Teams"])
def team_delete(
    team_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete team"""
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    session.delete(team)
    session.commit()
    return {"status": 200, "message": "Team deleted successfully"}


@app.get("/skills", response_model=list[Skill], tags=["Skills"])
def skills_list(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> list[Skill]:
    """Get all skills"""
    return session.exec(select(Skill)).all()


@app.get("/skill/{skill_id}", response_model=SkillWithParticipants, tags=["Skills"])
def skill_get(
    skill_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> SkillWithParticipants:
    """Get skill by ID with participants"""
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    _ = skill.participants
    return skill


@app.post("/skill", tags=["Skills"])
def skill_create(
    skill: SkillBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> TypedDict('Response', {"status": int, "data": Skill}):
    """Create a new skill"""
    db_skill = Skill.model_validate(skill)
    session.add(db_skill)
    session.commit()
    session.refresh(db_skill)
    return {"status": 200, "data": db_skill}


@app.patch("/skill/{skill_id}", tags=["Skills"])
def skill_update(
    skill_id: int,
    skill: SkillBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> Skill:
    """Update skill partially"""
    db_skill = session.get(Skill, skill_id)
    if not db_skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    skill_data = skill.model_dump(exclude_unset=True)
    for key, value in skill_data.items():
        setattr(db_skill, key, value)

    session.add(db_skill)
    session.commit()
    session.refresh(db_skill)
    return db_skill


@app.delete("/skill/{skill_id}", tags=["Skills"])
def skill_delete(
    skill_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete skill"""
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    session.delete(skill)
    session.commit()
    return {"status": 200, "message": "Skill deleted successfully"}


@app.get("/tasks", response_model=list[Task], tags=["Tasks"])
def tasks_list(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> list[Task]:
    """Get all tasks"""
    return session.exec(select(Task)).all()


@app.get("/task/{task_id}", response_model=TaskWithSubmissions, tags=["Tasks"])
def task_get(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> TaskWithSubmissions:
    """Get task by ID with submissions"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Trigger loading of submissions
    _ = task.submissions
    return task


@app.post("/task", tags=["Tasks"])
def task_create(
    task: TaskBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> TypedDict('Response', {"status": int, "data": Task}):
    """Create a new task"""
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return {"status": 200, "data": db_task}


@app.patch("/task/{task_id}", tags=["Tasks"])
def task_update(
    task_id: int,
    task: TaskBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> Task:
    """Update task partially"""
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = task.model_dump(exclude_unset=True)
    for key, value in task_data.items():
        setattr(db_task, key, value)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@app.delete("/task/{task_id}", tags=["Tasks"])
def task_delete(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete task"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()
    return {"status": 200, "message": "Task deleted successfully"}


@app.get("/submissions", response_model=list[Submission], tags=["Submissions"])
def submissions_list(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> list[Submission]:
    """Get all submissions"""
    return session.exec(select(Submission)).all()


@app.get("/submission/{submission_id}", response_model=SubmissionWithRelations, tags=["Submissions"])
def submission_get(
    submission_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> SubmissionWithRelations:
    """Get submission by ID with relations"""
    submission = session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    # Trigger loading of relations
    _ = submission.task
    _ = submission.team
    _ = submission.participant
    return submission


@app.post("/submission", tags=["Submissions"])
def submission_create(
    submission: SubmissionBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> TypedDict('Response', {"status": int, "data": Submission}):
    """Create a new submission"""
    db_submission = Submission.model_validate(submission)
    session.add(db_submission)
    session.commit()
    session.refresh(db_submission)
    return {"status": 200, "data": db_submission}


@app.patch("/submission/{submission_id}", tags=["Submissions"])
def submission_update(
    submission_id: int,
    submission: SubmissionBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> Submission:
    """Update submission partially"""
    db_submission = session.get(Submission, submission_id)
    if not db_submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    submission_data = submission.model_dump(exclude_unset=True)
    for key, value in submission_data.items():
        setattr(db_submission, key, value)

    session.add(db_submission)
    session.commit()
    session.refresh(db_submission)
    return db_submission


@app.delete("/submission/{submission_id}", tags=["Submissions"])
def submission_delete(
    submission_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete submission"""
    submission = session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    session.delete(submission)
    session.commit()
    return {"status": 200, "message": "Submission deleted successfully"}


@app.post("/participant/{participant_id}/skill/{skill_id}", tags=["Relationships"])
def add_skill_to_participant(
    participant_id: int,
    skill_id: int,
    proficiency_level: int = 1,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Add a skill to a participant (many-to-many)"""
    participant = session.get(Participant, participant_id)
    skill = session.get(Skill, skill_id)

    if not participant or not skill:
        raise HTTPException(status_code=404, detail="Participant or Skill not found")

    # Check if relationship already exists
    existing = session.exec(
        select(ParticipantSkillLink).where(
            ParticipantSkillLink.participant_id == participant_id,
            ParticipantSkillLink.skill_id == skill_id
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Skill already added to participant")

    # Create the relationship
    link = ParticipantSkillLink(
        participant_id=participant_id,
        skill_id=skill_id,
        proficiency_level=proficiency_level
    )
    session.add(link)
    session.commit()

    return {"status": 200, "message": "Skill added to participant successfully"}


@app.post("/team/{team_id}/participant/{participant_id}", tags=["Relationships"])
def add_participant_to_team(
    team_id: int,
    participant_id: int,
    role: str = "member",
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Add a participant to a team (many-to-many)"""
    team = session.get(Team, team_id)
    participant = session.get(Participant, participant_id)
    
    if not team or not participant:
        raise HTTPException(status_code=404, detail="Team or Participant not found")
    
    # Check if relationship already exists
    existing = session.exec(
        select(TeamParticipantLink).where(
            TeamParticipantLink.team_id == team_id,
            TeamParticipantLink.participant_id == participant_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Participant already in team")
    
    # Create the relationship
    link = TeamParticipantLink(
        team_id=team_id,
        participant_id=participant_id,
        role=role
    )
    session.add(link)
    session.commit()
    
    return {"status": 200, "message": "Participant added to team successfully"}


@app.get("/participant/{participant_id}/teams", response_model=list[Team], tags=["Relationships"])
def get_participant_teams(
    participant_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all teams for a participant"""
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant.teams


@app.get("/team/{team_id}/participants", response_model=list[Participant], tags=["Relationships"])
def get_team_participants(
    team_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all participants in a team"""
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team.participants


@app.get("/task/{task_id}/submissions", response_model=list[Submission], tags=["Relationships"])
def get_task_submissions(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all submissions for a task"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.submissions
