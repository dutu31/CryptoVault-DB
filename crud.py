import math

from sqlalchemy import func

import models


class Pagination:
    def __init__(self, page, per_page, total):
        self.total = total
        self.per_page = per_page
        self.pages = max(1, math.ceil(total / per_page)) if per_page else 1
        self.page = max(1, min(page, self.pages))
        self.has_prev = self.page > 1
        self.has_next = self.page < self.pages
        self.prev_page = self.page - 1 if self.has_prev else 1
        self.next_page = self.page + 1 if self.has_next else self.pages


def paginate_query(query, page=1, per_page=10):
    total = query.count()
    pagination = Pagination(page, per_page, total)

    items = (
        query
        .limit(per_page)
        .offset((pagination.page - 1) * per_page)
        .all()
    )

    return items, pagination


def normalize_operation(operation):
    if operation is None:
        return "-"

    value = str(operation).strip().lower()

    if value == "encrypt":
        return "Criptare"

    if value == "decrypt":
        return "Decriptare"

    return operation


def safe_round(value, digits=3):
    if value is None:
        return None

    return round(float(value), digits)


def get_stats(db):
    return {
        "algorithms": db.query(models.Algorithm).count(),
        "crypto_keys": db.query(models.Key).count(),
        "frameworks": db.query(models.Framework).count(),
        "files": db.query(models.File).count(),
        "performances": db.query(models.Performance).count(),
    }


def get_all_algorithms(db):
    return db.query(models.Algorithm).order_by(models.Algorithm.name.asc()).all()


def get_algorithms_paginated(db, page=1, per_page=10):
    query = db.query(models.Algorithm).order_by(models.Algorithm.name.asc())
    return paginate_query(query, page, per_page)


def get_algorithm(db, algorithm_id):
    return db.query(models.Algorithm).filter(models.Algorithm.id == algorithm_id).first()


def save_algorithm(db, name, algorithm_type, algorithm_id=None):
    name = name.strip()
    algorithm_type = algorithm_type.strip()

    duplicate_query = db.query(models.Algorithm).filter(func.lower(models.Algorithm.name) == name.lower())

    if algorithm_id:
        duplicate_query = duplicate_query.filter(models.Algorithm.id != algorithm_id)

    duplicate = duplicate_query.first()

    if duplicate:
        raise ValueError("Există deja un algoritm cu acest nume.")

    if algorithm_id:
        algorithm = get_algorithm(db, algorithm_id)

        if algorithm is None:
            raise ValueError("Algoritmul nu există.")

        algorithm.name = name
        algorithm.type = algorithm_type
    else:
        algorithm = models.Algorithm(name=name, type=algorithm_type)
        db.add(algorithm)

    db.commit()
    db.refresh(algorithm)

    return algorithm


def delete_algorithm(db, algorithm_id):
    algorithm = get_algorithm(db, algorithm_id)

    if algorithm is None:
        raise ValueError("Algoritmul nu există.")

    db.delete(algorithm)
    db.commit()


def get_all_frameworks(db):
    return db.query(models.Framework).order_by(models.Framework.name.asc()).all()


def get_frameworks_paginated(db, page=1, per_page=10):
    query = db.query(models.Framework).order_by(models.Framework.name.asc())
    return paginate_query(query, page, per_page)


def get_framework(db, framework_id):
    return db.query(models.Framework).filter(models.Framework.id == framework_id).first()


def save_framework(db, name, framework_id=None):
    name = name.strip()

    duplicate_query = db.query(models.Framework).filter(func.lower(models.Framework.name) == name.lower())

    if framework_id:
        duplicate_query = duplicate_query.filter(models.Framework.id != framework_id)

    duplicate = duplicate_query.first()

    if duplicate:
        raise ValueError("Există deja un framework cu acest nume.")

    if framework_id:
        framework = get_framework(db, framework_id)

        if framework is None:
            raise ValueError("Framework-ul nu există.")

        framework.name = name
    else:
        framework = models.Framework(name=name)
        db.add(framework)

    db.commit()
    db.refresh(framework)

    return framework


def delete_framework(db, framework_id):
    framework = get_framework(db, framework_id)

    if framework is None:
        raise ValueError("Framework-ul nu există.")

    db.delete(framework)
    db.commit()


