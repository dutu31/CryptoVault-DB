from dataclasses import dataclass
from typing import Optional


@dataclass
class Algorithm:
    id: int
    name: str
    type: str
    description: Optional[str]
    is_active: int


@dataclass
class Framework:
    id: int
    name: str
    version: Optional[str]
    notes: Optional[str]


@dataclass
class CryptoKey:
    id: int
    algorithm_id: int
    name: str
    key_size: Optional[int]
    public_key_path: Optional[str]
    private_key_path: Optional[str]
    secret_key_hex: Optional[str]
    created_at: str


@dataclass
class ManagedFile:
    id: int
    original_name: str
    stored_path: str
    file_size: int
    sha256: str
    status: str
    created_at: str


@dataclass
class Operation:
    id: int
    operation_type: str
    algorithm_id: int
    framework_id: int
    key_id: Optional[int]
    input_file_id: Optional[int]
    output_path: Optional[str]
    status: str
    duration_ms: Optional[float]
    memory_kb: Optional[float]
    details: Optional[str]
    created_at: str