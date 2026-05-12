from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime
import uuid
import json
import time

from database import SessionLocal, initialize_database
import crud
import crypto_services

app = Flask(__name__)
app.secret_key = "crypto-vault-secret-key"

BASE_DATA_DIR = Path("data")
ORIGINAL_DIR = BASE_DATA_DIR / "original"
ENCRYPTED_DIR = BASE_DATA_DIR / "encrypted"
DECRYPTED_DIR = BASE_DATA_DIR / "decrypted"

ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
ENCRYPTED_DIR.mkdir(parents=True, exist_ok=True)
DECRYPTED_DIR.mkdir(parents=True, exist_ok=True)

initialize_database()


def get_session():
    return SessionLocal()


def make_unique_name(original_name, prefix="file"):
    safe_name = secure_filename(original_name)

    if not safe_name:
        safe_name = prefix

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]

    return f"{timestamp}_{unique_id}_{safe_name}"


def operation_label(operation):
    if operation == "encrypt":
        return "Criptare"

    if operation == "decrypt":
        return "Decriptare"

    return operation


def get_output_path(file_obj, operation):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    original_path = Path(file_obj.original_name)
    stem = original_path.stem
    suffix = original_path.suffix

    if operation == "encrypt":
        output_name = f"{stem}_{timestamp}_{unique_id}_encrypted.bin"
        output_path = ENCRYPTED_DIR / output_name
        return output_name, str(output_path)

    output_suffix = suffix if suffix else ".txt"
    output_name = f"{stem}_{timestamp}_{unique_id}_decrypted{output_suffix}"
    output_path = DECRYPTED_DIR / output_name

    return output_name, str(output_path)


def get_input_path_for_operation(file_obj, operation):
    if operation == "encrypt":
        return file_obj.original_path

    if operation == "decrypt":
        return file_obj.encrypted_path

    return None


def parse_rsa_key(value):
    try:
        data = json.loads(value)

        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {}


def adjust_total_times(benchmark_result, measured_total_operation_ms):
    runs_count = benchmark_result["runs_count"]

    inner_avg_total = benchmark_result.get("avg_total_time_ms")

    if inner_avg_total is None:
        inner_avg_total = benchmark_result.get("avg_time_ms", 0)

    inner_min_total = benchmark_result.get("min_total_time_ms")

    if inner_min_total is None:
        inner_min_total = benchmark_result.get("min_time_ms", inner_avg_total)

    inner_max_total = benchmark_result.get("max_total_time_ms")

    if inner_max_total is None:
        inner_max_total = benchmark_result.get("max_time_ms", inner_avg_total)

    inner_last_total = benchmark_result.get("total_time_ms")

    if inner_last_total is None:
        inner_last_total = benchmark_result.get("time_taken_ms", inner_avg_total)

    total_inner_sum = float(inner_avg_total) * runs_count
    overhead_total = measured_total_operation_ms - total_inner_sum

    if overhead_total < 0:
        overhead_total = 0

    overhead_per_run = overhead_total / runs_count

    avg_total_time_ms = measured_total_operation_ms / runs_count
    min_total_time_ms = float(inner_min_total) + overhead_per_run
    max_total_time_ms = float(inner_max_total) + overhead_per_run
    total_time_ms = float(inner_last_total) + overhead_per_run

    benchmark_result["total_time_ms"] = round(total_time_ms, 3)
    benchmark_result["avg_total_time_ms"] = round(avg_total_time_ms, 3)
    benchmark_result["min_total_time_ms"] = round(min_total_time_ms, 3)
    benchmark_result["max_total_time_ms"] = round(max_total_time_ms, 3)

    return benchmark_result


@app.template_filter("is_rsa_key")
def is_rsa_key(value):
    data = parse_rsa_key(value)

    if "private_key" in data or "public_key" in data:
        return True

    if isinstance(value, str):
        return "PRIVATE KEY" in value and "PUBLIC KEY" in value

    return False


@app.template_filter("private_key")
def private_key(value):
    data = parse_rsa_key(value)

    if "private_key" in data:
        return data["private_key"]

    return value


