import pytest 
from alembic import command 
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import Settings 


@pytest.fixture(scope="session")
def engine():
    url = Settings().database_url(test=True)

    alembic_config = Config("alembic.ini")
    alembic_config.attributes["database_url"] = url
    command.upgrade(alembic_config, "head")

    engine = create_engine(url)
    yield engine
    engine.dispose()



@pytest.fixture
def session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()