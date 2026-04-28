import json
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, send_file

import database
import crud
import crypto_services

app = Flask(__name__)
app.secret_key = "cheie_super_secreta_pentru_proiect"


def load_key_json(key_value):
    try:
        key_data = json.loads(key_value)
    except Exception:
        return None

    if not isinstance(key_data, dict):
        return None

    return key_data


def clean_pem_key(value):
    if not value:
        return ""

    lines = value.replace("\r", "").split("\n")
    clean_lines = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("-----BEGIN"):
            continue

        if line.startswith("-----END"):
            continue

        clean_lines.append(line)

    return "\n".join(clean_lines)


def is_rsa_key(key_value):
    key_data = load_key_json(key_value)

    if key_data is None:
        return False

    return "private_key" in key_data and "public_key" in key_data


def private_key_for_display(key_value):
    key_data = load_key_json(key_value)

    if key_data is None:
        return key_value

    return clean_pem_key(key_data.get("private_key", ""))


def public_key_for_display(key_value):
    key_data = load_key_json(key_value)

    if key_data is None:
        return ""

    return clean_pem_key(key_data.get("public_key", ""))


app.jinja_env.filters["is_rsa_key"] = is_rsa_key
app.jinja_env.filters["private_key"] = private_key_for_display
app.jinja_env.filters["public_key"] = public_key_for_display

database.initialize_database()
crypto_services.ensure_data_directories()


@app.route("/")
def index():
    db = database.get_session()
    try:
        stats = {
            "algorithms": len(crud.get_all_algorithms(db)),
            "crypto_keys": len(crud.get_all_keys(db)),
            "frameworks": len(crud.get_all_frameworks(db)),
            "files": len(crud.get_all_files(db)),
            "performances": len(crud.get_all_performances(db))
        }

        return render_template("index.html", stats=stats)
    finally:
        db.close()


@app.route("/algorithms")
def show_algorithms():
    db = database.get_session()
    try:
        edit_algorithm_id = request.args.get("edit_algorithm", type=int)
        algorithms = crud.get_all_algorithms(db)
        edit_algorithm = crud.get_algorithm_by_id(db, edit_algorithm_id) if edit_algorithm_id else None

        return render_template("algorithms.html", algorithms=algorithms, edit_algorithm=edit_algorithm)
    finally:
        db.close()


@app.route("/algorithm/save", methods=["POST"])
def save_algorithm():
    db = database.get_session()
    try:
        algorithm_id = request.form.get("algorithm_id", type=int)
        name = request.form.get("name", "").strip()
        algo_type = request.form.get("type", "").strip()

        if not name or not algo_type:
            flash("Completează numele și tipul algoritmului.", "danger")
            return redirect(url_for("show_algorithms"))

        existing_algorithm = crud.get_algorithm_by_name(db, name)

        if algorithm_id:
            if existing_algorithm and existing_algorithm.id != algorithm_id:
                flash("Există deja un algoritm cu acest nume în listă.", "warning")
                return redirect(url_for("show_algorithms"))

            algo = crud.update_algorithm(db, algorithm_id, name, algo_type)
            if algo:
                flash("Algoritmul a fost actualizat cu succes.", "success")
            else:
                flash("Algoritmul nu a fost găsit.", "danger")
        else:
            if existing_algorithm:
                flash("Algoritmul există deja în listă.", "warning")
                return redirect(url_for("show_algorithms"))

            crud.create_algorithm(db, name, algo_type)
            flash("Algoritmul a fost adăugat cu succes.", "success")

    except Exception as exc:
        db.rollback()
        flash(f"Eroare la salvarea algoritmului: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_algorithms"))


@app.route("/algorithm/delete/<int:algo_id>")
def delete_algorithm(algo_id):
    db = database.get_session()
    try:
        deleted = crud.delete_algorithm(db, algo_id)
        if deleted:
            flash("Algoritmul a fost șters cu succes.", "warning")
        else:
            flash("Algoritmul nu a fost găsit.", "danger")
    except Exception as exc:
        db.rollback()
        flash(f"Eroare la ștergerea algoritmului: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_algorithms"))


