import logging
import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy.ext.declarative as dec
from sqlalchemy.orm import Session

SqlAlchemyBase = dec.declarative_base()

__factory = None


def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Database name required")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'

    logging.info(f"Connecting to {conn_str}...")
    print(f"Connecting to {conn_str}...")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    # You have to import your Sqlalchemy class before creating tables
    # Example: from . import your_class

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()