@app.template_filter("public_key")
def public_key(value):
    data = parse_rsa_key(value)

    if "public_key" in data:
        return data["public_key"]

    return value


@app.route("/")
def index():
    db = get_session()

    try:
        stats = crud.get_stats(db)
        return render_template("index.html", stats=stats)
    finally:
        db.close()


@app.route("/algorithms")
def show_algorithms():
    db = get_session()

    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        edit_algorithm_id = request.args.get("edit_algorithm", type=int)

        algorithms, pagination = crud.get_algorithms_paginated(db, page, per_page)
        edit_algorithm = crud.get_algorithm(db, edit_algorithm_id) if edit_algorithm_id else None

        return render_template(
            "algorithms.html",
            algorithms=algorithms,
            pagination=pagination,
            edit_algorithm=edit_algorithm,
        )
    finally:
        db.close()


@app.route("/algorithms/save", methods=["POST"])
def save_algorithm():
    db = get_session()

    try:
        algorithm_id = request.form.get("algorithm_id", type=int)
        name = request.form.get("name") or request.form.get("algorithm_name")
        algorithm_type = request.form.get("type") or request.form.get("algorithm_type")

        if not name or not algorithm_type:
            flash("Completează numele și tipul algoritmului.", "danger")
            return redirect(url_for("show_algorithms"))

        crud.save_algorithm(db, name, algorithm_type, algorithm_id)

        if algorithm_id:
            flash("Algoritmul a fost actualizat cu succes.", "success")
        else:
            flash("Algoritmul a fost adăugat cu succes.", "success")

        return redirect(url_for("show_algorithms"))
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
        return redirect(url_for("show_algorithms"))
    finally:
        db.close()


@app.route("/algorithms/delete/<int:algorithm_id>")
def delete_algorithm(algorithm_id):
    db = get_session()

    try:
        crud.delete_algorithm(db, algorithm_id)
        flash("Algoritmul a fost șters cu succes.", "success")
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
    finally:
        db.close()

    return redirect(url_for("show_algorithms"))


@app.route("/frameworks")
def show_frameworks():
    db = get_session()

    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        edit_framework_id = request.args.get("edit_framework", type=int)

        frameworks, pagination = crud.get_frameworks_paginated(db, page, per_page)
        edit_framework = crud.get_framework(db, edit_framework_id) if edit_framework_id else None

        return render_template(
            "frameworks.html",
            frameworks=frameworks,
            pagination=pagination,
            edit_framework=edit_framework,
        )
    finally:
        db.close()


@app.route("/frameworks/save", methods=["POST"])
def save_framework():
    db = get_session()

    try:
        framework_id = request.form.get("framework_id", type=int)
        name = request.form.get("name")

        if not name:
            flash("Completează numele framework-ului.", "danger")
            return redirect(url_for("show_frameworks"))

        crud.save_framework(db, name, framework_id)

        if framework_id:
            flash("Framework-ul a fost actualizat cu succes.", "success")
        else:
            flash("Framework-ul a fost adăugat cu succes.", "success")

        return redirect(url_for("show_frameworks"))
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
        return redirect(url_for("show_frameworks"))
    finally:
        db.close()


@app.route("/frameworks/delete/<int:framework_id>")
def delete_framework(framework_id):
    db = get_session()

    try:
        crud.delete_framework(db, framework_id)
        flash("Framework-ul a fost șters cu succes.", "success")
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
    finally:
        db.close()

    return redirect(url_for("show_frameworks"))


@app.route("/files")
def show_files():
    db = get_session()

    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        files, pagination = crud.get_files_paginated(db, page, per_page)

        return render_template(
            "files.html",
            files=files,
            pagination=pagination,
        )
    finally:
        db.close()


