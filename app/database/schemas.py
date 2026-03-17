from datetime import datetime
from pydantic import BaseModel


class BillData(BaseModel):
    id: int
    file_name: str
    owner_name: str | None = None
    issuer_name: str | None = None
    date: str | None = None
    total_amount: str | None = None
    created_at: datetime


class UploadBillsResponse(BaseModel):
    items: list[BillData]