def get_all_files(db):
    return db.query(models.File).order_by(models.File.id.desc()).all()


def get_files_paginated(db, page=1, per_page=10):
    query = db.query(models.File).order_by(models.File.id.desc())
    return paginate_query(query, page, per_page)


def get_file(db, file_id):
    return db.query(models.File).filter(models.File.id == file_id).first()


def create_file(db, original_name, stored_name, original_path, hash_value, size_bytes):
    file_obj = models.File(
        original_name=original_name,
        stored_name=stored_name,
        original_path=original_path,
        status="Ne-criptat",
        hash_value=hash_value,
        size_bytes=size_bytes,
    )

    db.add(file_obj)
    db.commit()
    db.refresh(file_obj)

    return file_obj


def update_file_after_operation(db, file_id, operation, output_name, output_path, output_hash, output_size):
    file_obj = get_file(db, file_id)

    if file_obj is None:
        raise ValueError("Fișierul nu există.")

    if operation == "encrypt":
        file_obj.encrypted_name = output_name
        file_obj.encrypted_path = output_path
        file_obj.encrypted_hash = output_hash
        file_obj.status = "Criptat"
    elif operation == "decrypt":
        file_obj.decrypted_name = output_name
        file_obj.decrypted_path = output_path
        file_obj.decrypted_hash = output_hash
        file_obj.status = "Decriptat"

    db.commit()
    db.refresh(file_obj)

    return file_obj


def delete_file(db, file_id):
    file_obj = get_file(db, file_id)

    if file_obj is None:
        raise ValueError("Fișierul nu există.")

    db.delete(file_obj)
    db.commit()


def get_all_keys(db):
    return db.query(models.Key).order_by(models.Key.id.desc()).all()


def get_keys_paginated(db, page=1, per_page=10):
    query = db.query(models.Key).order_by(models.Key.id.desc())
    return paginate_query(query, page, per_page)


def get_key(db, key_id):
    return db.query(models.Key).filter(models.Key.id == key_id).first()


def create_key(db, algorithm_id, key_value):
    algorithm = get_algorithm(db, algorithm_id)

    if algorithm is None:
        raise ValueError("Algoritmul selectat nu există.")

    key = models.Key(
        algorithm_id=algorithm_id,
        key_value=key_value,
    )

    db.add(key)
    db.commit()
    db.refresh(key)

    return key


def delete_key(db, key_id):
    key = get_key(db, key_id)

    if key is None:
        raise ValueError("Cheia nu există.")

    db.delete(key)
    db.commit()


def get_performances_paginated(db, page=1, per_page=5):
    query = db.query(models.Performance).order_by(models.Performance.id.desc())
    return paginate_query(query, page, per_page)


def get_performance(db, performance_id):
    return db.query(models.Performance).filter(models.Performance.id == performance_id).first()


def create_performance(
    db,
    file_id,
    algorithm_id,
    framework_id,
    key_id,
    operation,
    time_taken_ms,
    memory_used_kb,
    total_time_ms,
    runs_count,
    avg_time_ms,
    min_time_ms,
    max_time_ms,
    avg_total_time_ms,
    min_total_time_ms,
    max_total_time_ms,
    avg_memory_kb,
    min_memory_kb,
    max_memory_kb,
    input_size_bytes,
    file_size_bytes,
    result_hash,
):
    performance = models.Performance(
        file_id=file_id,
        algorithm_id=algorithm_id,
        framework_id=framework_id,
        key_id=key_id,
        operation=operation,
        time_taken_ms=time_taken_ms,
        memory_used_kb=memory_used_kb,
        total_time_ms=total_time_ms,
        runs_count=runs_count,
        avg_time_ms=avg_time_ms,
        min_time_ms=min_time_ms,
        max_time_ms=max_time_ms,
        avg_total_time_ms=avg_total_time_ms,
        min_total_time_ms=min_total_time_ms,
        max_total_time_ms=max_total_time_ms,
        avg_memory_kb=avg_memory_kb,
        min_memory_kb=min_memory_kb,
        max_memory_kb=max_memory_kb,
        input_size_bytes=input_size_bytes,
        file_size_bytes=file_size_bytes,
        result_hash=result_hash,
    )

    db.add(performance)
    db.commit()
    db.refresh(performance)

    return performance


