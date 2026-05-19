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
    """Create predefined skills with current technologies (2025-2026)"""
    skills_data = [
        {"name": "Python", "description": "Разработка на FastAPI, Django, AI/ML приложения"},
        {"name": "TypeScript", "description": "Типизированный JavaScript для современных фреймворков"},
        {"name": "React/Next.js", "description": "Современный фронтенд с SSR и метафреймворками"},
        {"name": "PostgreSQL", "description": "Реляционные базы данных с расширениями (PostGIS, TimescaleDB)"},
        {"name": "MongoDB", "description": "NoSQL базы данных для документоориентированных приложений"},
        {"name": "Docker & Kubernetes", "description": "Контейнеризация и оркестрация микросервисов"},
        {"name": "Cloud Native (AWS/Azure/GCP)", "description": "Мультиклауд архитектура и сервисы"},
        {"name": "AI/ML Engineering", "description": "Разработка и deployment ML моделей (PyTorch, TensorFlow)"},
        {"name": "Generative AI", "description": "Работа с LLM, RAG системы, fine-tuning моделей"},
        {"name": "DevSecOps", "description": "Безопасность в CI/CD, SAST/DAST, security as code"},
        {"name": "Blockchain & Web3", "description": "Смарт-контракты (Solidity), DeFi, NFT платформы"},
        {"name": "Edge Computing", "description": "Обработка данных на edge устройствах, IoT системы"},
        {"name": "AR/VR Development", "description": "Разработка для метавселенной, Unity/Unreal Engine"},
        {"name": "Quantum Computing Basics", "description": "Квантовые алгоритмы и программирование (Qiskit)"},
        {"name": "Sustainable Tech", "description": "Зеленые вычисления, энергоэффективные алгоритмы"},
        {"name": "Low-Code/No-Code", "description": "Платформы для citizen development (Bubble, Retool)"},
        {"name": "Cybersecurity", "description": "Пентестинг, threat modeling, security monitoring"},
        {"name": "Data Engineering", "description": "Обработка больших данных, ETL/ELT, data pipelines"},
        {"name": "UI/UX Design", "description": "Дизайн-системы, прототипирование (Figma, Adobe XD)"},
        {"name": "Product Management", "description": "Agile, Scrum, OKR, roadmap planning"},
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
    """Create participants with different types using string values"""
    participants_data = [
        {
            "name": "Иван Петров",
            "email": "ivan.petrov@example.com",
            "phone": "+79161234567",
            "type": "programmer"
        },
        {
            "name": "Анна Сидорова",
            "email": "anna.sidorova@example.com",
            "phone": "+79167654321",
            "type": "designer"
        },
        {
            "name": "Сергей Иванов",
            "email": "sergey.ivanov@example.com",
            "phone": "+79169876543",
            "type": "manager"
        },
        {
            "name": "Мария Кузнецова",
            "email": "maria.kuznetsova@example.com",
            "phone": "+79161112233",
            "type": "analyst"
        },
        {
            "name": "Алексей Смирнов",
            "email": "alexey.smirnov@example.com",
            "phone": "+79162223344",
            "type": "programmer"
        },
        {
            "name": "Елена Попова",
            "email": "elena.popova@example.com",
            "phone": "+79163334455",
            "type": "designer"
        },
        {
            "name": "Дмитрий Васильев",
            "email": "dmitry.vasiliev@example.com",
            "phone": "+79164445566",
            "type": "programmer"
        },
        {
            "name": "Ольга Новикова",
            "email": "olga.novikova@example.com",
            "phone": "+79165556677",
            "type": "manager"
        },
        {
            "name": "Павел Морозов",
            "email": "pavel.morozov@example.com",
            "phone": "+79166667788",
            "type": "analyst"
        },
        {
            "name": "Наталья Волкова",
            "email": "natalya.volkova@example.com",
            "phone": "+79167778899",
            "type": "designer"
        },
        {
            "name": "Артем Козлов",
            "email": "artem.kozlov@example.com",
            "phone": "+79168889900",
            "type": "programmer"
        },
        {
            "name": "Виктория Орлова",
            "email": "victoria.orlova@example.com",
            "phone": "+79169990011",
            "type": "designer"
        },
        {
            "name": "Максим Лебедев",
            "email": "maxim.lebedev@example.com",
            "phone": "+79161001122",
            "type": "manager"
        },
        {
            "name": "Алина Соколова",
            "email": "alina.sokolova@example.com",
            "phone": "+79162112233",
            "type": "analyst"
        },
        {
            "name": "Кирилл Воробьев",
            "email": "kirill.vorobiev@example.com",
            "phone": "+79163223344",
            "type": "programmer"
        },
    ]
    
    participants = []
    # Add participants one by one to avoid bulk insert issues with ENUM type
    for data in participants_data:
        # Use raw SQL to insert to avoid SQLModel ENUM type issues
        # SQLModel is trying to use PostgreSQL ENUM type that doesn't exist
        # So we'll use session.execute with raw SQL
        from sqlmodel import text
        stmt = text("""
            INSERT INTO participant (name, email, phone, type)
            VALUES (:name, :email, :phone, :type)
            RETURNING id
        """)
        result = session.execute(stmt, {
            "name": data["name"],
            "email": data["email"],
            "phone": data["phone"],
            "type": data["type"]
        })
        participant_id = result.scalar()
        
        # Create a Participant object for later use
        participant = Participant(
            id=participant_id,
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            type=data["type"]
        )
        participants.append(participant)
    
    session.commit()
    print(f"Created {len(participants)} participants")
    return participants


def create_teams(session):
    """Create teams with modern structures"""
    teams_data = [
        {"name": "Quantum Coders", "description": "Команда квантовых вычислений и AI"},
        {"name": "Cyber Guardians", "description": "Кибербезопасность и DevSecOps"},
        {"name": "Metaverse Architects", "description": "AR/VR разработка и метавселенная"},
        {"name": "Green Tech Innovators", "description": "Устойчивые технологии и green computing"},
        {"name": "Web3 Pioneers", "description": "Блокчейн, DeFi и смарт-контракты"},
        {"name": "Edge Computing Squad", "description": "IoT, edge devices и распределенные системы"},
        {"name": "Data Science Collective", "description": "AI/ML, большие данные и аналитика"},
        {"name": "Cloud Native Crew", "description": "Мультиклауд архитектура и микросервисы"},
        {"name": "Low-Code Mavericks", "description": "Гражданская разработка и автоматизация"},
        {"name": "Digital Health Warriors", "description": "HealthTech и медицинские технологии"},
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
    """Create hackathon tasks with current trends (2025-2026)"""
    tasks_data = [
        {
            "title": "Квантово-устойчивая криптография",
            "description": "Разработать систему шифрования, устойчивую к атакам квантовых компьютеров, с реализацией постквантовых алгоритмов.",
            "requirements": "Реализация алгоритмов Kyber, Dilithium или Falcon, веб-интерфейс для демонстрации, бенчмарки производительности.",
            "evaluation_criteria": "Безопасность, производительность, удобство использования, соответствие стандартам NIST.",
            "is_active": True
        },
        {
            "title": "AI-агент для автоматизации научных исследований",
            "description": "Создать интеллектуального агента, способного анализировать научные статьи, генерировать гипотезы и планировать эксперименты.",
            "requirements": "Использование LLM (GPT-4, Claude, Gemini), RAG система, интеграция с научными базами данных (PubMed, arXiv).",
            "evaluation_criteria": "Качество генерации гипотез, точность анализа, инновационность подхода.",
            "is_active": True
        },
        {
            "title": "Децентрализованная система идентификации (DID)",
            "description": "Разработать систему самоуправляемой цифровой идентификации на блокчейне с поддержкой верифицируемых учетных данных.",
            "requirements": "Блокчейн (Ethereum, Polkadot), смарт-контракты, мобильное приложение, стандарты W3C DID.",
            "evaluation_criteria": "Безопасность, приватность, совместимость со стандартами, пользовательский опыт.",
            "is_active": True
        },
        {
            "title": "Цифровой двойник для умного города",
            "description": "Создать цифровую копию городской инфраструктуры для моделирования и оптимизации транспортных потоков, энергопотребления и ЧС.",
            "requirements": "3D визуализация (Three.js/Unity), IoT интеграция, ML для предсказания, GIS данные.",
            "evaluation_criteria": "Точность моделирования, интерактивность, практическая полезность для городских служб.",
            "is_active": True
        },
        {
            "title": "Нейроинтерфейс для доступных технологий",
            "description": "Разработать систему управления устройствами с помощью мозговых волн (EEG) для людей с ограниченными возможностями.",
            "requirements": "Обработка сигналов EEG (Python, TensorFlow), ML классификация, интерфейс для управления умным домом.",
            "evaluation_criteria": "Точность распознавания, задержка, доступность, инновационность.",
            "is_active": True
        },
        {
            "title": "Зеленая цепочка поставок на блокчейне",
            "description": "Создать платформу для отслеживания углеродного следа продукции по всей цепочке поставок с прозрачной верификацией.",
            "requirements": "Блокчейн для неизменяемого лога, IoT датчики, мобильное приложение для сканирования QR кодов.",
            "evaluation_criteria": "Точность данных, прозрачность, влияние на устойчивое развитие.",
            "is_active": True
        },
        {
            "title": "Метавселенная для дистанционного образования",
            "description": "Разработать иммерсивную образовательную платформу в метавселенной с интерактивными лабораториями и социальным взаимодействием.",
            "requirements": "VR/AR совместимость (WebXR), мультиплеер, система достижений, инструменты для преподавателей.",
            "evaluation_criteria": "Иммерсивность, образовательная ценность, масштабируемость, пользовательский опыт.",
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
    # Define skill assignments: participant_index -> [skill_indices]
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
    # Define team assignments: team_index -> [participant_indices]
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
    
    # Delete in correct order to respect foreign key constraints
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
    
    # Initialize database (create tables if they don't exist)
    init_db()
    
    with Session(engine) as session:
        # Clear existing data (optional - uncomment if needed)
        # clear_database(session)
        
        # Create entities
        skills = create_skills(session)
        participants = create_participants(session)
        teams = create_teams(session)
        tasks = create_tasks(session)
        
        # Create relationships
        assign_skills_to_participants(session, participants, skills)
        assign_participants_to_teams(session, participants, teams)
        
        # Create submissions (needs IDs from created entities)
        submissions = create_submissions(session, tasks, teams, participants)
        
        print("\n=== Database Population Summary ===")
        print(f"Skills: {len(skills)}")
        print(f"Participants: {len(participants)}")
        print(f"Teams: {len(teams)}")
        print(f"Tasks: {len(tasks)}")
        print(f"Submissions: {len(submissions)}")
        
        # Count relationships
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
