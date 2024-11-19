# app/scraper/parser.py
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import logging
import re
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class DynamicParser:
    def __init__(self):
        self.text_blocks = []
        self.links = []

    def extract_meaningful_text(self, soup: BeautifulSoup) -> str:
        """Extract meaningful text content from the page"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text and clean it
        text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return '\n'.join(lines)

    def format_scholarship_block(self, title: str, amount: str, deadline: str, description: str, url: str) -> str:
        """Format extracted information into a structured text block"""
        return f"""Title: {title}
Amount: {amount}
Deadline: {deadline}
URL: {url}
Description: {description}"""

    def extract_important_elements(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract potentially important elements from the page"""
        domain = urlparse(url).netloc
        extracted_scholarships = []

        # Find scholarship containers
        scholarship_containers = soup.find_all(['div', 'article', 'section'], class_=lambda x: x and any(
            term in str(x).lower() for term in ['scholarship', 'award', 'grant', 'funding', 'bursary', 'opportunity']
        ))

        # If no specific containers found, try alternative approaches
        if not scholarship_containers:
            scholarship_containers = []
            
            # Look for headers
            headers = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=lambda x: x and any(
                term in str(x).lower() for term in ['scholarship', 'award', 'grant', 'funding', 'bursary']
            ))
            
            # For each header, create a container with following content
            for header in headers:
                container = {'header': header, 'content': []}
                next_elem = header.find_next_sibling()
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4']:
                    container['content'].append(next_elem)
                    next_elem = next_elem.find_next_sibling()
                scholarship_containers.append(container)

        # Process each container
        for container in scholarship_containers:
            try:
                # Extract title
                title = None
                if isinstance(container, dict):
                    title = container['header'].get_text(strip=True)
                    content = ' '.join(elem.get_text(strip=True) for elem in container['content'])
                else:
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                    title = title_elem.get_text(strip=True) if title_elem else None
                    content = container.get_text(strip=True)

                if not title:
                    continue

                # Extract amount
                amount = "Not specified"
                amount_patterns = [
                    r'\$[\d,]+(?:\.\d{2})?',
                    r'(?:award|value|amount).*?\$[\d,]+(?:\.\d{2})?',
                    r'\$[\d,]+(?:\.\d{2})?.*?(?:award|scholarship|grant)'
                ]
                for pattern in amount_patterns:
                    amount_match = re.search(pattern, content, re.IGNORECASE)
                    if amount_match:
                        amount = amount_match.group(0)
                        break

                # Extract deadline
                deadline = "Not specified"
                deadline_patterns = [
                    r'\b(?:deadline|due date|closes|applications close)\b.*?\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
                    r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b.*?\b(?:deadline|due date)\b',
                    r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
                ]
                for pattern in deadline_patterns:
                    deadline_match = re.search(pattern, content, re.IGNORECASE)
                    if deadline_match:
                        deadline = deadline_match.group(0)
                        break

                # Find related URL
                scholarship_url = url
                links = container.find_all('a', href=True) if not isinstance(container, dict) else []
                for link in links:
                    if any(term in link.get_text().lower() for term in ['apply', 'learn more', 'details']):
                        scholarship_url = urljoin(url, link['href'])
                        break

                # Format the scholarship block
                scholarship_block = self.format_scholarship_block(
                    title=title,
                    amount=amount,
                    deadline=deadline,
                    description=content,
                    url=scholarship_url
                )
                extracted_scholarships.append(scholarship_block)

            except Exception as e:
                logger.error(f"Error processing container: {str(e)}")
                continue

        return {
            'domain': domain,
            'url': url,
            'text_blocks': extracted_scholarships,
            'full_text': self.extract_meaningful_text(soup)
        }

    async def parse(self, html: str, url: str) -> Dict[str, Any]:
        """Parse any scholarship page and extract relevant information"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            extracted_data = self.extract_important_elements(soup, url)
            
            logger.info(f"Successfully extracted {len(extracted_data['text_blocks'])} scholarships from {url}")
            return extracted_data

        except Exception as e:
            logger.error(f"Error parsing {url}: {str(e)}")
            return {
                'url': url,
                'error': str(e),
                'text_blocks': []
            }