def delete_performance(db, performance_id):
    performance = get_performance(db, performance_id)

    if performance is None:
        raise ValueError("Înregistrarea de performanță nu există.")

    db.delete(performance)
    db.commit()


def get_performance_summary(db):
    performances = db.query(models.Performance).all()
    groups = {}

    for performance in performances:
        algorithm_name = performance.algorithm.name if performance.algorithm else "-"
        framework_name = performance.framework.name if performance.framework else "-"
        operation = normalize_operation(performance.operation)

        key = (algorithm_name, framework_name, operation)

        if key not in groups:
            groups[key] = {
                "algorithm_name": algorithm_name,
                "framework_name": framework_name,
                "operation": operation,
                "records_count": 0,
                "runs_total": 0,
                "time_sum": 0.0,
                "total_time_sum": 0.0,
                "memory_sum": 0.0,
                "min_time_ms": None,
                "max_time_ms": None,
                "min_total_time_ms": None,
                "max_total_time_ms": None,
            }

        runs_count = performance.runs_count or 1

        avg_time = performance.avg_time_ms
        if avg_time is None:
            avg_time = performance.time_taken_ms

        min_time = performance.min_time_ms
        if min_time is None:
            min_time = performance.time_taken_ms

        max_time = performance.max_time_ms
        if max_time is None:
            max_time = performance.time_taken_ms

        avg_total_time = performance.avg_total_time_ms
        if avg_total_time is None:
            avg_total_time = performance.total_time_ms

        if avg_total_time is None:
            avg_total_time = avg_time

        min_total_time = performance.min_total_time_ms
        if min_total_time is None:
            min_total_time = performance.total_time_ms

        if min_total_time is None:
            min_total_time = min_time

        max_total_time = performance.max_total_time_ms
        if max_total_time is None:
            max_total_time = performance.total_time_ms

        if max_total_time is None:
            max_total_time = max_time

        avg_memory = performance.avg_memory_kb
        if avg_memory is None:
            avg_memory = performance.memory_used_kb

        group = groups[key]
        group["records_count"] += 1
        group["runs_total"] += runs_count

        if avg_time is not None:
            group["time_sum"] += float(avg_time) * runs_count

        if avg_total_time is not None:
            group["total_time_sum"] += float(avg_total_time) * runs_count

        if avg_memory is not None:
            group["memory_sum"] += float(avg_memory) * runs_count

        if min_time is not None:
            group["min_time_ms"] = float(min_time) if group["min_time_ms"] is None else min(group["min_time_ms"], float(min_time))

        if max_time is not None:
            group["max_time_ms"] = float(max_time) if group["max_time_ms"] is None else max(group["max_time_ms"], float(max_time))

        if min_total_time is not None:
            group["min_total_time_ms"] = float(min_total_time) if group["min_total_time_ms"] is None else min(group["min_total_time_ms"], float(min_total_time))

        if max_total_time is not None:
            group["max_total_time_ms"] = float(max_total_time) if group["max_total_time_ms"] is None else max(group["max_total_time_ms"], float(max_total_time))

    rows = []

    for group in groups.values():
        runs_total = group["runs_total"] if group["runs_total"] else 1

        rows.append({
            "algorithm_name": group["algorithm_name"],
            "framework_name": group["framework_name"],
            "operation": group["operation"],
            "records_count": group["records_count"],
            "runs_total": group["runs_total"],
            "avg_time_ms": safe_round(group["time_sum"] / runs_total),
            "min_time_ms": safe_round(group["min_time_ms"]),
            "max_time_ms": safe_round(group["max_time_ms"]),
            "avg_total_time_ms": safe_round(group["total_time_sum"] / runs_total),
            "min_total_time_ms": safe_round(group["min_total_time_ms"]),
            "max_total_time_ms": safe_round(group["max_total_time_ms"]),
            "avg_memory_kb": safe_round(group["memory_sum"] / runs_total),
        })

    rows.sort(key=lambda item: (item["algorithm_name"], item["framework_name"], item["operation"]))

    return rows


