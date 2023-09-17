from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class DatabaseSessionFactory:
    def __init__(self, database_url: str, app_tz: str = "UTC"):
        self.engine = create_engine(database_url, connect_args={"options": f"-c timezone={app_tz}"})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()
