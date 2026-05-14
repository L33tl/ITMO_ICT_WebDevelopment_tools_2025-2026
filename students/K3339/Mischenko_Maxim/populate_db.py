#!/usr/bin/env python3
"""
Script to populate the database with fake test data for the Hackathon Management System.
This script creates Skills, Participants, Teams, Tasks, and Submissions with realistic relationships.
"""

import sys
from sqlmodel import Session, select
from connection import engine, init_db
from models import (
    Skill, Participant, Team, Task, Submission,
    ParticipantSkillLink, TeamParticipantLink,
    ParticipantType
)


def create_skills(session):
    """Create predefined skills"""
    skills_data = [
        {"name": "Python", "description": "Разработка на FastAPI и Django"},
        {"name": "PostgreSQL", "description": "Работа с базами данных"},
        {"name": "Figma", "description": "Создание интерфейсов"},
        {"name": "Adobe Photoshop", "description": "Графический дизайн"},
        {"name": "Управление проектами", "description": "Agile, Scrum"},
        {"name": "JavaScript", "description": "Frontend разработка на React/Vue"},
        {"name": "Docker", "description": "Контейнеризация приложений"},
        {"name": "AWS", "description": "Облачная инфраструктура"},
        {"name": "Machine Learning", "description": "AI/ML модели"},
        {"name": "UI/UX Design", "description": "Дизайн пользовательского опыта"},
        {"name": "DevOps", "description": "CI/CD, автоматизация"},
        {"name": "Mobile Development", "description": "iOS/Android разработка"},
    ]
    
    skills = []
    for data in skills_data:
        skill = Skill(**data)
        session.add(skill)
        skills.append(skill)
    
    session.commit()
    print(f"Created {len(skills)} skills")
    return skills


def create_participants(session):
    """Create participants with different types"""
    participants_data = [
        {
            "name": "Иван Петров",
            "email": "ivan@example.com",
            "phone": "+79161234567",
            "type": ParticipantType.programmer
        },
        {
            "name": "Анна Сидорова",
            "email": "anna@example.com",
            "phone": "+79167654321",
            "type": ParticipantType.designer
        },
        {
            "name": "Сергей Иванов",
            "email": "sergey@example.com",
            "phone": "+79169876543",
            "type": ParticipantType.manager
        },
        {
            "name": "Мария Кузнецова",
            "email": "maria@example.com",
            "phone": "+79161112233",
            "type": ParticipantType.analyst
        },
        {
            "name": "Алексей Смирнов",
            "email": "alexey@example.com",
            "phone": "+79162223344",
            "type": ParticipantType.programmer
        },
        {
            "name": "Елена Попова",
            "email": "elena@example.com",
            "phone": "+79163334455",
            "type": ParticipantType.designer
        },
        {
            "name": "Дмитрий Васильев",
            "email": "dmitry@example.com",
            "phone": "+79164445566",
            "type": ParticipantType.programmer
        },
        {
            "name": "Ольга Новикова",
            "email": "olga@example.com",
            "phone": "+79165556677",
            "type": ParticipantType.manager
        },
        {
            "name": "Павел Морозов",
            "email": "pavel@example.com",
            "phone": "+79166667788",
            "type": ParticipantType.analyst
        },
        {
            "name": "Наталья Волкова",
            "email": "natalya@example.com",
            "phone": "+79167778899",
            "type": ParticipantType.designer
        },
    ]
    
    participants = []
    for data in participants_data:
        participant = Participant(**data)
        session.add(participant)
        participants.append(participant)
    
    session.commit()
    print(f"Created {len(participants)} participants")
    return participants


def create_teams(session):
    """Create teams"""
    teams_data = [
        {"name": "Кододелы", "description": "Команда backend-разработчиков"},
        {"name": "Креативщики", "description": "UI/UX дизайнеры"},
        {"name": "Аналитики PRO", "description": "Команда аналитиков данных"},
        {"name": "Менеджеры Успеха", "description": "Управление проектами"},
        {"name": "FullStack Masters", "description": "Full-stack разработчики"},
        {"name": "AI Explorers", "description": "Исследователи искусственного интеллекта"},
    ]
    
    teams = []
    for data in teams_data:
        team = Team(**data)
        session.add(team)
        teams.append(team)
    
    session.commit()
    print(f"Created {len(teams)} teams")
    return teams


