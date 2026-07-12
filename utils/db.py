import os
from dotenv import load_dotenv
# Load .env relative to the project directory
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
from datetime import datetime
from typing import Optional, Dict, Any, List

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Auto-convert standard PostgreSQL schemes to use psycopg3 (since psycopg v3 is installed)
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

    from sqlalchemy import (create_engine, Column, String, Text, DateTime, Float, Integer)
    from sqlalchemy.orm import declarative_base, sessionmaker

    engine = create_engine(DATABASE_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base = declarative_base()

    class Client(Base):
        __tablename__ = "clients"
        client_id = Column(String(50), primary_key=True, index=True)
        name = Column(String(100), nullable=False)
        mobile = Column(String(20), nullable=True)
        email = Column(String(100), nullable=True)
        address = Column(Text, nullable=True)
        username = Column(String(50), nullable=True)
        password = Column(String(255), nullable=True)
        status = Column(String(20), default="Active")
        reg_date = Column(String(50), default=lambda: datetime.utcnow().isoformat())

    class Setting(Base):
        __tablename__ = "settings"
        key = Column(String(100), primary_key=True)
        value = Column(Text)

    class Service(Base):
        __tablename__ = "services"
        service_id = Column(String(50), primary_key=True)
        name = Column(String(100), nullable=False)
        price = Column(Float, nullable=False)

    class Work(Base):
        __tablename__ = "work_records"
        serial = Column(String(50), primary_key=True)
        date = Column(String(50), nullable=True)
        client_id = Column(String(50), nullable=True)
        client_name = Column(String(100), nullable=True)
        service_id = Column(String(50), nullable=True)
        service_name = Column(String(100), nullable=True)
        quantity = Column(Integer, nullable=True)
        price = Column(Float, nullable=True)
        total = Column(Float, nullable=True)
        notes = Column(Text, nullable=True)
        status = Column(String(50), nullable=True)

    class Payment(Base):
        __tablename__ = "payments"
        payment_id = Column(String(50), primary_key=True)
        client_id = Column(String(50), nullable=True)
        client_name = Column(String(100), nullable=True)
        invoice_no = Column(String(50), nullable=True)
        total_amount = Column(Float, nullable=True)
        amount_paid = Column(Float, nullable=True)
        balance = Column(Float, nullable=True)
        payment_date = Column(String(50), nullable=True)
        payment_method = Column(String(50), nullable=True)
        txn_id = Column(String(100), nullable=True)
        status = Column(String(50), nullable=True)

    class Invoice(Base):
        __tablename__ = "invoices"
        invoice_no = Column(String(50), primary_key=True)
        serial = Column(String(100), nullable=True)
        client_id = Column(String(50), nullable=True)
        client_name = Column(String(100), nullable=True)
        date = Column(String(50), nullable=True)
        total = Column(Float, nullable=True)
        status = Column(String(50), nullable=True)
        pdf_path = Column(String(255), nullable=True)

    class Report(Base):
        __tablename__ = "reports"
        report_id = Column(String(50), primary_key=True)
        type = Column(String(50), nullable=True)
        generated_on = Column(String(50), nullable=True)
        file_path = Column(String(255), nullable=True)

    def init_db():
        Base.metadata.create_all(bind=engine)

    def is_enabled() -> bool:
        return True

    # Clients
    def get_all_clients() -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            clients = s.query(Client).all()
            return [{k: getattr(c, k) for k in c.__table__.columns.keys()} for c in clients]

    def get_client_by_id(client_id: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as s:
            c = s.query(Client).filter(Client.client_id == client_id).first()
            if not c:
                return None
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

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

    def update_client(client_id: str, data: Dict[str, Any]) -> bool:
        with SessionLocal() as s:
            c = s.query(Client).filter(Client.client_id == client_id).first()
            if c:
                for k, v in data.items():
                    if hasattr(c, k):
                        setattr(c, k, v)
                s.commit()
                return True
            return False

    def update_client_password(client_id: str, new_hash: str) -> None:
        with SessionLocal() as s:
            c = s.query(Client).filter(Client.client_id == client_id).first()
            if c:
                c.password = new_hash
                s.commit()

    def delete_client(client_id: str) -> bool:
        with SessionLocal() as s:
            c = s.query(Client).filter(Client.client_id == client_id).first()
            if c:
                s.delete(c)
                s.commit()
                return True
            return False

    # Settings
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

    # Services
    def get_all_services() -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            services = s.query(Service).all()
            return [{k: getattr(c, k) for k in c.__table__.columns.keys()} for c in services]

    def get_service_by_id(service_id: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as s:
            c = s.query(Service).filter(Service.service_id == service_id).first()
            if not c:
                return None
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def create_service(data: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as s:
            c = Service(**data)
            s.add(c)
            s.commit()
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def update_service(service_id: str, data: Dict[str, Any]) -> bool:
        with SessionLocal() as s:
            c = s.query(Service).filter(Service.service_id == service_id).first()
            if c:
                for k, v in data.items():
                    if hasattr(c, k):
                        setattr(c, k, v)
                s.commit()
                return True
            return False

    def delete_service(service_id: str) -> bool:
        with SessionLocal() as s:
            c = s.query(Service).filter(Service.service_id == service_id).first()
            if c:
                s.delete(c)
                s.commit()
                return True
            return False

    # Works
    def get_all_work() -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            works = s.query(Work).all()
            return [{k: getattr(c, k) for k in c.__table__.columns.keys()} for c in works]

    def get_work_by_serial(serial: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as s:
            c = s.query(Work).filter(Work.serial == serial).first()
            if not c:
                return None
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def create_work(data: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as s:
            c = Work(**data)
            s.add(c)
            s.commit()
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def update_work(serial: str, data: Dict[str, Any]) -> bool:
        with SessionLocal() as s:
            c = s.query(Work).filter(Work.serial == serial).first()
            if c:
                for k, v in data.items():
                    if hasattr(c, k):
                        setattr(c, k, v)
                s.commit()
                return True
            return False

    def delete_work(serial: str) -> bool:
        with SessionLocal() as s:
            c = s.query(Work).filter(Work.serial == serial).first()
            if c:
                s.delete(c)
                s.commit()
                return True
            return False

    # Payments
    def get_all_payments() -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            payments = s.query(Payment).all()
            return [{k: getattr(c, k) for k in c.__table__.columns.keys()} for c in payments]

    def get_payment_by_id(payment_id: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as s:
            c = s.query(Payment).filter(Payment.payment_id == payment_id).first()
            if not c:
                return None
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def create_payment(data: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as s:
            c = Payment(**data)
            s.add(c)
            s.commit()
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def update_payment(payment_id: str, data: Dict[str, Any]) -> bool:
        with SessionLocal() as s:
            c = s.query(Payment).filter(Payment.payment_id == payment_id).first()
            if c:
                for k, v in data.items():
                    if hasattr(c, k):
                        setattr(c, k, v)
                s.commit()
                return True
            return False

    def delete_payment(payment_id: str) -> bool:
        with SessionLocal() as s:
            c = s.query(Payment).filter(Payment.payment_id == payment_id).first()
            if c:
                s.delete(c)
                s.commit()
                return True
            return False

    # Invoices
    def get_all_invoices() -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            invoices = s.query(Invoice).all()
            return [{k: getattr(c, k) for k in c.__table__.columns.keys()} for c in invoices]

    def get_invoice_by_no(invoice_no: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as s:
            c = s.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()
            if not c:
                return None
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def create_invoice(data: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as s:
            c = Invoice(**data)
            s.add(c)
            s.commit()
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def update_invoice(invoice_no: str, data: Dict[str, Any]) -> bool:
        with SessionLocal() as s:
            c = s.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()
            if c:
                for k, v in data.items():
                    if hasattr(c, k):
                        setattr(c, k, v)
                s.commit()
                return True
            return False

    def delete_invoice(invoice_no: str) -> bool:
        with SessionLocal() as s:
            c = s.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()
            if c:
                s.delete(c)
                s.commit()
                return True
            return False

    # Reports
    def get_all_reports() -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            reports = s.query(Report).all()
            return [{k: getattr(c, k) for k in c.__table__.columns.keys()} for c in reports]

    def create_report(data: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as s:
            c = Report(**data)
            s.add(c)
            s.commit()
            return {k: getattr(c, k) for k in c.__table__.columns.keys()}

    def delete_report(report_id: str) -> bool:
        with SessionLocal() as s:
            c = s.query(Report).filter(Report.report_id == report_id).first()
            if c:
                s.delete(c)
                s.commit()
                return True
            return False

else:
    # DB disabled fallbacks
    def init_db():
        return None

    def is_enabled() -> bool:
        return False

    def get_all_clients() -> list: return []
    def get_client_by_id(client_id: str): return None
    def get_client_by_name(name: str): return None
    def create_client(data: dict): raise RuntimeError("DB not enabled")
    def update_client(client_id: str, data: dict) -> bool: raise RuntimeError("DB not enabled")
    def update_client_password(client_id: str, new_hash: str) -> None: raise RuntimeError("DB not enabled")
    def delete_client(client_id: str) -> bool: raise RuntimeError("DB not enabled")

    def get_setting(key: str, default: str = "") -> str: return default
    def set_setting(key: str, value: str) -> None: raise RuntimeError("DB not enabled")

    def get_all_services() -> list: return []
    def get_service_by_id(service_id: str): return None
    def create_service(data: dict): raise RuntimeError("DB not enabled")
    def update_service(service_id: str, data: dict): raise RuntimeError("DB not enabled")
    def delete_service(service_id: str): raise RuntimeError("DB not enabled")

    def get_all_work() -> list: return []
    def get_work_by_serial(serial: str): return None
    def create_work(data: dict): raise RuntimeError("DB not enabled")
    def update_work(serial: str, data: dict): raise RuntimeError("DB not enabled")
    def delete_work(serial: str): raise RuntimeError("DB not enabled")

    def get_all_payments() -> list: return []
    def get_payment_by_id(payment_id: str): return None
    def create_payment(data: dict): raise RuntimeError("DB not enabled")
    def update_payment(payment_id: str, data: dict): raise RuntimeError("DB not enabled")
    def delete_payment(payment_id: str): raise RuntimeError("DB not enabled")

    def get_all_invoices() -> list: return []
    def get_invoice_by_no(invoice_no: str): return None
    def create_invoice(data: dict): raise RuntimeError("DB not enabled")
    def update_invoice(invoice_no: str, data: dict): raise RuntimeError("DB not enabled")
    def delete_invoice(invoice_no: str): raise RuntimeError("DB not enabled")

    def get_all_reports() -> list: return []
    def create_report(data: dict): raise RuntimeError("DB not enabled")
    def delete_report(report_id: str): raise RuntimeError("DB not enabled")
