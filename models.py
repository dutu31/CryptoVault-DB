from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
import datetime

from database import Base


class Algorithm(Base):
    __tablename__ = "algorithms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(50), nullable=False)

    keys = relationship("Key", back_populates="algorithm", cascade="all, delete-orphan")
    performances = relationship("Performance", back_populates="algorithm", cascade="all, delete-orphan")


class Key(Base):
    __tablename__ = "keys"

    id = Column(Integer, primary_key=True, index=True)
    algorithm_id = Column(Integer, ForeignKey("algorithms.id", ondelete="CASCADE"), nullable=False)
    key_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    algorithm = relationship("Algorithm", back_populates="keys")
    performances = relationship("Performance", back_populates="key", passive_deletes=True)


class Framework(Base):
    __tablename__ = "frameworks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)

    performances = relationship("Performance", back_populates="framework", cascade="all, delete-orphan")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=True)
    original_path = Column(String(500), nullable=True)
    encrypted_name = Column(String(255), nullable=True)
    encrypted_path = Column(String(500), nullable=True)
    decrypted_name = Column(String(255), nullable=True)
    decrypted_path = Column(String(500), nullable=True)
    status = Column(String(50), default="Ne-criptat", nullable=False)
    hash_value = Column(String(256), nullable=True)
    encrypted_hash = Column(String(256), nullable=True)
    decrypted_hash = Column(String(256), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=True)

    performances = relationship("Performance", back_populates="file", cascade="all, delete-orphan")


class Performance(Base):
    __tablename__ = "performances"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    algorithm_id = Column(Integer, ForeignKey("algorithms.id", ondelete="CASCADE"), nullable=False)
    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False)
    key_id = Column(Integer, ForeignKey("keys.id", ondelete="SET NULL"), nullable=True)
    operation = Column(String(50), nullable=False)
    time_taken_ms = Column(Float, nullable=True)
    memory_used_kb = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    result_hash = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=True)

    file = relationship("File", back_populates="performances")
    algorithm = relationship("Algorithm", back_populates="performances")
    framework = relationship("Framework", back_populates="performances")
    key = relationship("Key", back_populates="performances")