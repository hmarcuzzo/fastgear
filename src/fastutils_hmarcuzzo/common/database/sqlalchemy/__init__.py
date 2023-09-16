from sqlalchemy.orm import Session

from fastutils_hmarcuzzo.common.database.sqlalchemy.session import get_session


def get_db(database_url: str, app_tz: str = "UTC") -> Session:
    db: Session = get_session(database_url, app_tz)
    try:
        yield db
    finally:
        db.close()
