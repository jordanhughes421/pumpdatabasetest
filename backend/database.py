import os
from sqlmodel import SQLModel, create_engine, Session

# Updated database name to force schema refresh for new features
sqlite_file_name = os.environ.get("SQLITE_DB_PATH", "pump_curves.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
