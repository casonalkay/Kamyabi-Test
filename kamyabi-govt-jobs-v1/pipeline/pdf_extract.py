from io import BytesIO
from pypdf import PdfReader
from scrapers.base import get, clean_text

def pdf_text(url, session=None):
    r = get(url, session)
    reader = PdfReader(BytesIO(r.content))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return clean_text("\n".join(pages))
