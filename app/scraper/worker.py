import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
from typing import List, Any, Dict, Optional
from app.models.schemas import ScrapingTask, Scholarship, ScrapedLink, ScrapingProgress
from app.core.config import get_settings
from app.scraper.parser import DynamicParser
from app.services.ai import ScholarshipAIProcessor, LinkClassifier
from app.core.logging_config import setup_logging
from playwright.async_api import async_playwright, TimeoutError
import urllib.parse
import json

logger = setup_logging()

class ScholarshipScraper:
    def __init__(self, db: Session):
        self.db = db
        self.parser = DynamicParser()
        self.ai_processor = ScholarshipAIProcessor()
        self.link_classifier = LinkClassifier()
        self.settings = get_settings()
        logger.info("ScholarshipScraper initialized")

    def parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string into datetime object."""
        if not date_str:
            return None
        try:
            formats = [
                '%Y-%m-%d',
                '%d-%m-%Y',
                '%m/%d/%Y',
                '%Y/%m/%d',
                '%b %d, %Y',
                '%B %d, %Y',
                '%Y-%m-%dT%H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {str(e)}")
            return None

    def prepare_scholarship_data(self, data: Dict[str, Any], task_id: int, source_url: str) -> Dict[str, Any]:
        """Prepare scholarship data with proper type conversions."""
        try:
            # Handle deadline
            deadline_date = None
            if isinstance(data.get('deadline_info'), dict):
                deadline_date = self.parse_date(data['deadline_info'].get('date'))
            elif isinstance(data.get('deadline'), str):
                deadline_date = self.parse_date(data['deadline'])

            # Ensure AI summary is a string
            ai_summary = data.get('ai_summary')
            if isinstance(ai_summary, dict):
                ai_summary = json.dumps(ai_summary)
            elif ai_summary is None:
                ai_summary = '{}'

            # Prepare normalized data
            return {
                'task_id': task_id,
                'title': str(data.get('title', 'Unknown')),
                'amount': str(data.get('amount_normalized', {}).get('display_amount', 'Unknown')),
                'deadline': deadline_date,
                'field_of_study': str(data.get('field_of_study', 'Not specified')),
                'level_of_study': str(data.get('level_of_study', 'Not specified')),
                'eligibility_criteria': str(data.get('eligibility_requirements', 'Contact institution')),
                'application_url': str(data.get('url', source_url)),
                'location_of_study': str(data.get('location_of_study', 'Not specified')),
                'source_url': str(source_url),
                'ai_summary': ai_summary,
                'confidence_score': float(data.get('confidence_score', 0.0)),
                'last_updated': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Error preparing scholarship data: {str(e)}")
            return None

    async def save_scholarship(self, data: Dict[str, Any], task_id: int, source_url: str):
        """Save a single scholarship with progress tracking."""
        try:
            # Prepare data with proper type conversions
            prepared_data = self.prepare_scholarship_data(data, task_id, source_url)
            if not prepared_data:
                return None

            # Create scholarship object
            scholarship = Scholarship(**prepared_data)
            
            try:
                self.db.add(scholarship)
                self.db.flush()  # Check for errors before committing
                
                # Update progress
                progress = self.db.query(ScrapingProgress).filter_by(task_id=task_id).first()
                if progress:
                    progress.scholarships_found += 1
                
                self.db.commit()
                logger.info(f"Saved scholarship: {scholarship.title}")
                return scholarship
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Database error saving scholarship: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error in save_scholarship: {str(e)}")
            self.db.rollback()
            return None

    async def scrape_url(self, task: ScrapingTask, retry_count: int = 0):
        logger.info(f"Starting to scrape URL: {task.url}")
        
        # Create or update progress tracking
        try:
            existing_progress = self.db.query(ScrapingProgress)\
                .filter_by(task_id=task.id)\
                .first()
            
            if existing_progress:
                progress = existing_progress
                progress.status = "in_progress"
                progress.processed_links = 0
                progress.start_time = datetime.utcnow()
            else:
                progress = ScrapingProgress(
                    task_id=task.id,
                    status="in_progress",
                    total_links=0,
                    processed_links=0,
                    scholarships_found=0,
                    start_time=datetime.utcnow()
                )
                self.db.add(progress)
            
            self.db.commit()

        except Exception as e:
            logger.error(f"Error creating progress record: {str(e)}")
            return

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                try:
                    await page.goto(task.url, wait_until="networkidle", timeout=60000)
                except TimeoutError as e:
                    if retry_count < 3:
                        logger.warning(f"Timeout error occurred while scraping {task.url}. Retrying...")
                        await browser.close()
                        await asyncio.sleep(5)
                        return await self.scrape_url(task, retry_count + 1)
                    else:
                        raise e

                # Extract links
                links = await page.evaluate("""() => {
                    const links = Array.from(document.querySelectorAll('a'));
                    return links.map(link => ({
                        text: link.textContent.trim(),
                        url: link.href
                    }));
                }""")
                
                # Update progress with total links
                progress.total_links = len(links)
                self.db.commit()
                
                for link in links:
                    try:
                        link_text = link['text']
                        link_url = link['url']
                        
                        if link_text and link_url:
                            full_url = urllib.parse.urljoin(task.url, link_url)
                            classification = await self.link_classifier.classify(link_text, full_url)
                            
                            scraped_link = ScrapedLink(
                                task_id=task.id,
                                text=link_text,
                                url=full_url,
                                classification=classification,
                                found_at=datetime.utcnow()
                            )
                            self.db.add(scraped_link)
                            self.db.commit()
                            
                            if classification == 'scholarship':
                                await page.goto(full_url, wait_until="networkidle", timeout=60000)
                                link_html = await page.content()
                                raw_data = await self.parser.parse(link_html, full_url)
                                text_blocks = raw_data.get('text_blocks', [])
                                
                                # Process and save scholarships in real-time
                                processed_scholarships = await self.ai_processor.process_scholarship_chunk(text_blocks)
                                for processed_data in processed_scholarships:
                                    if processed_data:
                                        await self.save_scholarship(processed_data, task.id, full_url)
                            
                            # Update progress
                            progress.processed_links += 1
                            self.db.commit()
                            
                    except Exception as e:
                        logger.warning(f"Error processing link: {str(e)}")
                        continue

                # Process main page content
                html = await page.content()
                await browser.close()
                
                raw_data = await self.parser.parse(html, task.url)
                text_blocks = raw_data.get('text_blocks', [])
                
                chunk_size = self.settings.AI_CHUNK_SIZE
                for i in range(0, len(text_blocks), chunk_size):
                    chunk = text_blocks[i:i+chunk_size]
                    processed_chunk = await self.ai_processor.process_scholarship_chunk(chunk)
                    
                    for processed_data in processed_chunk:
                        if processed_data:
                            await self.save_scholarship(processed_data, task.id, task.url)
                
                # Update task and progress status
                progress.status = "completed"
                progress.end_time = datetime.utcnow()
                task.status = "completed"
                task.last_run = datetime.utcnow()
                task.next_run = datetime.utcnow() + timedelta(hours=24)
                task.success_count += 1
                self.db.commit()
                
                logger.info(f"Successfully processed task: {task.url}")
                
        except Exception as e:
            logger.error(f"Error scraping {task.url}: {str(e)}", exc_info=True)
            progress.status = "failed"
            progress.error_message = str(e)
            task.status = "failed"
            task.error_message = str(e)
            task.fail_count += 1
            self.db.commit()

    async def run_worker(self):
        logger.info("Worker started")
        while True:
            try:
                tasks = self.db.query(ScrapingTask)\
                    .filter(ScrapingTask.status.in_(["pending", "failed"]))\
                    .filter(
                        (ScrapingTask.next_run <= datetime.utcnow()) | 
                        (ScrapingTask.next_run.is_(None))
                    )\
                    .limit(self.settings.WORKER_BATCH_SIZE)\
                    .all()
                
                if not tasks:
                    logger.debug("No tasks found, waiting...")
                    await asyncio.sleep(60)
                    continue
                
                logger.info(f"Found {len(tasks)} tasks to process")
                await asyncio.gather(*[self.scrape_url(task) for task in tasks])
                
            except Exception as e:
                logger.error(f"Worker error: {str(e)}", exc_info=True)
            await asyncio.sleep(60)