def get_performance_analysis(db):
    performances = db.query(models.Performance).all()
    groups = {}

    for performance in performances:
        algorithm_name = performance.algorithm.name if performance.algorithm else "-"
        framework_name = performance.framework.name if performance.framework else "-"
        operation = normalize_operation(performance.operation)

        input_size = performance.input_size_bytes

        if input_size is None:
            input_size = performance.file_size_bytes

        if input_size is None and performance.file is not None:
            input_size = performance.file.size_bytes

        if input_size is None or input_size <= 0:
            continue

        avg_time = performance.avg_time_ms
        if avg_time is None:
            avg_time = performance.time_taken_ms

        avg_total_time = performance.avg_total_time_ms
        if avg_total_time is None:
            avg_total_time = performance.total_time_ms

        if avg_total_time is None:
            avg_total_time = avg_time

        avg_memory = performance.avg_memory_kb
        if avg_memory is None:
            avg_memory = performance.memory_used_kb

        if avg_time is None or avg_total_time is None:
            continue

        crypto_ms_per_byte = float(avg_time) / float(input_size)
        total_ms_per_byte = float(avg_total_time) / float(input_size)

        runs_count = performance.runs_count or 1
        key = (algorithm_name, framework_name, operation)

        if key not in groups:
            groups[key] = {
                "algorithm_name": algorithm_name,
                "framework_name": framework_name,
                "operation": operation,
                "records_count": 0,
                "runs_total": 0,
                "input_bytes_total": 0,
                "crypto_ms_sum": 0.0,
                "total_ms_sum": 0.0,
                "memory_sum": 0.0,
                "min_crypto_ms_per_byte": None,
                "max_crypto_ms_per_byte": None,
                "min_total_ms_per_byte": None,
                "max_total_ms_per_byte": None,
            }

        group = groups[key]

        group["records_count"] += 1
        group["runs_total"] += runs_count
        group["input_bytes_total"] += int(input_size) * runs_count
        group["crypto_ms_sum"] += crypto_ms_per_byte * runs_count
        group["total_ms_sum"] += total_ms_per_byte * runs_count

        if avg_memory is not None:
            group["memory_sum"] += float(avg_memory) * runs_count

        group["min_crypto_ms_per_byte"] = crypto_ms_per_byte if group["min_crypto_ms_per_byte"] is None else min(group["min_crypto_ms_per_byte"], crypto_ms_per_byte)
        group["max_crypto_ms_per_byte"] = crypto_ms_per_byte if group["max_crypto_ms_per_byte"] is None else max(group["max_crypto_ms_per_byte"], crypto_ms_per_byte)

        group["min_total_ms_per_byte"] = total_ms_per_byte if group["min_total_ms_per_byte"] is None else min(group["min_total_ms_per_byte"], total_ms_per_byte)
        group["max_total_ms_per_byte"] = total_ms_per_byte if group["max_total_ms_per_byte"] is None else max(group["max_total_ms_per_byte"], total_ms_per_byte)

    rows = []

    for group in groups.values():
        runs_total = group["runs_total"] if group["runs_total"] else 1

        rows.append({
            "algorithm_name": group["algorithm_name"],
            "framework_name": group["framework_name"],
            "operation": group["operation"],
            "records_count": group["records_count"],
            "runs_total": group["runs_total"],
            "input_bytes_total": group["input_bytes_total"],
            "avg_crypto_ms_per_byte": safe_round(group["crypto_ms_sum"] / runs_total, 6),
            "min_crypto_ms_per_byte": safe_round(group["min_crypto_ms_per_byte"], 6),
            "max_crypto_ms_per_byte": safe_round(group["max_crypto_ms_per_byte"], 6),
            "avg_total_ms_per_byte": safe_round(group["total_ms_sum"] / runs_total, 6),
            "min_total_ms_per_byte": safe_round(group["min_total_ms_per_byte"], 6),
            "max_total_ms_per_byte": safe_round(group["max_total_ms_per_byte"], 6),
            "avg_memory_kb": safe_round(group["memory_sum"] / runs_total),
        })

    rows.sort(key=lambda item: (item["algorithm_name"], item["framework_name"], item["operation"]))

    return rows