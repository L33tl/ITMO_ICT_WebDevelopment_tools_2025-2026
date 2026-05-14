from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from typing_extensions import TypedDict
from sqlmodel import Session, select
from datetime import datetime, timedelta
import aiohttp
import logging
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
import os

from models import (
    Participant, ParticipantBase, ParticipantWithSkills,
    Team, TeamBase, TeamWithParticipants,
    Skill, SkillBase, SkillWithParticipants,
    Task, TaskBase, TaskWithSubmissions,
    Submission, SubmissionBase, SubmissionWithRelations,
    ParticipantSkillLink, TeamParticipantLink,
    User, UserCreate, UserResponse, UserUpdate, UserLogin, Token
)
from connection import get_session, init_db
from auth import (
    get_password_hash, verify_password, create_access_token,
    authenticate_user, get_current_user, get_current_active_user,
    get_current_superuser, ACCESS_TOKEN_EXPIRE_MINUTES
)

try:
    from celery_config import celery_app
    from celery_tasks import parse_url_task, health_check_task, batch_parse_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not available. Async parsing will not work.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParseRequest(BaseModel):
    """Модель запроса для парсинга URL"""
    url: str

class AsyncParseRequest(BaseModel):
    """Модель запроса для асинхронного парсинга URL"""
    url: str = Field(..., description="URL для парсинга")
    callback_url: Optional[str] = Field(None, description="URL для callback уведомления о завершении")

class BatchParseRequest(BaseModel):
    """Модель запроса для пакетного парсинга URL"""
    urls: List[str] = Field(..., description="Список URL для парсинга")
    callback_url: Optional[str] = Field(None, description="URL для callback уведомления о завершении")

class TaskResponse(BaseModel):
    """Модель ответа с информацией о задаче"""
    task_id: str
    status: str
    message: str
    url: Optional[str] = None
    urls: Optional[List[str]] = None
    check_status_url: str

app = FastAPI()


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
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    current_user.hashed_password = get_password_hash(new_password)
    current_user.updated_at = datetime.utcnow().isoformat()
    session.add(current_user)
    session.commit()
    return {"message": "Password updated successfully"}


@app.get("/participants", response_model=list[Participant], tags=["Participants"])
def participants_list(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> list[Participant]:
    """Get all participants"""
    return session.exec(select(Participant)).all()


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
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> list[Team]:
    """Get all teams"""
    return session.exec(select(Team)).all()


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

    existing = session.exec(
        select(ParticipantSkillLink).where(
            ParticipantSkillLink.participant_id == participant_id,
            ParticipantSkillLink.skill_id == skill_id
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Skill already added to participant")

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
    
    existing = session.exec(
        select(TeamParticipantLink).where(
            TeamParticipantLink.team_id == team_id,
            TeamParticipantLink.participant_id == participant_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Participant already in team")
    
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


@app.post("/parse", tags=["Parsing"])
async def parse_url(
    parse_request: ParseRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Parse a URL by forwarding request to parser service.
    
    Accepts a URL in JSON body, sends it to parser service (http://parser:8001/parse),
    and returns the parsing results.
    """
    PARSER_SERVICE_URL = "http://parser-app:8001/parse"
    
    logger.info(f"Parsing URL: {parse_request.url} for user: {current_user.username}")
    
    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": parse_request.url}
            async with session.post(PARSER_SERVICE_URL, params=params, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Successfully parsed URL: {parse_request.url}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Parser service returned error: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Parser service error: {error_text}"
                    )
    except aiohttp.ClientConnectorError:
        logger.error("Cannot connect to parser service. Service may be down.")
        raise HTTPException(
            status_code=503,
            detail="Parser service is unavailable. Please try again later."
        )
    except aiohttp.ClientError as e:
        logger.error(f"HTTP client error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to communicate with parser service: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during parsing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/parse/async", tags=["Parsing"], response_model=TaskResponse)
async def parse_url_async(
    parse_request: AsyncParseRequest,
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """
    Асинхронный парсинг URL через Celery очередь.
    
    Принимает URL в теле запроса, ставит задачу в очередь Celery
    и возвращает идентификатор задачи для отслеживания статуса.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Celery service is not available. Async parsing is disabled."
        )
    
    logger.info(f"Starting async parsing of URL: {parse_request.url} for user: {current_user.username}")
    
    try:
        task = parse_url_task.delay(parse_request.url)
        task_id = task.id
        
        logger.info(f"Task {task_id} created for URL: {parse_request.url}")
        
        return TaskResponse(
            task_id=task_id,
            status="pending",
            message="Задача на парсинг URL поставлена в очередь",
            url=parse_request.url,
            check_status_url=f"http://localhost:5555/task/{task_id}"
        )
    except Exception as e:
        logger.error(f"Failed to create Celery task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create async parsing task: {str(e)}"
        )


@app.post("/parse/batch", tags=["Parsing"], response_model=TaskResponse)
async def parse_batch_urls(
    batch_request: BatchParseRequest,
    current_user: User = Depends(get_current_active_user)
) -> TaskResponse:
    """
    Пакетный асинхронный парсинг нескольких URL через Celery очередь.
    
    Принимает список URL в теле запроса, ставит задачу в очередь Celery
    и возвращает идентификатор задачи для отслеживания статуса.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Celery service is not available. Async parsing is disabled."
        )
    
    if not batch_request.urls:
        raise HTTPException(
            status_code=400,
            detail="Список URL не может быть пустым"
        )
    
    logger.info(f"Starting batch async parsing of {len(batch_request.urls)} URLs for user: {current_user.username}")
    
    try:
        task = batch_parse_task.delay(batch_request.urls)
        task_id = task.id
        
        logger.info(f"Batch task {task_id} created for {len(batch_request.urls)} URLs")
        
        return TaskResponse(
            task_id=task_id,
            status="pending",
            message=f"Задача на пакетный парсинг {len(batch_request.urls)} URL поставлена в очередь",
            urls=batch_request.urls,
            check_status_url=f"/tasks/{task_id}/status"
        )
    except Exception as e:
        logger.error(f"Failed to create Celery batch task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create async batch parsing task: {str(e)}"
        )


@app.get("/tasks/{task_id}/status", tags=["Tasks"])
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Получить статус задачи Celery по её идентификатору.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Celery service is not available. Task status checking is disabled."
        )
    
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
            "successful": task_result.successful(),
            "failed": task_result.failed()
        }
        
        if task_result.ready():
            if task_result.successful():
                response["result"] = task_result.result
            else:
                response["error"] = str(task_result.result) if task_result.result else "Unknown error"
        
        if hasattr(task_result, "info") and task_result.info:
            if isinstance(task_result.info, dict):
                response.update(task_result.info)
            else:
                response["info"] = task_result.info
        
        return response
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@app.get("/celery/health", tags=["Tasks"])
async def celery_health_check() -> Dict[str, Any]:
    """
    Проверка здоровья Celery worker.
    """
    if not CELERY_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "Celery is not configured"
        }
    
    try:
        task = health_check_task.delay()
        task_id = task.id
        
        return {
            "status": "healthy",
            "message": "Celery worker is responding",
            "task_id": task_id,
            "check_task_url": f"/tasks/{task_id}/status"
        }
    except Exception as e:
        logger.error(f"Celery health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Celery worker is not responding: {str(e)}"
        }
