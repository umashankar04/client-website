import os
from datetime import datetime
from typing import Optional, Dict, Any

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    from sqlalchemy import (create_engine, Column, String, Text, DateTime)
    from sqlalchemy.orm import declarative_base, sessionmaker

    engine = create_engine(DATABASE_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base = declarative_base()

    class Client(Base):
        __tablename__ = "clients"
        client_id = Column(String, primary_key=True, index=True)
        name = Column(String, nullable=False)
        mobile = Column(String, nullable=True)
        email = Column(String, nullable=True)
        address = Column(Text, nullable=True)
        username = Column(String, nullable=True)
        password = Column(String, nullable=True)
        status = Column(String, default="Active")
        reg_date = Column(String, default=lambda: datetime.utcnow().isoformat())

    class Setting(Base):
        __tablename__ = "settings"
        key = Column(String, primary_key=True)
        value = Column(Text)

    def init_db():
        Base.metadata.create_all(bind=engine)

    def is_enabled() -> bool:
        return True

    def get_client_by_name(name: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as s:
            c = s.query(Client).filter(Client.name.ilike(name)).first()
            if not c:
                return None
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def create_client(data: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as s:
            c = Client(**data)
            s.add(c)
            s.commit()
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def update_client_password(client_id: str, new_hash: str) -> None:
        with SessionLocal() as s:
            c = s.query(Client).filter(Client.client_id == client_id).first()
            if c:
                c.password = new_hash
                s.commit()

    def get_setting(key: str, default: str = "") -> str:
        with SessionLocal() as s:
            r = s.query(Setting).filter(Setting.key == key).first()
            return r.value if r else default

    def set_setting(key: str, value: str) -> None:
        with SessionLocal() as s:
            r = s.query(Setting).filter(Setting.key == key).first()
            if r:
                r.value = value
            else:
                r = Setting(key=key, value=value)
                s.add(r)
            s.commit()

else:
    # DB disabled fallbacks
    def init_db():
        return None

    def is_enabled() -> bool:
        return False

    def get_client_by_name(name: str):
        return None

    def create_client(data: dict):
        raise RuntimeError("DB not enabled")

    def update_client_password(client_id: str, new_hash: str) -> None:
        raise RuntimeError("DB not enabled")

    def get_setting(key: str, default: str = "") -> str:
        return default

    def set_setting(key: str, value: str) -> None:
        raise RuntimeError("DB not enabled")
