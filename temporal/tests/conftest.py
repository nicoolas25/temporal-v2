from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm.session import Session as SqlaSession
from sqlalchemy.orm.session import sessionmaker

from .models import Base  # This will also load all models

# Setup a test database, in memory
engine = create_engine("sqlite://")
Session = sessionmaker(bind=engine)


@pytest.fixture()
def session() -> Iterator[SqlaSession]:
    # Drop the whole DB and create it again before each test!
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with Session() as session:
        yield session