def create_tasks(session):
    """Create hackathon tasks"""
    tasks_data = [
        {
            "title": "Разработка платформы для онлайн-хакатонов",
            "description": "Создать веб-платформу для проведения хакатонов с функционалом регистрации команд,提交 проектов и оценки жюри.",
            "requirements": "Backend на FastAPI, фронтенд на React, база данных PostgreSQL, Docker-контейнеризация.",
            "evaluation_criteria": "Функциональность, удобство использования, качество кода, инновационность.",
            "is_active": True
        },
        {
            "title": "AI-ассистент для планирования задач",
            "description": "Разработать интеллектуального помощника, который помогает командам планировать задачи и распределять ресурсы.",
            "requirements": "Использование ML моделей для предсказания времени выполнения задач, веб-интерфейс, интеграция с календарями.",
            "evaluation_criteria": "Точность предсказаний, полезность функционала, дизайн интерфейса.",
            "is_active": True
        },
        {
            "title": "Экосистема для устойчивого развития",
            "description": "Создать платформу, которая помогает компаниям отслеживать и уменьшать углеродный след.",
            "requirements": "Дашборды с аналитикой, мобильное приложение, интеграция с IoT датчиками.",
            "evaluation_criteria": "Практическая применимость, масштабируемость, инновационность.",
            "is_active": True
        },
        {
            "title": "Геймификация обучения программированию",
            "description": "Разработать игровую платформу для обучения программированию с элементами соревнования.",
            "requirements": "Система уровней и достижений, редактор кода, система проверки решений.",
            "evaluation_criteria": "Увлекательность, образовательная ценность, техническая реализация.",
            "is_active": False
        },
    ]
    
    tasks = []
    for data in tasks_data:
        task = Task(**data)
        session.add(task)
        tasks.append(task)
    
    session.commit()
    print(f"Created {len(tasks)} tasks")
    return tasks


def assign_skills_to_participants(session, participants, skills):
    """Assign skills to participants with proficiency levels"""
    assignments = [
        [0, 1, 5],      # Иван: Python, PostgreSQL, JavaScript
        [2, 3],         # Анна: Figma, Adobe Photoshop
        [4],            # Сергей: Управление проектами
        [9, 10],        # Мария: UI/UX Design, DevOps
        [0, 5, 6, 7],   # Алексей: Python, JavaScript, Docker, AWS
        [2, 9],         # Елена: Figma, UI/UX Design
        [0, 1, 6, 10],  # Дмитрий: Python, PostgreSQL, Docker, DevOps
        [4, 7],         # Ольга: Управление проектами, AWS
        [8, 11],        # Павел: Machine Learning, Mobile Development
        [2, 3, 9],      # Наталья: Figma, Adobe Photoshop, UI/UX Design
    ]
    
    links_created = 0
    for i, participant in enumerate(participants):
        if i < len(assignments):
            for skill_idx in assignments[i]:
                if skill_idx < len(skills):
                    link = ParticipantSkillLink(
                        participant_id=participant.id,
                        skill_id=skills[skill_idx].id,
                        proficiency_level=(i % 5) + 1  # 1-5
                    )
                    session.add(link)
                    links_created += 1
    
    session.commit()
    print(f"Created {links_created} participant-skill links")
    return links_created


def assign_participants_to_teams(session, participants, teams):
    """Assign participants to teams with roles"""
    assignments = [
        [0, 2, 4, 6],   # Кододелы: Иван, Сергей, Алексей, Дмитрий
        [1, 5, 9],      # Креативщики: Анна, Елена, Наталья
        [3, 8],         # Аналитики PRO: Мария, Павел
        [2, 7],         # Менеджеры Успеха: Сергей, Ольга
        [0, 4, 6, 1],   # FullStack Masters: Иван, Алексей, Дмитрий, Анна
        [3, 8, 4],      # AI Explorers: Мария, Павел, Алексей
    ]
    
    roles = ["lead", "member", "member", "member", "member"]
    
    links_created = 0
    for team_idx, team in enumerate(teams):
        if team_idx < len(assignments):
            for i, participant_idx in enumerate(assignments[team_idx]):
                if participant_idx < len(participants):
                    role = roles[i % len(roles)]
                    link = TeamParticipantLink(
                        team_id=team.id,
                        participant_id=participants[participant_idx].id,
                        role=role
                    )
                    session.add(link)
                    links_created += 1
    
    session.commit()
    print(f"Created {links_created} team-participant links")
    return links_created


