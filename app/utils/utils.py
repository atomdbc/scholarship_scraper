from fastapi import APIRouter, UploadFile
from typing import List
import io
import csv
from urllib.parse import urlparse
import re



async def extract_urls_from_file(file: UploadFile) -> List[str]:
    content = await file.read()
    urls = set()
    
    # Try CSV first
    try:
        csv_content = io.StringIO(content.decode('utf-8'))
        csv_reader = csv.reader(csv_content)
        for row in csv_reader:
            for cell in row:
                # Extract URLs using regex
                found_urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*', cell)
                urls.update(found_urls)
    except:
        # If CSV fails, try as plain text
        text_content = content.decode('utf-8')
        found_urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*', text_content)
        urls.update(found_urls)
    
    return list(urls)

def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False