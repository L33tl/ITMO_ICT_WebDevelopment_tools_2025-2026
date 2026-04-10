from fastapi import FastAPI, Depends, HTTPException
from typing_extensions import TypedDict
from sqlmodel import Session, select

from models import (
    Participant, ParticipantBase, ParticipantWithSkills,
    Team, TeamBase, TeamWithParticipants,
    Skill, SkillBase, SkillWithParticipants,
    Task, TaskBase, TaskWithSubmissions,
    Submission, SubmissionBase, SubmissionWithRelations,
    ParticipantSkillLink, TeamParticipantLink
)
from connection import get_session, init_db

app = FastAPI()


@app.on_event("startup")
def on_startup():
    """Initialize database on startup"""
    init_db()


@app.get('/')
def hello():
    return 'Hackathon Management System API'


@app.get("/participants", response_model=list[Participant])
def participants_list(session: Session = Depends(get_session)) -> list[Participant]:
    """Get all participants"""
    return session.exec(select(Participant)).all()


@app.get("/participant/{participant_id}", response_model=ParticipantWithSkills)
def participant_get(participant_id: int, session: Session = Depends(get_session)) -> Participant:
    """Get participant by ID with skills"""
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@app.post("/participant")
def participant_create(participant: ParticipantBase,
                       session: Session = Depends(get_session)
                    ) -> TypedDict('Response', {"status": int, "data": Participant}):
    """Create a new participant"""
    db_participant = Participant.model_validate(participant)
    session.add(db_participant)
    session.commit()
    session.refresh(db_participant)
    return {"status": 200, "data": db_participant}


