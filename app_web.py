from flask import Flask, render_template, request, redirect, url_for, flash

import database
import crud

app = Flask(__name__)
app.secret_key = "cheie_super_secreta_pentru_proiect"

database.initialize_database()


def empty_to_none(value: str):
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def parse_optional_float(value: str):
    value = empty_to_none(value)
    if value is None:
        return None
    return float(value)


@app.route("/")
def index():
    db = database.get_session()
    try:
        stats= {
            "algorithms": len(crud.get_all_algorithms(db)),
            "crypto_keys": len(crud.get_all_keys(db)),
            "frameworks": len(crud.get_all_frameworks(db)),
            "files": len(crud.get_all_files(db)),
            "performances": len(crud.get_all_performances(db))
        }

        return render_template( "index.html", stats=stats )
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

        if algorithm_id:
            algo = crud.update_algorithm(db, algorithm_id, name, algo_type)
            if algo:
                flash("Algoritmul a fost actualizat cu succes.", "success")
            else:
                flash("Algoritmul nu a fost găsit.", "danger")
        else:
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
        edit_key_id = request.args.get("edit_key", type=int)
        keys = crud.get_all_keys(db)
        algorithms = crud.get_all_algorithms(db)
        edit_key = crud.get_key_by_id(db, edit_key_id) if edit_key_id else None
        
        return render_template("keys.html", keys=keys, algorithms=algorithms, edit_key=edit_key)
    finally:
        db.close()

@app.route("/key/save", methods=["POST"])
def save_key():
    db = database.get_session()
    try:
        key_id = request.form.get("key_id", type=int)
        algorithm_id = request.form.get("algorithm_id", type=int)
        key_value = request.form.get("key_value", "").strip()

        if algorithm_id is None or not key_value:
            flash("Completează algoritmul și valoarea cheii.", "danger")
            return redirect(url_for("show_keys"))

        if key_id:
            key = crud.update_key(db, key_id, algorithm_id, key_value)
            if key:
                flash("Cheia a fost actualizată cu succes.", "success")
            else:
                flash("Cheia nu a fost găsită.", "danger")
        else:
            crud.create_key(db, algorithm_id, key_value)
            flash("Cheia a fost adăugată cu succes.", "success")

    except Exception as exc:
        db.rollback()
        flash(f"Eroare la salvarea cheii: {exc}", "danger")
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

        if framework_id:
            framework = crud.update_framework(db, framework_id, name)
            if framework:
                flash("Framework-ul a fost actualizat cu succes.", "success")
            else:
                flash("Framework-ul nu a fost găsit.", "danger")
        else:
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
        edit_file_id = request.args.get("edit_file", type=int)
        files = crud.get_all_files(db)
        edit_file = crud.get_file_by_id(db, edit_file_id) if edit_file_id else None
        
        return render_template("files.html", files=files, edit_file=edit_file)
    finally:
        db.close()

@app.route("/file/save", methods=["POST"])
def save_file():
    db = database.get_session()
    try:
        file_id = request.form.get("file_id", type=int)
        original_name = request.form.get("original_name", "").strip()
        encrypted_name = empty_to_none(request.form.get("encrypted_name"))
        status = request.form.get("status", "").strip()
        hash_value = empty_to_none(request.form.get("hash_value"))

        if not original_name or not status:
            flash("Completează numele original și statusul fișierului.", "danger")
            return redirect(url_for("show_files"))

        if file_id:
            db_file = crud.update_file(db, file_id, original_name, encrypted_name, status, hash_value)
            if db_file:
                flash("Fișierul a fost actualizat cu succes.", "success")
            else:
                flash("Fișierul nu a fost găsit.", "danger")
        else:
            crud.create_file(db, original_name, encrypted_name, status, hash_value)
            flash("Fișierul a fost adăugat cu succes.", "success")

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
            flash("Fișierul a fost șters cu succes.", "warning")
        else:
            flash("Fișierul nu a fost găsit.", "danger")
    except Exception as exc:
        db.rollback()
        flash(f"Eroare la ștergerea fișierului: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_files"))

@app.route("/performances")
def show_performances():
    db = database.get_session()
    try:
        edit_performance_id = request.args.get("edit_performance", type=int)
        
        performances = crud.get_all_performances(db)
        files = crud.get_all_files(db)
        algorithms = crud.get_all_algorithms(db)
        frameworks = crud.get_all_frameworks(db)
        edit_performance = crud.get_performance_by_id(db, edit_performance_id) if edit_performance_id else None
        
        return render_template("performances.html", 
                               performances=performances, 
                               files=files, 
                               algorithms=algorithms, 
                               frameworks=frameworks, 
                               edit_performance=edit_performance)
    finally:
        db.close()

@app.route("/performance/save", methods=["POST"])
def save_performance():
    db = database.get_session()
    try:
        performance_id = request.form.get("performance_id", type=int)
        file_id = request.form.get("file_id", type=int)
        algorithm_id = request.form.get("algorithm_id", type=int)
        framework_id = request.form.get("framework_id", type=int)
        operation = request.form.get("operation", "").strip()
        time_taken_ms = parse_optional_float(request.form.get("time_taken_ms"))
        memory_used_kb = parse_optional_float(request.form.get("memory_used_kb"))

        if file_id is None or algorithm_id is None or framework_id is None or not operation:
            flash("Completează toate câmpurile obligatorii pentru performanță.", "danger")
            return redirect(url_for("show_performances"))

        if performance_id:
            performance = crud.update_performance(
                db,
                performance_id,
                file_id,
                algorithm_id,
                framework_id,
                operation,
                time_taken_ms,
                memory_used_kb,
            )
            if performance:
                flash("Înregistrarea de performanță a fost actualizată cu succes.", "success")
            else:
                flash("Înregistrarea de performanță nu a fost găsită.", "danger")
        else:
            crud.create_performance(
                db,
                file_id,
                algorithm_id,
                framework_id,
                operation,
                time_taken_ms,
                memory_used_kb,
            )
            flash("Înregistrarea de performanță a fost adăugată cu succes.", "success")

    except Exception as exc:
        db.rollback()
        flash(f"Eroare la salvarea performanței: {exc}", "danger")
    finally:
        db.close()

    return redirect(url_for("show_performances"))


@app.route("/performance/delete/<int:performance_id>")
def delete_performance(performance_id):
    db = database.get_session()
    try:
        deleted = crud.delete_performance(db, performance_id)
        if deleted:
            flash("Înregistrarea de performanță a fost ștearsă cu succes.", "warning")
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