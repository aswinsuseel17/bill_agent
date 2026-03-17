import io
import json
import os

import pdfplumber
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


def _extract_text_from_pdf(pdf_content: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def _normalize_llm_data(data: dict) -> dict[str, str | None]:
    owner_name = data.get("owner_name") or data.get("owner")
    issuer_name = data.get("issuer_name") or data.get("issuer")
    bill_date = data.get("date")
    total_amount = data.get("total_amount") or data.get("amount")

    return {
        "owner_name": str(owner_name).strip() if owner_name else None,
        "issuer_name": str(issuer_name).strip() if issuer_name else None,
        "date": str(bill_date).strip() if bill_date else None,
        "total_amount": str(total_amount).strip() if total_amount else None,
    }


def _parse_llm_json(raw_text: str) -> dict[str, str | None]:
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            return _normalize_llm_data(parsed)
    except json.JSONDecodeError:
        return {
            "owner_name": None,
            "issuer_name": None,
            "date": None,
            "total_amount": None,
        }

    return {
        "owner_name": None,
        "issuer_name": None,
        "date": None,
        "total_amount": None,
    }


def _truncate_text_for_llm(text: str, max_chars: int = 18000) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-(max_chars // 2) :]
    return f"{head}\n\n...[TRUNCATED]...\n\n{tail}"


def _extract_with_llm(full_text: str) -> dict[str, str | None]:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_VERSION", "2025-01-01-preview")
    model = os.getenv("AZURE_GPT4O_MODEL")

    if not endpoint or not api_key or not model:
        raise RuntimeError("Azure OpenAI environment variables are missing")

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    prompt_text = _truncate_text_for_llm(full_text)

    completion = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract bill fields. Return JSON only with keys: "
                    "owner_name, issuer_name, date, amount. "
                    "If a value is unavailable, set it to null."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Extract owner name, issuer name, date, and amount from this bill text:\n\n"
                    f"{prompt_text}"
                ),
            },
        ],
    )

    message_content = completion.choices[0].message.content or "{}"
    return _parse_llm_json(message_content)


def extract_bill_fields(pdf_content: bytes) -> dict[str, str | None]:
    full_text = _extract_text_from_pdf(pdf_content)
    return _extract_with_llm(full_text)