@app.patch("/participant/{participant_id}")
def participant_update(participant_id: int, 
                       participant: ParticipantBase, 
                       session: Session = Depends(get_session)
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


@app.delete("/participant/{participant_id}")
def participant_delete(participant_id: int, session: Session = Depends(get_session)):
    """Delete participant"""
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    session.delete(participant)
    session.commit()
    return {"status": 200, "message": "Participant deleted successfully"}


@app.get("/teams", response_model=list[Team])
def teams_list(session: Session = Depends(get_session)) -> list[Team]:
    """Get all teams"""
    return session.exec(select(Team)).all()


@app.get("/team/{team_id}", response_model=TeamWithParticipants)
def team_get(team_id: int, session: Session = Depends(get_session)) -> TeamWithParticipants:
    """Get team by ID with participants"""
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    # Trigger loading of participants
    _ = team.participants
    return team


@app.post("/team")
def team_create(
    team: TeamBase,
    session: Session = Depends(get_session)
) -> TypedDict('Response', {"status": int, "data": Team}):
    """Create a new team"""
    db_team = Team.model_validate(team)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return {"status": 200, "data": db_team}


@app.patch("/team/{team_id}")
def team_update(
    team_id: int,
    team: TeamBase,
    session: Session = Depends(get_session)
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


@app.delete("/team/{team_id}")
def team_delete(team_id: int, session: Session = Depends(get_session)):
    """Delete team"""
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    session.delete(team)
    session.commit()
    return {"status": 200, "message": "Team deleted successfully"}


@app.get("/skills", response_model=list[Skill])
def skills_list(session: Session = Depends(get_session)) -> list[Skill]:
    """Get all skills"""
    return session.exec(select(Skill)).all()


@app.get("/skill/{skill_id}", response_model=SkillWithParticipants)
def skill_get(skill_id: int, session: Session = Depends(get_session)) -> SkillWithParticipants:
    """Get skill by ID with participants"""
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    # Trigger loading of participants
    _ = skill.participants
    return skill


@app.post("/skill")
def skill_create(
    skill: SkillBase,
    session: Session = Depends(get_session)
) -> TypedDict('Response', {"status": int, "data": Skill}):
    """Create a new skill"""
    db_skill = Skill.model_validate(skill)
    session.add(db_skill)
    session.commit()
    session.refresh(db_skill)
    return {"status": 200, "data": db_skill}


@app.patch("/skill/{skill_id}")
def skill_update(
    skill_id: int,
    skill: SkillBase,
    session: Session = Depends(get_session)
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


@app.delete("/skill/{skill_id}")
def skill_delete(skill_id: int, session: Session = Depends(get_session)):
    """Delete skill"""
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    session.delete(skill)
    session.commit()
    return {"status": 200, "message": "Skill deleted successfully"}


@app.get("/tasks", response_model=list[Task])
def tasks_list(session: Session = Depends(get_session)) -> list[Task]:
    """Get all tasks"""
    return session.exec(select(Task)).all()


@app.get("/task/{task_id}", response_model=TaskWithSubmissions)
def task_get(task_id: int, session: Session = Depends(get_session)) -> TaskWithSubmissions:
    """Get task by ID with submissions"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Trigger loading of submissions
    _ = task.submissions
    return task


@app.post("/task")
def task_create(
    task: TaskBase,
    session: Session = Depends(get_session)
) -> TypedDict('Response', {"status": int, "data": Task}):
    """Create a new task"""
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return {"status": 200, "data": db_task}


@app.patch("/task/{task_id}")
def task_update(
    task_id: int,
    task: TaskBase,
    session: Session = Depends(get_session)
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


@app.delete("/task/{task_id}")
def task_delete(task_id: int, session: Session = Depends(get_session)):
    """Delete task"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()
    return {"status": 200, "message": "Task deleted successfully"}


@app.get("/submissions", response_model=list[Submission])
def submissions_list(session: Session = Depends(get_session)) -> list[Submission]:
    """Get all submissions"""
    return session.exec(select(Submission)).all()


@app.get("/submission/{submission_id}", response_model=SubmissionWithRelations)
def submission_get(submission_id: int, session: Session = Depends(get_session)) -> SubmissionWithRelations:
    """Get submission by ID with relations"""
    submission = session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    # Trigger loading of relations
    _ = submission.task
    _ = submission.team
    _ = submission.participant
    return submission


@app.post("/submission")
def submission_create(
    submission: SubmissionBase,
    session: Session = Depends(get_session)
) -> TypedDict('Response', {"status": int, "data": Submission}):
    """Create a new submission"""
    db_submission = Submission.model_validate(submission)
    session.add(db_submission)
    session.commit()
    session.refresh(db_submission)
    return {"status": 200, "data": db_submission}


@app.patch("/submission/{submission_id}")
def submission_update(
    submission_id: int,
    submission: SubmissionBase,
    session: Session = Depends(get_session)
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


@app.delete("/submission/{submission_id}")
def submission_delete(submission_id: int, session: Session = Depends(get_session)):
    """Delete submission"""
    submission = session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    session.delete(submission)
    session.commit()
    return {"status": 200, "message": "Submission deleted successfully"}


@app.post("/participant/{participant_id}/skill/{skill_id}")
def add_skill_to_participant(
    participant_id: int,
    skill_id: int,
    proficiency_level: int = 1,
    session: Session = Depends(get_session)
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


@app.post("/team/{team_id}/participant/{participant_id}")
def add_participant_to_team(
    team_id: int,
    participant_id: int,
    role: str = "member",
    session: Session = Depends(get_session)
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


@app.get("/participant/{participant_id}/teams", response_model=list[Team])
def get_participant_teams(participant_id: int, session: Session = Depends(get_session)):
    """Get all teams for a participant"""
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant.teams


@app.get("/team/{team_id}/participants", response_model=list[Participant])
def get_team_participants(team_id: int, session: Session = Depends(get_session)):
    """Get all participants in a team"""
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team.participants


@app.get("/task/{task_id}/submissions", response_model=list[Submission])
def get_task_submissions(task_id: int, session: Session = Depends(get_session)):
    """Get all submissions for a task"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.submissions
