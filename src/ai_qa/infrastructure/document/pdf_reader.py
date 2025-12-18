from pypdf import PdfReader
from io import BytesIO

def extract_text_from_pdf(file_context: bytes) -> str:
    """从 PDF 文件内容中提取文本
    
    Args:
        file_context: PDF 文件的二进制内容
        
    Returns:
        提取的文本内容
    """
    pdf_file = BytesIO(file_context)
    reader = PdfReader(pdf_file)

    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    
    return "\n\n".join(text_parts)

