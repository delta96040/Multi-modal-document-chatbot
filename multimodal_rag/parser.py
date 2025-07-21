import fitz  # PyMuPDF
from pathlib import Path
import pandas as pd
import email
from email import policy
import requests
from bs4 import BeautifulSoup

def parse_pdf_comprehensive(pdf_path: str):
    """Extracts text, embedded images, and vector graphics from each page of a PDF."""
    if not Path(pdf_path).is_file():
        raise FileNotFoundError(f"The file {pdf_path} was not found.")
    doc = fitz.open(pdf_path)
    parsed_content = []
    temp_img_dir = Path("temp_images")
    temp_img_dir.mkdir(exist_ok=True)
    for page_num, page in enumerate(doc):
        text = page.get_text()
        visual_paths = []
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_filename = f"page{page_num+1}_img{img_index}.png"
            img_path = temp_img_dir / img_filename
            with open(img_path, "wb") as img_file:
                img_file.write(base_image["image"])
            visual_paths.append(str(img_path))
        drawings = page.get_drawings()
        if drawings:
            total_rect = fitz.Rect()
            for path in drawings:
                total_rect.include_rect(path["rect"])
            if not total_rect.is_empty:
                total_rect += (-10, -10, 10, 10)
                pix = page.get_pixmap(clip=total_rect, dpi=200)
                graphic_filename = f"page{page_num + 1}_graphic.png"
                graphic_path = temp_img_dir / graphic_filename
                pix.save(str(graphic_path))
                visual_paths.append(str(graphic_path))
        parsed_content.append({"page_number": page_num + 1, "text": text, "visuals": visual_paths})
    doc.close()
    return parsed_content

def parse_spreadsheet(file_path: str):
    """Parses a spreadsheet (CSV or Excel) into a text format."""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        text_chunks = [f"Row {index+1}: " + ", ".join(f"'{col}' is '{val}'" for col, val in row.items()) for index, row in df.iterrows()]
        full_text = "\n".join(text_chunks)
        return [{"page_number": 1, "text": full_text, "visuals": []}]
    except Exception as e:
        print(f"Error parsing spreadsheet: {e}")
        return []

def parse_email(file_path: str):
    """Parses an email file (.eml)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            msg = email.message_from_file(f, policy=policy.default)
        subject = msg['subject']
        sender = msg['from']
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(part.get_content_charset(), 'ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode(msg.get_content_charset(), 'ignore')
        full_text = f"This is an email from '{sender}' with the subject '{subject}'. The content is: {body}"
        return [{"page_number": 1, "text": full_text, "visuals": []}]
    except Exception as e:
        print(f"Error parsing email: {e}")
        return []

def parse_website(url: str):
    """
    Parses the text content of a website from a URL, using a realistic User-Agent.
    """
    try:
        # --- THIS IS THE KEY CHANGE ---
        # Using a header that mimics a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        # This will raise an error if the request was not successful (like 403 Forbidden)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        
        # Get text, strip leading/trailing whitespace, and remove blank lines
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        full_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if not full_text:
            print("Warning: Could not extract meaningful text from the URL.")
            return []
            
        return [{"page_number": 1, "text": full_text, "visuals": []}]

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - The website may be blocking requests.")
        return []
    except Exception as e:
        print(f"An error occurred while parsing the website: {e}")
        return []