@app.route("/keys")
def show_keys():
    db = database.get_session()
    try:
        keys = crud.get_all_keys(db)
        algorithms = crud.get_all_algorithms(db)

        return render_template("keys.html", keys=keys, algorithms=algorithms)
    finally:
        db.close()


@app.route("/key/save", methods=["POST"])
def save_key():
    db = database.get_session()
    try:
        algorithm_id = request.form.get("algorithm_id", type=int)
        key_value = request.form.get("key_value", "").strip()

        if algorithm_id is None or not key_value:
            flash("Completează algoritmul și valoarea cheii.", "danger")
            return redirect(url_for("show_keys"))

        existing_key = crud.get_key_by_algorithm_and_value(db, algorithm_id, key_value)

        if existing_key:
            flash("Această cheie există deja pentru algoritmul selectat.", "warning")
            return redirect(url_for("show_keys"))

        crud.create_key(db, algorithm_id, key_value)
        flash("Cheia a fost adăugată cu succes.", "success")

    except Exception as exc:
        db.rollback()
        flash(f"Eroare la salvarea cheii: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_keys"))


@app.route("/key/generate-aes", methods=["POST"])
def generate_aes_key():
    db = database.get_session()
    try:
        algorithm_id = request.form.get("algorithm_id", type=int)
        algorithm = crud.get_algorithm_by_id(db, algorithm_id)

        if algorithm is None:
            flash("Algoritmul AES nu a fost găsit.", "danger")
            return redirect(url_for("show_keys"))

        if "AES" not in algorithm.name.upper():
            flash("Selectează un algoritm AES pentru generarea cheii.", "danger")
            return redirect(url_for("show_keys"))

        key_value = crypto_services.generate_aes_key()
        crud.create_key(db, algorithm.id, key_value)
        flash("Cheia AES a fost generată și salvată în baza de date.", "success")

    except Exception as exc:
        db.rollback()
        flash(f"Eroare la generarea cheii AES: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_keys"))


@app.route("/key/generate-rsa", methods=["POST"])
def generate_rsa_key():
    db = database.get_session()
    try:
        algorithm_id = request.form.get("algorithm_id", type=int)
        algorithm = crud.get_algorithm_by_id(db, algorithm_id)

        if algorithm is None:
            flash("Algoritmul RSA nu a fost găsit.", "danger")
            return redirect(url_for("show_keys"))

        if "RSA" not in algorithm.name.upper():
            flash("Selectează un algoritm RSA pentru generarea cheii.", "danger")
            return redirect(url_for("show_keys"))

        key_value = crypto_services.generate_rsa_key_pair_openssl()
        crud.create_key(db, algorithm.id, key_value)
        flash("Perechea de chei RSA a fost generată cu OpenSSL și salvată în baza de date.", "success")

    except Exception as exc:
        db.rollback()
        flash(f"Eroare la generarea cheii RSA: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_keys"))


@app.route("/key/delete/<int:key_id>")
def delete_key(key_id):
    db = database.get_session()
    try:
        deleted = crud.delete_key(db, key_id)
        if deleted:
            flash("Cheia a fost ștearsă cu succes.", "warning")
        else:
            flash("Cheia nu a fost găsită.", "danger")
    except Exception as exc:
        db.rollback()
        flash(f"Eroare la ștergerea cheii: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_keys"))


@app.route("/frameworks")
def show_frameworks():
    db = database.get_session()
    try:
        edit_framework_id = request.args.get("edit_framework", type=int)
        frameworks = crud.get_all_frameworks(db)
        edit_framework = crud.get_framework_by_id(db, edit_framework_id) if edit_framework_id else None

        return render_template("frameworks.html", frameworks=frameworks, edit_framework=edit_framework)
    finally:
        db.close()


