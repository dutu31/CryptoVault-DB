import math

from sqlalchemy import func
from sqlalchemy.orm import Session

import models


DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 100


def normalize_page(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = DEFAULT_PAGE

    if value < 1:
        value = DEFAULT_PAGE

    return value


def normalize_per_page(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = DEFAULT_PER_PAGE

    if value < 1:
        value = DEFAULT_PER_PAGE

    if value > MAX_PER_PAGE:
        value = MAX_PER_PAGE

    return value


def paginate_query(query, page=1, per_page=25):
    page = normalize_page(page)
    per_page = normalize_per_page(per_page)

    total = query.count()
    pages = math.ceil(total / per_page) if total > 0 else 1

    if page > pages:
        page = pages

    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_prev": page > 1,
        "has_next": page < pages,
        "prev_page": page - 1 if page > 1 else 1,
        "next_page": page + 1 if page < pages else pages,
    }


def create_algorithm(db: Session, name: str, algo_type: str):
    new_algo = models.Algorithm(name=name, type=algo_type)
    db.add(new_algo)
    db.commit()
    db.refresh(new_algo)
    return new_algo


def get_all_algorithms(db: Session):
    return db.query(models.Algorithm).order_by(models.Algorithm.id).all()


def get_algorithms_paginated(db: Session, page=1, per_page=25):
    query = db.query(models.Algorithm).order_by(models.Algorithm.id)
    return paginate_query(query, page, per_page)


def count_algorithms(db: Session):
    return db.query(models.Algorithm).count()


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


def create_key(db: Session, algorithm_id: int, key_value: str):
    new_key = models.Key(algorithm_id=algorithm_id, key_value=key_value)
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    return new_key


def get_all_keys(db: Session):
    return db.query(models.Key).order_by(models.Key.id).all()


def get_keys_paginated(db: Session, page=1, per_page=25):
    query = db.query(models.Key).order_by(models.Key.id.desc())
    return paginate_query(query, page, per_page)


def count_keys(db: Session):
    return db.query(models.Key).count()


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


def create_framework(db: Session, name: str):
    new_framework = models.Framework(name=name)
    db.add(new_framework)
    db.commit()
    db.refresh(new_framework)
    return new_framework


def get_all_frameworks(db: Session):
    return db.query(models.Framework).order_by(models.Framework.id).all()


def get_frameworks_paginated(db: Session, page=1, per_page=25):
    query = db.query(models.Framework).order_by(models.Framework.id)
    return paginate_query(query, page, per_page)


def count_frameworks(db: Session):
    return db.query(models.Framework).count()


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


def create_file(
    db: Session,
    original_name: str,
    stored_name: str = None,
    original_path: str = None,
    status: str = "Ne-criptat",
    hash_value: str = None,
    size_bytes: int = None
):
    new_file = models.File(
        original_name=original_name,
        stored_name=stored_name,
        original_path=original_path,
        status=status,
        hash_value=hash_value,
        size_bytes=size_bytes,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file


def get_all_files(db: Session):
    return db.query(models.File).order_by(models.File.id.desc()).all()


def get_files_paginated(db: Session, page=1, per_page=25):
    query = db.query(models.File).order_by(models.File.id.desc())
    return paginate_query(query, page, per_page)


def count_files(db: Session):
    return db.query(models.File).count()


def get_file_by_id(db: Session, file_id: int):
    return db.query(models.File).filter(models.File.id == file_id).first()


def get_file_by_original_name(db: Session, original_name: str):
    return (
        db.query(models.File)
        .filter(func.lower(models.File.original_name) == original_name.strip().lower())
        .first()
    )


def update_file_after_encrypt(
    db: Session,
    file_id: int,
    encrypted_name: str,
    encrypted_path: str,
    encrypted_hash: str
):
    db_file = get_file_by_id(db, file_id)
    if db_file:
        db_file.encrypted_name = encrypted_name
        db_file.encrypted_path = encrypted_path
        db_file.encrypted_hash = encrypted_hash
        db_file.status = "Criptat"
        db.commit()
        db.refresh(db_file)
    return db_file


def update_file_after_decrypt(
    db: Session,
    file_id: int,
    decrypted_name: str,
    decrypted_path: str,
    decrypted_hash: str
):
    db_file = get_file_by_id(db, file_id)
    if db_file:
        db_file.decrypted_name = decrypted_name
        db_file.decrypted_path = decrypted_path
        db_file.decrypted_hash = decrypted_hash
        db_file.status = "Decriptat"
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


def create_performance(
    db: Session,
    file_id: int,
    algorithm_id: int,
    framework_id: int,
    operation: str,
    time_taken_ms: float = None,
    memory_used_kb: float = None,
    key_id: int = None,
    file_size_bytes: int = None,
    result_hash: str = None,
    runs_count: int = 1,
    avg_time_ms: float = None,
    min_time_ms: float = None,
    max_time_ms: float = None,
    avg_memory_kb: float = None,
    min_memory_kb: float = None,
    max_memory_kb: float = None
):
    new_performance = models.Performance(
        file_id=file_id,
        algorithm_id=algorithm_id,
        framework_id=framework_id,
        key_id=key_id,
        operation=operation,
        time_taken_ms=time_taken_ms,
        memory_used_kb=memory_used_kb,
        runs_count=runs_count,
        avg_time_ms=avg_time_ms if avg_time_ms is not None else time_taken_ms,
        min_time_ms=min_time_ms if min_time_ms is not None else time_taken_ms,
        max_time_ms=max_time_ms if max_time_ms is not None else time_taken_ms,
        avg_memory_kb=avg_memory_kb if avg_memory_kb is not None else memory_used_kb,
        min_memory_kb=min_memory_kb if min_memory_kb is not None else memory_used_kb,
        max_memory_kb=max_memory_kb if max_memory_kb is not None else memory_used_kb,
        file_size_bytes=file_size_bytes,
        result_hash=result_hash,
    )
    db.add(new_performance)
    db.commit()
    db.refresh(new_performance)
    return new_performance


def get_all_performances(db: Session):
    return db.query(models.Performance).order_by(models.Performance.id.desc()).all()


def get_performances_paginated(db: Session, page=1, per_page=25):
    query = db.query(models.Performance).order_by(models.Performance.id.desc())
    return paginate_query(query, page, per_page)


def count_performances(db: Session):
    return db.query(models.Performance).count()


def get_performance_by_id(db: Session, performance_id: int):
    return db.query(models.Performance).filter(models.Performance.id == performance_id).first()


def delete_performance(db: Session, performance_id: int):
    db_performance = get_performance_by_id(db, performance_id)
    if db_performance:
        db.delete(db_performance)
        db.commit()
        return True
    return False


def get_performance_summary(db: Session):
    rows = (
        db.query(
            models.Algorithm.name.label("algorithm_name"),
            models.Framework.name.label("framework_name"),
            models.Performance.operation.label("operation"),
            func.count(models.Performance.id).label("records_count"),
            func.sum(models.Performance.runs_count).label("runs_total"),
            func.avg(models.Performance.avg_time_ms).label("avg_time_ms"),
            func.min(models.Performance.min_time_ms).label("min_time_ms"),
            func.max(models.Performance.max_time_ms).label("max_time_ms"),
            func.avg(models.Performance.avg_memory_kb).label("avg_memory_kb"),
        )
        .join(models.Algorithm, models.Performance.algorithm_id == models.Algorithm.id)
        .join(models.Framework, models.Performance.framework_id == models.Framework.id)
        .group_by(
            models.Algorithm.name,
            models.Framework.name,
            models.Performance.operation
        )
        .order_by(
            models.Algorithm.name,
            models.Framework.name,
            models.Performance.operation
        )
        .all()
    )

    summary = []

    for row in rows:
        summary.append({
            "algorithm_name": row.algorithm_name,
            "framework_name": row.framework_name,
            "operation": row.operation,
            "records_count": row.records_count or 0,
            "runs_total": row.runs_total or 0,
            "avg_time_ms": round(row.avg_time_ms or 0, 3),
            "min_time_ms": round(row.min_time_ms or 0, 3),
            "max_time_ms": round(row.max_time_ms or 0, 3),
            "avg_memory_kb": round(row.avg_memory_kb or 0, 3),
        })

    return summary
