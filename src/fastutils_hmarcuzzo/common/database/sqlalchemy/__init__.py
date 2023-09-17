from sqlalchemy.orm import Session

from fastutils_hmarcuzzo.common.database.sqlalchemy.session import DatabaseSessionFactory


class DatabaseSessionManager:
    def __init__(self, database_url: str, app_tz: str = "UTC"):
        self.session_factory = DatabaseSessionFactory(database_url, app_tz)

    def get_db(self) -> Session:
        db: Session = self.session_factory.get_session()
        try:
            yield db
        finally:
            db.close()
