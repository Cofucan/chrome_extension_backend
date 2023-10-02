from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from settings import DB_USER, DB_PASSWORD, DB_PORT, DB_HOST, DB_NAME, DB_TYPE


if DB_TYPE == "mysql":
    DB_URL = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DB_URL)

else:
    DB_URL = f"sqlite:///./{DB_NAME}.db"
    engine = create_engine(
        DB_URL, connect_args={"check_same_thread": False}
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    create_tables()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