def create_submissions(session, tasks, teams, participants):
    """Create submissions for tasks"""
    submissions_data = [
        {
            "title": "HackPlatform v1.0",
            "description": "Полнофункциональная платформа для проведения онлайн-хакатонов с системой оценки проектов.",
            "repository_url": "https://github.com/team1/hackplatform",
            "demo_url": "https://demo.hackplatform.example.com",
            "task_id": tasks[0].id if len(tasks) > 0 else None,
            "team_id": teams[0].id if len(teams) > 0 else None,
            "participant_id": participants[0].id if len(participants) > 0 else None,
        },
        {
            "title": "AI Task Planner",
            "description": "Интеллектуальный помощник для планирования задач с ML-предсказаниями.",
            "repository_url": "https://github.com/team5/ai-task-planner",
            "demo_url": "https://demo.aitaskplanner.example.com",
            "task_id": tasks[1].id if len(tasks) > 1 else None,
            "team_id": teams[4].id if len(teams) > 4 else None,
            "participant_id": participants[4].id if len(participants) > 4 else None,
        },
        {
            "title": "EcoTrack Pro",
            "description": "Платформа для отслеживания углеродного следа с аналитическими дашбордами.",
            "repository_url": "https://github.com/team2/ecotrack",
            "demo_url": "https://demo.ecotrack.example.com",
            "task_id": tasks[2].id if len(tasks) > 2 else None,
            "team_id": teams[2].id if len(teams) > 2 else None,
            "participant_id": participants[3].id if len(participants) > 3 else None,
        },
        {
            "title": "CodeGame Learning Platform",
            "description": "Игровая платформа для обучения программированию с системой достижений.",
            "repository_url": "https://github.com/team1/codegame",
            "demo_url": "https://demo.codegame.example.com",
            "task_id": tasks[3].id if len(tasks) > 3 else None,
            "team_id": teams[0].id if len(teams) > 0 else None,
            "participant_id": participants[6].id if len(participants) > 6 else None,
        },
    ]
    
    submissions = []
    for data in submissions_data:
        submission = Submission(**data)
        session.add(submission)
        submissions.append(submission)
    
    session.commit()
    print(f"Created {len(submissions)} submissions")
    return submissions


def clear_database(session):
    """Clear all data from database (optional)"""
    print("Clearing existing data...")
    
    session.exec("DELETE FROM submissions")
    session.exec("DELETE FROM teamparticipantlink")
    session.exec("DELETE FROM participantskilllink")
    session.exec("DELETE FROM tasks")
    session.exec("DELETE FROM teams")
    session.exec("DELETE FROM participants")
    session.exec("DELETE FROM skills")
    
    session.commit()
    print("Database cleared")


def main():
    """Main function to populate the database"""
    print("Starting database population...")
    
    init_db()
    
    with Session(engine) as session:
        
        skills = create_skills(session)
        participants = create_participants(session)
        teams = create_teams(session)
        tasks = create_tasks(session)
        
        assign_skills_to_participants(session, participants, skills)
        assign_participants_to_teams(session, participants, teams)
        
        submissions = create_submissions(session, tasks, teams, participants)
        
        print("\n=== Database Population Summary ===")
        print(f"Skills: {len(skills)}")
        print(f"Participants: {len(participants)}")
        print(f"Teams: {len(teams)}")
        print(f"Tasks: {len(tasks)}")
        print(f"Submissions: {len(submissions)}")
        
        skill_links = session.exec(select(ParticipantSkillLink)).all()
        team_links = session.exec(select(TeamParticipantLink)).all()
        print(f"Participant-Skill links: {len(skill_links)}")
        print(f"Team-Participant links: {len(team_links)}")
        
        print("\nDatabase populated successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error populating database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
