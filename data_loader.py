"""Carregador de dados da Empório da Música.

Lê os arquivos CSV da pasta ``data/`` e extrai o texto do manual de
políticas em PDF (``políticas_da_loja.pdf``).
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any

try:  # pdfplumber é opcional; fallback para pypdf
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover - dependência opcional
    pdfplumber = None  # type: ignore

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover - dependência opcional
    PdfReader = None  # type: ignore

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

CSV_FILES = {
    "categories": "desafio_tecnico_ai_eng - categories.csv",
    "customers": "desafio_tecnico_ai_eng - customers.csv",
    "orders": "desafio_tecnico_ai_eng - orders.csv",
    "order_items": "desafio_tecnico_ai_eng - order_items.csv",
    "products": "desafio_tecnico_ai_eng - products.csv",
    "promotions": "desafio_tecnico_ai_eng - promotions.csv",
}

PDF_FILE = "políticas_da_loja.pdf"


def _read_csv(name: str) -> list[dict[str, str]]:
    """Lê um CSV da pasta ``data/`` usando ``utf-8-sig`` (suporte a BOM)."""
    path = os.path.join(DATA_DIR, name)
    rows: list[dict[str, str]] = []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Remove chaves vazias / BOM residuais
            cleaned = {k: v for k, v in row.items() if k is not None}
            rows.append(cleaned)
    return rows


def load_csv_data() -> dict[str, list[dict[str, str]]]:
    """Carrega todos os CSVs e retorna um dicionário ``{nome: [linhas]}``."""
    data: dict[str, list[dict[str, str]]] = {}
    for key, filename in CSV_FILES.items():
        data[key] = _read_csv(filename)
    return data


def _extract_text_pypdf(path: str) -> str:
    if PdfReader is None:
        return ""
    reader = PdfReader(path)
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
    return "\n".join(parts)


def _extract_text_pdfplumber(path: str) -> str:
    if pdfplumber is None:
        return ""
    parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            parts.append(text)
    return "\n".join(parts)


def load_policies(path: str | None = None) -> str:
    """Extrai todo o texto do manual de políticas em PDF."""
    if path is None:
        path = os.path.join(DATA_DIR, PDF_FILE)
    if not os.path.exists(path):
        return ""
    # Tenta pdfplumber primeiro (melhor extração de tabelas/layout)
    text = _extract_text_pdfplumber(path)
    if not text.strip() and PdfReader is not None:
        text = _extract_text_pypdf(path)
    return text


def load_all() -> dict[str, Any]:
    """Carrega CSVs e políticas. Retorna um dicionário pronto para o KB."""
    return {
        "csv": load_csv_data(),
        "policies": load_policies(),
    }


if __name__ == "__main__":  # pragma: no cover - smoke test
    all_data = load_all()
    for key, rows in all_data["csv"].items():
        print(f"{key}: {len(rows)} linha(s)")
    print(f"policies: {len(all_data['policies'])} caractere(s)")