@app.route("/framework/save", methods=["POST"])
def save_framework():
    db = database.get_session()
    try:
        framework_id = request.form.get("framework_id", type=int)
        name = request.form.get("name", "").strip()

        if not name:
            flash("Completează numele framework-ului.", "danger")
            return redirect(url_for("show_frameworks"))

        existing_framework = crud.get_framework_by_name(db, name)

        if framework_id:
            if existing_framework and existing_framework.id != framework_id:
                flash("Există deja un framework cu acest nume în listă.", "warning")
                return redirect(url_for("show_frameworks"))

            framework = crud.update_framework(db, framework_id, name)
            if framework:
                flash("Framework-ul a fost actualizat cu succes.", "success")
            else:
                flash("Framework-ul nu a fost găsit.", "danger")
        else:
            if existing_framework:
                flash("Framework-ul există deja în listă.", "warning")
                return redirect(url_for("show_frameworks"))

            crud.create_framework(db, name)
            flash("Framework-ul a fost adăugat cu succes.", "success")

    except Exception as exc:
        db.rollback()
        flash(f"Eroare la salvarea framework-ului: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_frameworks"))


@app.route("/framework/delete/<int:framework_id>")
def delete_framework(framework_id):
    db = database.get_session()
    try:
        deleted = crud.delete_framework(db, framework_id)
        if deleted:
            flash("Framework-ul a fost șters cu succes.", "warning")
        else:
            flash("Framework-ul nu a fost găsit.", "danger")
    except Exception as exc:
        db.rollback()
        flash(f"Eroare la ștergerea framework-ului: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_frameworks"))


@app.route("/files")
def show_files():
    db = database.get_session()
    try:
        files = crud.get_all_files(db)
        return render_template("files.html", files=files)
    finally:
        db.close()


@app.route("/file/save", methods=["POST"])
def save_file():
    db = database.get_session()
    try:
        uploaded_file = request.files.get("upload_file")

        if uploaded_file is None or uploaded_file.filename.strip() == "":
            flash("Încarcă un fișier.", "danger")
            return redirect(url_for("show_files"))

        original_name = uploaded_file.filename.strip()
        stored_name = crypto_services.unique_file_name(original_name)
        save_path = crypto_services.ORIGINAL_DIR / stored_name

        uploaded_file.save(save_path)

        hash_value = crypto_services.sha256_file(save_path)
        size_bytes = save_path.stat().st_size

        crud.create_file(
            db,
            original_name=original_name,
            stored_name=stored_name,
            original_path=str(save_path),
            status="Ne-criptat",
            hash_value=hash_value,
            size_bytes=size_bytes
        )

        flash("Fișierul a fost încărcat și salvat în baza de date.", "success")

    except Exception as exc:
        db.rollback()
        flash(f"Eroare la salvarea fișierului: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_files"))


@app.route("/file/delete/<int:file_id>")
def delete_file(file_id):
    db = database.get_session()
    try:
        deleted = crud.delete_file(db, file_id)
        if deleted:
            flash("Fișierul a fost șters din baza de date.", "warning")
        else:
            flash("Fișierul nu a fost găsit.", "danger")
    except Exception as exc:
        db.rollback()
        flash(f"Eroare la ștergerea fișierului: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_files"))


@app.route("/file/download/<int:file_id>/<kind>")
def download_file(file_id, kind):
    db = database.get_session()
    path_value = None
    download_name = None

    try:
        db_file = crud.get_file_by_id(db, file_id)

        if db_file is None:
            flash("Fișierul nu a fost găsit.", "danger")
            return redirect(url_for("show_files"))

        if kind == "original":
            path_value = db_file.original_path
            download_name = db_file.original_name
        elif kind == "encrypted":
            path_value = db_file.encrypted_path
            download_name = db_file.encrypted_name
        elif kind == "decrypted":
            path_value = db_file.decrypted_path
            download_name = db_file.decrypted_name
        else:
            flash("Tip de descărcare invalid.", "danger")
            return redirect(url_for("show_files"))

        if not path_value or not Path(path_value).exists():
            flash("Fișierul fizic nu există pe disc.", "danger")
            return redirect(url_for("show_files"))

    finally:
        db.close()

    return send_file(path_value, as_attachment=True, download_name=download_name)


@app.route("/operations")
def show_operations():
    db = database.get_session()
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
            frameworks=frameworks
        )
    finally:
        db.close()


