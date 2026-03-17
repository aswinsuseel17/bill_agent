import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from database.models import Base, BillRecord
from database.schemas import BillData

load_dotenv()


class BillStore:
    def __init__(self) -> None:
        db_url = os.getenv("db_url")
        if not db_url:
            raise RuntimeError("Missing required database URL in .env (db_url)")

        self._engine = create_engine(db_url)
        self._session_factory = sessionmaker(bind=self._engine, autoflush=False, autocommit=False)

    def init_db(self) -> None:
        Base.metadata.create_all(self._engine)
        self._ensure_bills_schema()

    def _ensure_bills_schema(self) -> None:
        inspector = inspect(self._engine)
        if "bills" not in inspector.get_table_names():
            return

        existing_columns = {column["name"] for column in inspector.get_columns("bills")}

        ddl_statements: list[str] = []
        if "file_name" not in existing_columns:
            ddl_statements.append(
                "ALTER TABLE bills ADD COLUMN file_name VARCHAR(255) DEFAULT 'unknown.pdf' NOT NULL"
            )
        if "owner_name" not in existing_columns:
            ddl_statements.append("ALTER TABLE bills ADD COLUMN owner_name VARCHAR(255)")
        if "issuer_name" not in existing_columns:
            ddl_statements.append("ALTER TABLE bills ADD COLUMN issuer_name VARCHAR(255)")
        if "date" not in existing_columns:
            ddl_statements.append("ALTER TABLE bills ADD COLUMN date VARCHAR(64)")
        if "total_amount" not in existing_columns:
            ddl_statements.append("ALTER TABLE bills ADD COLUMN total_amount VARCHAR(64)")
        if "created_at" not in existing_columns:
            ddl_statements.append(
                "ALTER TABLE bills ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL"
            )

        if not ddl_statements:
            return

        with self._engine.begin() as connection:
            for statement in ddl_statements:
                connection.execute(text(statement))

    @staticmethod
    def _to_schema(record: BillRecord) -> BillData:
        return BillData(
            id=record.id,
            file_name=record.file_name,
            owner_name=record.owner_name,
            issuer_name=record.issuer_name,
            date=record.date,
            total_amount=record.total_amount,
            created_at=record.created_at,
        )

    def save(self, file_name: str, extracted: dict[str, str | None]) -> BillData:
        with self._session_factory() as session:
            record = BillRecord(
                file_name=file_name,
                owner_name=extracted.get("owner_name"),
                issuer_name=extracted.get("issuer_name"),
                date=extracted.get("date"),
                total_amount=extracted.get("total_amount"),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def get(self, bill_id: int) -> BillData | None:
        with self._session_factory() as session:
            record = session.get(BillRecord, bill_id)
            if not record:
                return None
            return self._to_schema(record)


bill_store = BillStore()