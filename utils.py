from pypdf import PdfReader

def read_file(file):
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
    else:
        return file.read().decode("utf-8")

def chunk_text(text, size=400):
    return [text[i:i+size] for i in range(0, len(text), size)]