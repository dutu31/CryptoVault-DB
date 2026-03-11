CREATE TABLE IF NOT EXISTS algorithms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK(type IN ('symmetric', 'asymmetric')),
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS frameworks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    version TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    algorithm_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    key_size INTEGER,
    public_key_path TEXT,
    private_key_path TEXT,
    secret_key_hex TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (algorithm_id) REFERENCES algorithms(id)
);

CREATE TABLE IF NOT EXISTS managed_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_name TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('plain', 'encrypted', 'decrypted')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL CHECK(operation_type IN ('encrypt', 'decrypt', 'generate_key')),
    algorithm_id INTEGER NOT NULL,
    framework_id INTEGER NOT NULL,
    key_id INTEGER,
    input_file_id INTEGER,
    output_path TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'success', 'failed')),
    duration_ms REAL,
    memory_kb REAL,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (algorithm_id) REFERENCES algorithms(id),
    FOREIGN KEY (framework_id) REFERENCES frameworks(id),
    FOREIGN KEY (key_id) REFERENCES keys(id),
    FOREIGN KEY (input_file_id) REFERENCES managed_files(id)
);