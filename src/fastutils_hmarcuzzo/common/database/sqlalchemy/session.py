from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def get_session(database_url: str, app_tz: str = "UTC") -> Session:
    engine = create_engine(database_url, connect_args={"options": f"-c timezone={app_tz}"})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return SessionLocal()
