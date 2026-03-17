from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile

from database.db import bill_store
from services.extractor import extract_bill_fields
from database.schemas import BillData, UploadBillsResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    bill_store.init_db()
    yield

app = FastAPI(title="Bill Analyzer API", version="1.0.0", lifespan=lifespan)


@app.post("/bills/upload", response_model=UploadBillsResponse)
async def upload_bills(files: list[UploadFile] = File(...)) -> UploadBillsResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    bills: list[BillData] = []

    for file in files:
        is_pdf = file.filename.lower().endswith(".pdf") if file.filename else False
        if not is_pdf:
            raise HTTPException(status_code=400, detail=f"Only PDF files are supported: {file.filename}")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail=f"Empty file uploaded: {file.filename}")

        extracted = extract_bill_fields(content)
        bill_data = bill_store.save(file.filename or "unknown.pdf", extracted)
        bills.append(bill_data)

    return UploadBillsResponse(items=bills)


@app.get("/bills/{bill_id}", response_model=BillData)
async def get_bill_by_id(bill_id: int) -> BillData:
    bill = bill_store.get(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail=f"Bill not found for id: {bill_id}")
    return bill

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8001)