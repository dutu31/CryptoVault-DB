import uuid

import database
import crud


def print_ok(message: str):
    print(f"[OK] {message}")


def main():
    database.initialize_database()
    db = database.get_session()

    suffix = uuid.uuid4().hex[:8]

    algorithm_id = None
    key_id = None
    framework_id = None
    file_id = None
    performance_id = None

    try:
        algorithm = crud.create_algorithm(db, f"TEST-ALG-{suffix}", "Simetric")
        algorithm_id = algorithm.id
        assert algorithm.id is not None
        print_ok("CREATE algorithm")

        algorithms = crud.get_all_algorithms(db)
        assert any(a.id == algorithm_id for a in algorithms)
        print_ok("READ algorithms")

        updated_algorithm = crud.update_algorithm(db, algorithm_id, f"TEST-ALG-UPD-{suffix}", "Asimetric")
        assert updated_algorithm is not None
        assert updated_algorithm.name == f"TEST-ALG-UPD-{suffix}"
        assert updated_algorithm.type == "Asimetric"
        print_ok("UPDATE algorithm")

        framework = crud.create_framework(db, f"TEST-FRAMEWORK-{suffix}")
        framework_id = framework.id
        assert framework.id is not None
        print_ok("CREATE framework")

        frameworks = crud.get_all_frameworks(db)
        assert any(f.id == framework_id for f in frameworks)
        print_ok("READ frameworks")

        updated_framework = crud.update_framework(db, framework_id, f"TEST-FRAMEWORK-UPD-{suffix}")
        assert updated_framework is not None
        assert updated_framework.name == f"TEST-FRAMEWORK-UPD-{suffix}"
        print_ok("UPDATE framework")

        key = crud.create_key(db, algorithm_id, f"TEST-KEY-VALUE-{suffix}")
        key_id = key.id
        assert key.id is not None
        print_ok("CREATE key")

        keys = crud.get_all_keys(db)
        assert any(k.id == key_id for k in keys)
        print_ok("READ keys")

        file = crud.create_file(
            db,
            original_name=f"test_file_{suffix}.txt",
            stored_name=f"stored_{suffix}.txt",
            original_path=f"data/original/stored_{suffix}.txt",
            status="Ne-criptat",
            hash_value="abc123",
            size_bytes=100
        )
        file_id = file.id
        assert file.id is not None
        print_ok("CREATE file")

        files = crud.get_all_files(db)
        assert any(f.id == file_id for f in files)
        print_ok("READ files")

        encrypted_file = crud.update_file_after_encrypt(
            db,
            file_id,
            encrypted_name=f"test_file_{suffix}.enc",
            encrypted_path=f"data/encrypted/test_file_{suffix}.enc",
            encrypted_hash="def456"
        )
        assert encrypted_file is not None
        assert encrypted_file.status == "Criptat"
        assert encrypted_file.encrypted_hash == "def456"
        print_ok("UPDATE file after encrypt")

        decrypted_file = crud.update_file_after_decrypt(
            db,
            file_id,
            decrypted_name=f"test_file_{suffix}.dec",
            decrypted_path=f"data/decrypted/test_file_{suffix}.dec",
            decrypted_hash="ghi789"
        )
        assert decrypted_file is not None
        assert decrypted_file.status == "Decriptat"
        assert decrypted_file.decrypted_hash == "ghi789"
        print_ok("UPDATE file after decrypt")

        performance = crud.create_performance(
            db,
            file_id=file_id,
            algorithm_id=algorithm_id,
            framework_id=framework_id,
            key_id=key_id,
            operation="Criptare",
            time_taken_ms=12.5,
            memory_used_kb=256.0,
            file_size_bytes=128,
            result_hash="hash123"
        )
        performance_id = performance.id
        assert performance.id is not None
        print_ok("CREATE performance")

        performances = crud.get_all_performances(db)
        assert any(p.id == performance_id for p in performances)
        print_ok("READ performances")

        assert crud.delete_performance(db, performance_id) is True
        performance_id = None
        print_ok("DELETE performance")

        assert crud.delete_key(db, key_id) is True
        key_id = None
        print_ok("DELETE key")

        assert crud.delete_file(db, file_id) is True
        file_id = None
        print_ok("DELETE file")

        assert crud.delete_framework(db, framework_id) is True
        framework_id = None
        print_ok("DELETE framework")

        assert crud.delete_algorithm(db, algorithm_id) is True
        algorithm_id = None
        print_ok("DELETE algorithm")

        print("\nToate testele pentru baza proiectului au trecut cu succes.")

    finally:
        db.close()


if __name__ == "__main__":
    main()