@app.route("/files/save", methods=["POST"])
def save_file():
    db = get_session()

    try:
        uploaded_file = request.files.get("upload_file")

        if uploaded_file is None or uploaded_file.filename == "":
            flash("Alege un fișier pentru încărcare.", "danger")
            return redirect(url_for("show_files"))

        original_name = uploaded_file.filename
        stored_name = make_unique_name(original_name)
        original_path = ORIGINAL_DIR / stored_name

        uploaded_file.save(original_path)

        hash_value = crypto_services.sha256_file(str(original_path))
        size_bytes = original_path.stat().st_size

        crud.create_file(
            db=db,
            original_name=original_name,
            stored_name=stored_name,
            original_path=str(original_path),
            hash_value=hash_value,
            size_bytes=size_bytes,
        )

        flash("Fișierul a fost încărcat cu succes.", "success")
        return redirect(url_for("show_files"))
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
        return redirect(url_for("show_files"))
    finally:
        db.close()


@app.route("/files/download/<int:file_id>/<kind>")
def download_file(file_id, kind):
    db = get_session()

    try:
        file_obj = crud.get_file(db, file_id)

        if file_obj is None:
            flash("Fișierul nu există.", "danger")
            return redirect(url_for("show_files"))

        if kind == "original":
            path = file_obj.original_path
            download_name = file_obj.original_name
        elif kind == "encrypted":
            path = file_obj.encrypted_path
            download_name = file_obj.encrypted_name
        elif kind == "decrypted":
            path = file_obj.decrypted_path
            download_name = file_obj.decrypted_name
        else:
            flash("Tip de fișier invalid.", "danger")
            return redirect(url_for("show_files"))

        if not path or not Path(path).exists():
            flash("Fișierul nu există pe disc.", "danger")
            return redirect(url_for("show_files"))

        return send_file(path, as_attachment=True, download_name=download_name)
    finally:
        db.close()


@app.route("/files/delete/<int:file_id>")
def delete_file(file_id):
    db = get_session()

    try:
        file_obj = crud.get_file(db, file_id)

        if file_obj:
            paths = [
                file_obj.original_path,
                file_obj.encrypted_path,
                file_obj.decrypted_path,
            ]

            for path in paths:
                if path and Path(path).exists():
                    Path(path).unlink()

        crud.delete_file(db, file_id)
        flash("Fișierul a fost șters cu succes.", "success")
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
    finally:
        db.close()

    return redirect(url_for("show_files"))


@app.route("/keys")
def show_keys():
    db = get_session()

    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        keys, pagination = crud.get_keys_paginated(db, page, per_page)
        algorithms = crud.get_all_algorithms(db)

        return render_template(
            "keys.html",
            keys=keys,
            algorithms=algorithms,
            pagination=pagination,
        )
    finally:
        db.close()


@app.route("/keys/save", methods=["POST"])
def save_key():
    db = get_session()

    try:
        algorithm_id = request.form.get("algorithm_id", type=int)
        key_value = request.form.get("key_value")

        if not algorithm_id or not key_value:
            flash("Completează algoritmul și valoarea cheii.", "danger")
            return redirect(url_for("show_keys"))

        crud.create_key(db, algorithm_id, key_value)
        flash("Cheia a fost adăugată cu succes.", "success")

        return redirect(url_for("show_keys"))
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
        return redirect(url_for("show_keys"))
    finally:
        db.close()


@app.route("/keys/generate-aes", methods=["POST"])
def generate_aes_key():
    db = get_session()

    try:
        algorithm_id = request.form.get("algorithm_id", type=int)

        if not algorithm_id:
            flash("Selectează algoritmul AES.", "danger")
            return redirect(url_for("show_keys"))

        key_value = crypto_services.generate_aes_key()
        crud.create_key(db, algorithm_id, key_value)

        flash("Cheia AES a fost generată cu succes.", "success")
        return redirect(url_for("show_keys"))
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
        return redirect(url_for("show_keys"))
    finally:
        db.close()


@app.route("/keys/generate-rsa", methods=["POST"])
def generate_rsa_key():
    db = get_session()

    try:
        algorithm_id = request.form.get("algorithm_id", type=int)

        if not algorithm_id:
            flash("Selectează algoritmul RSA.", "danger")
            return redirect(url_for("show_keys"))

        if hasattr(crypto_services, "generate_rsa_key_pair"):
            key_value = crypto_services.generate_rsa_key_pair()
        else:
            key_value = crypto_services.generate_rsa_key()

        if isinstance(key_value, dict):
            key_value = json.dumps(key_value, ensure_ascii=False)

        crud.create_key(db, algorithm_id, key_value)

        flash("Perechea de chei RSA a fost generată cu succes.", "success")
        return redirect(url_for("show_keys"))
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
        return redirect(url_for("show_keys"))
    finally:
        db.close()


