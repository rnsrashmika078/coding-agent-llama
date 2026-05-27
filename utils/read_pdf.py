from pypdf import PdfReader
import re
pdf_reader = PdfReader("./assets/SRI LANKA.pdf")

page_content = {}


def format(text: str) -> str:

    text = text.replace("\n", "")
    text = text.replace("  " , " ")

    return text.strip()


print(f"pdr_reader: {pdf_reader.pages}")
for idx, pdf_page in enumerate(pdf_reader.pages):
    cleaned = format(pdf_page.extract_text())
    page_content[idx + 1] = cleaned

print(f"page content {page_content}")
