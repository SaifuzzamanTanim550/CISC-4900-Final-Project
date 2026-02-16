from src.db.database import engine
from src.models.base import Base
import src.models.models  # This ensures models are registered


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Tables created successfully")