@app.route("/keys/delete/<int:key_id>")
def delete_key(key_id):
    db = get_session()

    try:
        crud.delete_key(db, key_id)
        flash("Cheia a fost ștearsă cu succes.", "success")
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
    finally:
        db.close()

    return redirect(url_for("show_keys"))


@app.route("/operations")
def show_operations():
    db = get_session()

    try:
        files = crud.get_all_files(db)
        algorithms = crud.get_all_algorithms(db)
        keys = crud.get_all_keys(db)
        frameworks = crud.get_all_frameworks(db)

        return render_template(
            "operations.html",
            files=files,
            algorithms=algorithms,
            keys=keys,
            frameworks=frameworks,
        )
    finally:
        db.close()


@app.route("/operations/run", methods=["POST"])
def run_operation():
    db = get_session()

    try:
        file_id = request.form.get("file_id", type=int)
        algorithm_id = request.form.get("algorithm_id", type=int)
        key_id = request.form.get("key_id", type=int)
        framework_id = request.form.get("framework_id", type=int)
        operation = request.form.get("operation")
        benchmark_runs = request.form.get("benchmark_runs", 1, type=int)

        if benchmark_runs < 1:
            benchmark_runs = 1

        file_obj = crud.get_file(db, file_id)
        algorithm = crud.get_algorithm(db, algorithm_id)
        key = crud.get_key(db, key_id)
        framework = crud.get_framework(db, framework_id)

        if file_obj is None or algorithm is None or key is None or framework is None:
            flash("Datele selectate nu sunt valide.", "danger")
            return redirect(url_for("show_operations"))

        if operation not in ["encrypt", "decrypt"]:
            flash("Operația selectată nu este validă.", "danger")
            return redirect(url_for("show_operations"))

        total_operation_start = time.perf_counter()

        input_path = get_input_path_for_operation(file_obj, operation)

        if not input_path or not Path(input_path).exists():
            if operation == "decrypt":
                flash("Pentru decriptare trebuie să existe mai întâi un fișier criptat.", "danger")
            else:
                flash("Fișierul original nu există pe disc.", "danger")

            return redirect(url_for("show_operations"))

        input_size_bytes = Path(input_path).stat().st_size

        output_name, output_path = get_output_path(file_obj, operation)

        benchmark_result = crypto_services.run_crypto_operation(
            operation=operation,
            algorithm_name=algorithm.name,
            framework_name=framework.name,
            key_value=key.key_value,
            input_path=input_path,
            output_path=output_path,
            runs=benchmark_runs,
        )

        output_path_obj = Path(output_path)

        if not output_path_obj.exists():
            flash("Operația nu a generat fișierul rezultat.", "danger")
            return redirect(url_for("show_operations"))

        output_hash = crypto_services.sha256_file(str(output_path_obj))
        output_size_bytes = output_path_obj.stat().st_size

        crud.update_file_after_operation(
            db=db,
            file_id=file_obj.id,
            operation=operation,
            output_name=output_name,
            output_path=str(output_path_obj),
            output_hash=output_hash,
            output_size=output_size_bytes,
        )

        total_operation_end = time.perf_counter()
        measured_total_operation_ms = (total_operation_end - total_operation_start) * 1000

        benchmark_result = adjust_total_times(
            benchmark_result=benchmark_result,
            measured_total_operation_ms=measured_total_operation_ms,
        )

        crud.create_performance(
            db=db,
            file_id=file_obj.id,
            algorithm_id=algorithm.id,
            framework_id=framework.id,
            key_id=key.id,
            operation=operation_label(operation),
            time_taken_ms=benchmark_result["time_taken_ms"],
            memory_used_kb=benchmark_result["memory_used_kb"],
            total_time_ms=benchmark_result["total_time_ms"],
            runs_count=benchmark_result["runs_count"],
            avg_time_ms=benchmark_result["avg_time_ms"],
            min_time_ms=benchmark_result["min_time_ms"],
            max_time_ms=benchmark_result["max_time_ms"],
            avg_total_time_ms=benchmark_result["avg_total_time_ms"],
            min_total_time_ms=benchmark_result["min_total_time_ms"],
            max_total_time_ms=benchmark_result["max_total_time_ms"],
            avg_memory_kb=benchmark_result["avg_memory_kb"],
            min_memory_kb=benchmark_result["min_memory_kb"],
            max_memory_kb=benchmark_result["max_memory_kb"],
            input_size_bytes=input_size_bytes,
            file_size_bytes=output_size_bytes,
            result_hash=output_hash,
        )

        crypto_ms_per_byte = None
        total_ms_per_byte = None

        if input_size_bytes > 0:
            crypto_ms_per_byte = round(benchmark_result["avg_time_ms"] / input_size_bytes, 9)
            total_ms_per_byte = round(benchmark_result["avg_total_time_ms"] / input_size_bytes, 9)

        message = (
            f"Operația a fost executată cu succes. "
            f"Timp de execuție criptografică mediu: {benchmark_result['avg_time_ms']} ms. "
            f"Timp total al operației mediu: {benchmark_result['avg_total_time_ms']} ms. "
            f"Dimensiune intrare: {input_size_bytes} bytes."
        )

        if crypto_ms_per_byte is not None and total_ms_per_byte is not None:
            message += (
                f" Timp criptografic per octet: {crypto_ms_per_byte} ms/octet. "
                f"Timp total per octet: {total_ms_per_byte} ms/octet."
            )

        flash(message, "success")

        return redirect(url_for("show_performances"))
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
        return redirect(url_for("show_operations"))
    finally:
        db.close()


