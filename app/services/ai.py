# app/services/ai.py
from openai import AsyncOpenAI
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import re
from app.core.config import get_settings
from pydantic import BaseModel
import asyncio
import logging

logger = logging.getLogger(__name__)

def safe_get_first(lst: List[Any], default: Any = None) -> Any:
    """Safely get first element of a list or return default."""
    try:
        if lst and len(lst) > 0:
            return lst[0]
        return default
    except Exception:
        return default

def safe_get_nested(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary values."""
    try:
        current = data
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key, default)
            if current is None:
                return default
        return current
    except Exception:
        return default

class LinkClassifier:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def classify(self, link_text: str, link_url: str) -> str:
        prompt = f"""Given the following link text and URL, classify the link into one of these categories: scholarship, irrelevant.

Link Text: {link_text}
URL: {link_url}

Return only the category name, either "scholarship" or "irrelevant"."""

        try:
            # Get response from OpenAI
            completion = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a link classification expert. Return only the category name."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1
            )

            # Get the response content
            response_content = completion.choices[0].message.content.strip().lower()
            logger.debug(f"OpenAI raw response: {response_content}")

            # Validate the response
            if response_content in ['scholarship', 'irrelevant']:
                return response_content
            else:
                logger.warning(f"Invalid link classification response: {response_content}")
                return 'irrelevant'

        except Exception as e:
            logger.error(f"Error in OpenAI link classification: {str(e)}")
            return 'irrelevant'

class ScholarshipAIProcessor:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def _parse_amount(self, amount_str: str) -> Dict[str, Any]:
        """Extract structured amount information."""
        default_amount = {
            'type': 'unknown',
            'min_amount': None,
            'max_amount': None,
            'is_renewable': False,
            'duration': None,
            'display_amount': 'Not specified'
        }

        if not amount_str or not isinstance(amount_str, str):
            return default_amount

        try:
            amount_info = default_amount.copy()
            amount_info['display_amount'] = amount_str

            # Look for patterns like "$5,000" or "up to $10,000"
            amount_matches = re.findall(r'\$?\d+(?:,\d{3})*(?:\.\d{2})?', amount_str)
            if amount_matches:
                amounts = [float(re.sub(r'[$,]', '', amt)) for amt in amount_matches]
                if len(amounts) == 1:
                    amount_info['type'] = 'fixed'
                    amount_info['min_amount'] = amounts[0]
                    amount_info['max_amount'] = amounts[0]
                elif len(amounts) >= 2:
                    amount_info['type'] = 'range'
                    amount_info['min_amount'] = min(amounts)
                    amount_info['max_amount'] = max(amounts)

            # Check for renewable scholarships
            if re.search(r'renewable|per year|annual|yearly', amount_str, re.I):
                amount_info['is_renewable'] = True

            return amount_info
        except Exception as e:
            logger.error(f"Error parsing amount '{amount_str}': {str(e)}")
            return default_amount

    async def process_scholarship(self, text_block: str) -> Optional[Dict[str, Any]]:
        """Process a single scholarship text block."""
        try:
            # Extract basic information using regex
            title_match = re.search(r'Title:\s*(.*?)(?:\n|$)', text_block, re.IGNORECASE)
            amount_match = re.search(r'Amount:\s*(.*?)(?:\n|$)', text_block, re.IGNORECASE)
            deadline_match = re.search(r'Deadline:\s*(.*?)(?:\n|$)', text_block, re.IGNORECASE)
            url_match = re.search(r'URL:\s*(.*?)(?:\n|$)', text_block, re.IGNORECASE)
            description_match = re.search(r'Description:\s*(.*?)(?:\n|$)', text_block, re.IGNORECASE | re.DOTALL)

            # Skip if missing essential information
            if not (title_match and description_match):
                logger.warning("Skipping scholarship due to missing essential information")
                return None

            # Structure the data
            structured_data = {
                'title': title_match.group(1).strip(),
                'amount': amount_match.group(1).strip() if amount_match else 'Not specified',
                'deadline': deadline_match.group(1).strip() if deadline_match else None,
                'url': url_match.group(1).strip() if url_match else '',
                'description': description_match.group(1).strip(),
            }

            # Process with GPT-4
            prompt = f"""Analyze this scholarship information and provide a structured JSON response:

    {text_block}

    Return a JSON object with this exact structure:
    {{
        "amount_analysis": {{
            "type": "fixed|range|unknown",
            "value": "string",
            "is_renewable": boolean,
            "conditions": []
        }},
        "eligibility_requirements": [],
        "deadline_info": {{
            "date": "YYYY-MM-DD|null",
            "is_recurring": boolean
        }},
        "field_of_study": "string",
        "level_of_study": "string",
        "confidence_score": number
    }}"""

            completion = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a scholarship analysis expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )

            # Parse AI response
            ai_response = json.loads(completion.choices[0].message.content.strip())
            
            # Normalize amount information
            amount_info = self._parse_amount(ai_response['amount_analysis']['value'])

            # Build final data structure
            final_data = {
                'title': structured_data['title'],
                'amount_normalized': amount_info,
                'amount': structured_data['amount'],
                'deadline_info': ai_response['deadline_info'],
                'field_of_study': ai_response['field_of_study'],
                'level_of_study': ai_response['level_of_study'],
                'eligibility_requirements': '\n'.join(ai_response['eligibility_requirements']),
                'application_url': structured_data['url'],
                'source_url': structured_data['url'],
                'ai_summary': json.dumps(ai_response),
                'confidence_score': float(ai_response['confidence_score']),
                'last_updated': datetime.utcnow()
            }

            # Only return if confidence score is above threshold
            if final_data['confidence_score'] >= 0.6:
                logger.info(f"Successfully processed scholarship: {final_data['title']}")
                return final_data
            else:
                logger.warning(f"Skipping low-confidence scholarship: {final_data['title']}")
                return None

        except Exception as e:
            logger.error(f"Error processing scholarship: {str(e)}")
            return None
    
    async def process_scholarship_chunk(self, chunk: List[str]) -> List[Dict[str, Any]]:
        processed_scholarships = []
        
        for text_block in chunk:
            processed_data = await self.process_scholarship(text_block)
            
            if processed_data:
                processed_scholarships.append(processed_data)
        
        return processed_scholarships

    async def batch_process(self, scholarships: List[Dict[str, Any]], batch_size: int = 5) -> List[Dict[str, Any]]:
        """Process multiple scholarships in batches."""
        results = []
        for i in range(0, len(scholarships), batch_size):
            batch = scholarships[i:i + batch_size]
            try:
                batch_results = await asyncio.gather(
                    *[self.process_scholarship(s) for s in batch],
                    return_exceptions=True
                )
                # Filter out exceptions and log them
                processed_results = []
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch processing error: {str(result)}")
                    else:
                        processed_results.append(result)
                results.extend(processed_results)
            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")
                
        return results