@app.route("/operation/run", methods=["POST"])
def run_operation():
    db = database.get_session()
    try:
        file_id = request.form.get("file_id", type=int)
        algorithm_id = request.form.get("algorithm_id", type=int)
        key_id = request.form.get("key_id", type=int)
        framework_id = request.form.get("framework_id", type=int)
        operation = request.form.get("operation", "").strip()

        if file_id is None or algorithm_id is None or key_id is None or framework_id is None or not operation:
            flash("Selectează fișierul, algoritmul, cheia, framework-ul și operația.", "danger")
            return redirect(url_for("show_operations"))

        db_file = crud.get_file_by_id(db, file_id)
        algorithm = crud.get_algorithm_by_id(db, algorithm_id)
        key = crud.get_key_by_id(db, key_id)
        framework = crud.get_framework_by_id(db, framework_id)

        if db_file is None or algorithm is None or key is None or framework is None:
            flash("Datele selectate nu sunt valide.", "danger")
            return redirect(url_for("show_operations"))

        if key.algorithm_id != algorithm.id:
            flash("Cheia selectată nu aparține algoritmului ales.", "danger")
            return redirect(url_for("show_operations"))

        if operation == "encrypt":
            if not db_file.original_path or not Path(db_file.original_path).exists():
                flash("Fișierul original nu există pe disc.", "danger")
                return redirect(url_for("show_operations"))

            input_path = Path(db_file.original_path)
            output_name = crypto_services.output_file_name(db_file.original_name, "encrypted", ".enc")
            output_path = crypto_services.ENCRYPTED_DIR / output_name
            operation_label = "Criptare"

        elif operation == "decrypt":
            if not db_file.encrypted_path or not Path(db_file.encrypted_path).exists():
                flash("Nu există fișier criptat pentru decriptare.", "danger")
                return redirect(url_for("show_operations"))

            input_path = Path(db_file.encrypted_path)
            output_name = crypto_services.output_file_name(db_file.original_name, "decrypted", "")
            output_path = crypto_services.DECRYPTED_DIR / output_name
            operation_label = "Decriptare"

        else:
            flash("Operația selectată nu este validă.", "danger")
            return redirect(url_for("show_operations"))

        time_ms, memory_kb = crypto_services.run_crypto_operation(
            algorithm.name,
            framework.name,
            operation,
            input_path,
            output_path,
            key.key_value
        )

        result_hash = crypto_services.sha256_file(output_path)
        file_size_bytes = output_path.stat().st_size

        if operation == "encrypt":
            crud.update_file_after_encrypt(
                db,
                db_file.id,
                output_name,
                str(output_path),
                result_hash
            )
        else:
            crud.update_file_after_decrypt(
                db,
                db_file.id,
                output_name,
                str(output_path),
                result_hash
            )

        crud.create_performance(
            db,
            file_id=db_file.id,
            algorithm_id=algorithm.id,
            framework_id=framework.id,
            key_id=key.id,
            operation=operation_label,
            time_taken_ms=time_ms,
            memory_used_kb=memory_kb,
            file_size_bytes=file_size_bytes,
            result_hash=result_hash
        )

        flash(f"Operația de {operation_label.lower()} a fost realizată cu succes.", "success")

    except Exception as exc:
        db.rollback()
        flash(f"Eroare la executarea operației: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_operations"))


@app.route("/performances")
def show_performances():
    db = database.get_session()
    try:
        performances = crud.get_all_performances(db)
        return render_template("performances.html", performances=performances)
    finally:
        db.close()


@app.route("/performance/delete/<int:performance_id>")
def delete_performance(performance_id):
    db = database.get_session()
    try:
        deleted = crud.delete_performance(db, performance_id)
        if deleted:
            flash("Înregistrarea de performanță a fost ștearsă.", "warning")
        else:
            flash("Înregistrarea de performanță nu a fost găsită.", "danger")
    except Exception as exc:
        db.rollback()
        flash(f"Eroare la ștergerea performanței: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_performances"))


if __name__ == "__main__":
    print("=== Serverul Web CryptoVault a pornit! ===")
    app.run(debug=True)