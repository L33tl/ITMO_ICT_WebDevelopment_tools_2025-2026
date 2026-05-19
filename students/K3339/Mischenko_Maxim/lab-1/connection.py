import os
import subprocess
import sys
from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DB_ADMIN')
engine = create_engine(db_url, echo=True)

def init_db():
    """Initialize database using Alembic migrations."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Alembic migration failed: {result.stderr}")
            SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Error running Alembic: {e}")
        SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
