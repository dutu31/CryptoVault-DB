from sqlalchemy.orm import Session
from sqlalchemy import func
import models


# -------------------- ALGORITHMS --------------------

def create_algorithm(db: Session, name: str, algo_type: str):
    new_algo = models.Algorithm(name=name, type=algo_type)
    db.add(new_algo)
    db.commit()
    db.refresh(new_algo)
    return new_algo


def get_all_algorithms(db: Session):
    return db.query(models.Algorithm).order_by(models.Algorithm.id).all()


def get_algorithm_by_id(db: Session, algo_id: int):
    return db.query(models.Algorithm).filter(models.Algorithm.id == algo_id).first()

def get_algorithm_by_name(db: Session, name: str):
    return (
        db.query(models.Algorithm)
        .filter(func.lower(models.Algorithm.name) == name.strip().lower())
        .first()
    )


def update_algorithm(db: Session, algo_id: int, name: str, algo_type: str):
    db_algo = get_algorithm_by_id(db, algo_id)
    if db_algo:
        db_algo.name = name
        db_algo.type = algo_type
        db.commit()
        db.refresh(db_algo)
    return db_algo


def delete_algorithm(db: Session, algo_id: int):
    db_algo = get_algorithm_by_id(db, algo_id)
    if db_algo:
        db.delete(db_algo)
        db.commit()
        return True
    return False


# -------------------- KEYS --------------------

def create_key(db: Session, algorithm_id: int, key_value: str):
    new_key = models.Key(algorithm_id=algorithm_id, key_value=key_value)
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    return new_key


def get_all_keys(db: Session):
    return db.query(models.Key).order_by(models.Key.id).all()


def get_key_by_id(db: Session, key_id: int):
    return db.query(models.Key).filter(models.Key.id == key_id).first()

def get_key_by_algorithm_and_value(db: Session, algorithm_id: int, key_value: str):
    return (
        db.query(models.Key)
        .filter(
            models.Key.algorithm_id == algorithm_id,
            models.Key.key_value == key_value.strip()
        )
        .first()
    )

def delete_key(db: Session, key_id: int):
    db_key = get_key_by_id(db, key_id)
    if db_key:
        db.delete(db_key)
        db.commit()
        return True
    return False


# -------------------- FRAMEWORKS --------------------

def create_framework(db: Session, name: str):
    new_framework = models.Framework(name=name)
    db.add(new_framework)
    db.commit()
    db.refresh(new_framework)
    return new_framework


def get_all_frameworks(db: Session):
    return db.query(models.Framework).order_by(models.Framework.id).all()


def get_framework_by_id(db: Session, framework_id: int):
    return db.query(models.Framework).filter(models.Framework.id == framework_id).first()

def get_framework_by_name(db: Session, name: str):
    return (
        db.query(models.Framework)
        .filter(func.lower(models.Framework.name) == name.strip().lower())
        .first()
    )


def update_framework(db: Session, framework_id: int, name: str):
    db_framework = get_framework_by_id(db, framework_id)
    if db_framework:
        db_framework.name = name
        db.commit()
        db.refresh(db_framework)
    return db_framework


def delete_framework(db: Session, framework_id: int):
    db_framework = get_framework_by_id(db, framework_id)
    if db_framework:
        db.delete(db_framework)
        db.commit()
        return True
    return False


# -------------------- FILES --------------------

def create_file(db: Session, original_name: str, encrypted_name: str = None, status: str = "Ne-criptat", hash_value: str = None):
    new_file = models.File(
        original_name=original_name,
        encrypted_name=encrypted_name,
        status=status,
        hash_value=hash_value,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file


def get_all_files(db: Session):
    return db.query(models.File).order_by(models.File.id).all()


def get_file_by_id(db: Session, file_id: int):
    return db.query(models.File).filter(models.File.id == file_id).first()

def get_file_by_original_name(db: Session, original_name: str):
    return (
        db.query(models.File)
        .filter(func.lower(models.File.original_name) == original_name.strip().lower())
        .first()
    )


def update_file(db: Session, file_id: int, original_name: str, encrypted_name: str = None, status: str = "Ne-criptat", hash_value: str = None):
    db_file = get_file_by_id(db, file_id)
    if db_file:
        db_file.original_name = original_name
        db_file.encrypted_name = encrypted_name
        db_file.status = status
        db_file.hash_value = hash_value
        db.commit()
        db.refresh(db_file)
    return db_file


def delete_file(db: Session, file_id: int):
    db_file = get_file_by_id(db, file_id)
    if db_file:
        db.delete(db_file)
        db.commit()
        return True
    return False


# -------------------- PERFORMANCES --------------------

def create_performance(db: Session, file_id: int, algorithm_id: int, framework_id: int, operation: str, time_taken_ms: float = None, memory_used_kb: float = None):
    new_performance = models.Performance(
        file_id=file_id,
        algorithm_id=algorithm_id,
        framework_id=framework_id,
        operation=operation,
        time_taken_ms=time_taken_ms,
        memory_used_kb=memory_used_kb,
    )
    db.add(new_performance)
    db.commit()
    db.refresh(new_performance)
    return new_performance


def get_all_performances(db: Session):
    return db.query(models.Performance).order_by(models.Performance.id).all()


def get_performance_by_id(db: Session, performance_id: int):
    return db.query(models.Performance).filter(models.Performance.id == performance_id).first()

def delete_performance(db: Session, performance_id: int):
    db_performance = get_performance_by_id(db, performance_id)
    if db_performance:
        db.delete(db_performance)
        db.commit()
        return True
    return False