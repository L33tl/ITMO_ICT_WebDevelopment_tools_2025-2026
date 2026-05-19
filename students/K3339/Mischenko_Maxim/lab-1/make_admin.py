import sys
from sqlmodel import Session, select
from connection import engine
from models import User

def list_users(session):
    """List all users with their admin status."""
    users = session.exec(select(User)).all()
    print("\n=== Current Users ===")
    for user in users:
        admin_status = "ADMIN" if user.is_superuser else "USER"
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Status: {admin_status}")
    return users

def make_user_admin(session, user_identifier):
    """
    Make a user an admin by username, email, or ID.
    
    Args:
        session: Database session
        user_identifier: Username, email, or ID of the user to make admin
    
    Returns:
        The updated user or None if not found
    """
    user = None
    
    if user_identifier.isdigit():
        user = session.get(User, int(user_identifier))
        if user:
            print(f"Found user by ID {user_identifier}: {user.username}")
    
    if not user:
        statement = select(User).where(User.username == user_identifier)
        user = session.exec(statement).first()
        if user:
            print(f"Found user by username: {user.username}")
    
    # If not found by username, try by email
    if not user:
        statement = select(User).where(User.email == user_identifier)
        user = session.exec(statement).first()
        if user:
            print(f"Found user by email: {user.email}")
    
    if not user:
        print(f"User '{user_identifier}' not found!")
        return None
    
    # Check if already admin
    if user.is_superuser:
        print(f"User '{user.username}' is already an admin!")
        return user
    
    # Update to admin
    user.is_superuser = True
    user.updated_at = "2026-04-10T21:47:22.722Z"  # Current timestamp
    session.add(user)
    session.commit()
    session.refresh(user)
    
    print(f"✓ Successfully made user '{user.username}' an admin!")
    return user

def create_admin_user(session, username, email, password, full_name=None):
    """
    Create a new admin user directly.
    
    Args:
        session: Database session
        username: Username for the new admin
        email: Email for the new admin
        password: Password for the new admin
        full_name: Optional full name
    
    Returns:
        The created admin user
    """
    from auth import get_password_hash
    from datetime import datetime
    
    # Check if user already exists
    existing = session.exec(select(User).where(
        (User.username == username) | (User.email == email)
    )).first()
    
    if existing:
        print(f"User with username '{username}' or email '{email}' already exists!")
        # Make existing user admin
        existing.is_superuser = True
        session.add(existing)
        session.commit()
        session.refresh(existing)
        print(f"✓ Made existing user '{existing.username}' an admin!")
        return existing
    
    # Create new admin user
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        full_name=full_name or username,
        hashed_password=hashed_password,
        is_superuser=True,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    print(f"✓ Created new admin user: {db_user.username} (ID: {db_user.id})")
    return db_user

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python make_admin.py list                    - List all users")
        print("  python make_admin.py make <username/email/id> - Make user admin")
        print("  python make_admin.py create <username> <email> <password> [full_name] - Create new admin")
        print("\nExamples:")
        print("  python make_admin.py list")
        print("  python make_admin.py make testuser")
        print("  python make_admin.py make admin@example.com")
        print("  python make_admin.py make 1")
        print("  python make_admin.py create admin admin@example.com AdminPassword123 \"Admin User\"")
        return
    
    command = sys.argv[1].lower()
    
    with Session(engine) as session:
        if command == "list":
            list_users(session)
        
        elif command == "make":
            if len(sys.argv) < 3:
                print("Error: Please specify a username, email, or ID")
                print("Usage: python make_admin.py make <username/email/id>")
                return
            
            user_identifier = sys.argv[2]
            make_user_admin(session, user_identifier)
        
        elif command == "create":
            if len(sys.argv) < 5:
                print("Error: Please specify username, email, and password")
                print("Usage: python make_admin.py create <username> <email> <password> [full_name]")
                return
            
            username = sys.argv[2]
            email = sys.argv[3]
            password = sys.argv[4]
            full_name = sys.argv[5] if len(sys.argv) > 5 else None
            
            create_admin_user(session, username, email, password, full_name)
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: list, make, create")

if __name__ == "__main__":
    main()