from sqlalchemy.orm import Session

from fastutils_hmarcuzzo.common.database.sqlalchemy.session import get_session


def get_db(database_url: str) -> Session:
    db: Session = get_session(database_url)
    try:
        yield db
    finally:
        db.close()
