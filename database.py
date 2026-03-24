from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///crypto_vault.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine
)

Base = declarative_base()


def get_session():
    return SessionLocal()


def initialize_database():
    import models

    Base.metadata.create_all(bind=engine)
    seed_reference_data()


def seed_reference_data():
    import models

    db = get_session()
    try:
        default_algorithms = [
            ("AES-256-CBC", "Simetric"),
            ("RSA", "Asimetric"),
        ]

        default_frameworks = [
            "OpenSSL",
            "PyCryptodome",
        ]

        for name, algo_type in default_algorithms:
            existing = db.query(models.Algorithm).filter(models.Algorithm.name == name).first()
            if existing is None:
                db.add(models.Algorithm(name=name, type=algo_type))

        for name in default_frameworks:
            existing = db.query(models.Framework).filter(models.Framework.name == name).first()
            if existing is None:
                db.add(models.Framework(name=name))

        db.commit()
    finally:
        db.close()