@app.route("/performances")
def show_performances():
    db = get_session()

    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 5, type=int)

        performances, pagination = crud.get_performances_paginated(db, page, per_page)
        summary = crud.get_performance_summary(db)

        chart_labels = [
            f"{row['algorithm_name']} · {row['framework_name']} · {row['operation']}"
            for row in summary
        ]

        chart_execution_times = [
            row["avg_time_ms"]
            for row in summary
        ]

        chart_total_times = [
            row["avg_total_time_ms"]
            for row in summary
        ]

        chart_memory = [
            row["avg_memory_kb"]
            for row in summary
        ]

        return render_template(
            "performances.html",
            performances=performances,
            pagination=pagination,
            summary=summary,
            chart_labels=chart_labels,
            chart_execution_times=chart_execution_times,
            chart_total_times=chart_total_times,
            chart_memory=chart_memory,
        )
    finally:
        db.close()


@app.route("/analysis")
def show_analysis():
    db = get_session()

    try:
        analysis_rows = crud.get_performance_analysis(db)

        chart_labels = [
            f"{row['algorithm_name']} · {row['framework_name']} · {row['operation']}"
            for row in analysis_rows
        ]

        chart_crypto_per_byte = [
            row["avg_crypto_ms_per_byte"]
            for row in analysis_rows
        ]

        chart_total_per_byte = [
            row["avg_total_ms_per_byte"]
            for row in analysis_rows
        ]

        chart_memory = [
            row["avg_memory_kb"]
            for row in analysis_rows
        ]

        return render_template(
            "analysis.html",
            analysis_rows=analysis_rows,
            chart_labels=chart_labels,
            chart_crypto_per_byte=chart_crypto_per_byte,
            chart_total_per_byte=chart_total_per_byte,
            chart_memory=chart_memory,
        )
    finally:
        db.close()


@app.route("/performances/delete/<int:performance_id>")
def delete_performance(performance_id):
    db = get_session()

    try:
        crud.delete_performance(db, performance_id)
        flash("Înregistrarea de performanță a fost ștearsă cu succes.", "success")
    except Exception as exception:
        db.rollback()
        flash(str(exception), "danger")
    finally:
        db.close()

    return redirect(url_for("show_performances"))


if __name__ == "__main__":
    app.run(debug=True)