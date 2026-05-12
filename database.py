from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///crypto_vault.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def column_exists(connection, table_name, column_name):
    rows = connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()

    for row in rows:
        if row[1] == column_name:
            return True

    return False


def add_column_if_missing(connection, table_name, column_name, column_definition):
    if not column_exists(connection, table_name, column_name):
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))


def migrate_database():
    with engine.begin() as connection:
        add_column_if_missing(connection, "files", "stored_name", "VARCHAR(255)")
        add_column_if_missing(connection, "files", "original_path", "VARCHAR(500)")
        add_column_if_missing(connection, "files", "encrypted_path", "VARCHAR(500)")
        add_column_if_missing(connection, "files", "decrypted_path", "VARCHAR(500)")
        add_column_if_missing(connection, "files", "encrypted_hash", "VARCHAR(256)")
        add_column_if_missing(connection, "files", "decrypted_hash", "VARCHAR(256)")
        add_column_if_missing(connection, "files", "size_bytes", "INTEGER")
        add_column_if_missing(connection, "files", "created_at", "DATETIME")
        add_column_if_missing(connection, "files", "updated_at", "DATETIME")

        add_column_if_missing(connection, "performances", "key_id", "INTEGER")
        add_column_if_missing(connection, "performances", "runs_count", "INTEGER DEFAULT 1")

        add_column_if_missing(connection, "performances", "avg_time_ms", "FLOAT")
        add_column_if_missing(connection, "performances", "min_time_ms", "FLOAT")
        add_column_if_missing(connection, "performances", "max_time_ms", "FLOAT")

        add_column_if_missing(connection, "performances", "total_time_ms", "FLOAT")
        add_column_if_missing(connection, "performances", "avg_total_time_ms", "FLOAT")
        add_column_if_missing(connection, "performances", "min_total_time_ms", "FLOAT")
        add_column_if_missing(connection, "performances", "max_total_time_ms", "FLOAT")

        add_column_if_missing(connection, "performances", "avg_memory_kb", "FLOAT")
        add_column_if_missing(connection, "performances", "min_memory_kb", "FLOAT")
        add_column_if_missing(connection, "performances", "max_memory_kb", "FLOAT")

        add_column_if_missing(connection, "performances", "input_size_bytes", "INTEGER")
        add_column_if_missing(connection, "performances", "file_size_bytes", "INTEGER")
        add_column_if_missing(connection, "performances", "result_hash", "VARCHAR(256)")
        add_column_if_missing(connection, "performances", "created_at", "DATETIME")

        connection.execute(text("""
            UPDATE performances
            SET runs_count = 1
            WHERE runs_count IS NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET avg_time_ms = time_taken_ms
            WHERE avg_time_ms IS NULL AND time_taken_ms IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET min_time_ms = time_taken_ms
            WHERE min_time_ms IS NULL AND time_taken_ms IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET max_time_ms = time_taken_ms
            WHERE max_time_ms IS NULL AND time_taken_ms IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET total_time_ms = time_taken_ms
            WHERE total_time_ms IS NULL AND time_taken_ms IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET avg_total_time_ms = total_time_ms
            WHERE avg_total_time_ms IS NULL AND total_time_ms IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET min_total_time_ms = total_time_ms
            WHERE min_total_time_ms IS NULL AND total_time_ms IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET max_total_time_ms = total_time_ms
            WHERE max_total_time_ms IS NULL AND total_time_ms IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET avg_memory_kb = memory_used_kb
            WHERE avg_memory_kb IS NULL AND memory_used_kb IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET min_memory_kb = memory_used_kb
            WHERE min_memory_kb IS NULL AND memory_used_kb IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET max_memory_kb = memory_used_kb
            WHERE max_memory_kb IS NULL AND memory_used_kb IS NOT NULL
        """))

        connection.execute(text("""
            UPDATE performances
            SET input_size_bytes = file_size_bytes
            WHERE input_size_bytes IS NULL AND file_size_bytes IS NOT NULL
        """))


def seed_reference_data():
    import models

    db = SessionLocal()

    try:
        existing_aes = db.query(models.Algorithm).filter(models.Algorithm.name == "AES-256-CBC").first()

        if existing_aes is None:
            db.add(models.Algorithm(name="AES-256-CBC", type="Simetric"))

        existing_rsa = db.query(models.Algorithm).filter(models.Algorithm.name == "RSA").first()

        if existing_rsa is None:
            db.add(models.Algorithm(name="RSA", type="Asimetric"))

        frameworks = ["OpenSSL", "Cryptography API", "PyCryptodome"]

        for framework_name in frameworks:
            existing_framework = db.query(models.Framework).filter(models.Framework.name == framework_name).first()

            if existing_framework is None:
                db.add(models.Framework(name=framework_name))

        db.commit()
    finally:
        db.close()


def initialize_database():
    import models

    Base.metadata.create_all(bind=engine)
    migrate_database()
    seed_reference_data()