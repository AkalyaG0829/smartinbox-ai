import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Mock database url using sqlite in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create engine for testing (SQLite requires special connect args for threading)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import base and models to create tables
from src.database.session import Base, get_db
from src.main import app
from src.infrastructure.models import User, Channel, ChannelMember, Contact, Message, RoutingDecision

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # SQLite doesn't natively support pgvector, but since we are mocking/stubbing vector operations 
    # and not running raw pgvector operations in unit tests, it works if the model contains the Vector type 
    # as long as we don't try to query vectors. To handle sqlite, we can mock/override the Vector type mapping.
    
    # Create all tables in SQLite
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after testing
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
