from dataclasses import dataclass
from typing import List
import fitz  # PyMuPDF

@dataclass
class Page:
    page_num: int
    text: str

def load_pdf_pages(pdf_path: str) -> List[Page]:
    doc = fitz.open(pdf_path)
    pages: List[Page] = []
    for i in range(len(doc)):
        t = doc[i].get_text("text") or ""
        pages.append(Page(page_num=i + 1, text=t))
    doc.close()
    return pages
