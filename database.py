from sqlalchemy import create_engine, event, func
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


def get_columns(table_name):
    with engine.connect() as connection:
        rows = connection.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
        return {row[1] for row in rows}


def add_column_if_missing(table_name, column_name, definition):
    columns = get_columns(table_name)
    if column_name not in columns:
        with engine.begin() as connection:
            connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def migrate_database():
    add_column_if_missing("files", "stored_name", "VARCHAR(255)")
    add_column_if_missing("files", "original_path", "VARCHAR(500)")
    add_column_if_missing("files", "encrypted_path", "VARCHAR(500)")
    add_column_if_missing("files", "decrypted_name", "VARCHAR(255)")
    add_column_if_missing("files", "decrypted_path", "VARCHAR(500)")
    add_column_if_missing("files", "encrypted_hash", "VARCHAR(256)")
    add_column_if_missing("files", "decrypted_hash", "VARCHAR(256)")
    add_column_if_missing("files", "size_bytes", "INTEGER")
    add_column_if_missing("files", "created_at", "DATETIME")
    add_column_if_missing("files", "updated_at", "DATETIME")

    add_column_if_missing("performances", "key_id", "INTEGER REFERENCES keys(id) ON DELETE SET NULL")
    add_column_if_missing("performances", "file_size_bytes", "INTEGER")
    add_column_if_missing("performances", "result_hash", "VARCHAR(256)")
    add_column_if_missing("performances", "created_at", "DATETIME")


def get_framework_case_insensitive(db, models, name):
    return (
        db.query(models.Framework)
        .filter(func.lower(models.Framework.name) == name.lower())
        .first()
    )


def initialize_database():
    import models

    Base.metadata.create_all(bind=engine)
    migrate_database()
    seed_reference_data()


def seed_reference_data():
    import models

    db = get_session()
    try:
        default_algorithms = [
            ("AES-256-CBC", "Simetric"),
            ("RSA", "Asimetric"),
        ]

        for name, algo_type in default_algorithms:
            existing = (
                db.query(models.Algorithm)
                .filter(func.lower(models.Algorithm.name) == name.lower())
                .first()
            )
            if existing is None:
                db.add(models.Algorithm(name=name, type=algo_type))

        openssl_framework = get_framework_case_insensitive(db, models, "OpenSSL")
        if openssl_framework is None:
            db.add(models.Framework(name="OpenSSL"))

        cryptography_framework = get_framework_case_insensitive(db, models, "Cryptography API")
        pycryptodome_framework = get_framework_case_insensitive(db, models, "PyCryptodome")

        if pycryptodome_framework is not None and cryptography_framework is None:
            pycryptodome_framework.name = "Cryptography API"
            cryptography_framework = pycryptodome_framework

        elif pycryptodome_framework is not None and cryptography_framework is not None:
            db.query(models.Performance).filter(
                models.Performance.framework_id == pycryptodome_framework.id
            ).update(
                {"framework_id": cryptography_framework.id},
                synchronize_session=False
            )
            db.delete(pycryptodome_framework)

        cryptography_framework = get_framework_case_insensitive(db, models, "Cryptography API")
        if cryptography_framework is None:
            db.add(models.Framework(name="Cryptography API"))
        else:
            cryptography_framework.name = "Cryptography API"

        db.commit()
    finally:
        db.close()