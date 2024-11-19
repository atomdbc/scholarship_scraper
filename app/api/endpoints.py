from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, validator, Field
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.schemas import ScrapingTask, Scholarship, ScrapedLink, ScrapingProgress
from app.core.logging_config import setup_logging
from sqlalchemy import desc, func, and_, or_
import json
from app.utils.utils import extract_urls_from_file, validate_url

logger = setup_logging()
router = APIRouter()

# --- Pydantic Models ---
class UrlUpload(BaseModel):
    url: HttpUrl

    @validator('url')
    def validate_url(cls, v):
        return str(v)

class BulkUrlUpload(BaseModel):
    urls: List[HttpUrl]

    @validator('urls')
    def validate_urls(cls, urls):
        return [str(url) for url in urls]

class ScholarshipResponse(BaseModel):
    id: int
    title: str
    amount: str
    deadline: Optional[str] = None  # Changed to string type
    field_of_study: str
    level_of_study: str
    eligibility_criteria: str
    application_url: str
    source_url: str
    confidence_score: float
    ai_summary: Optional[Dict] = None
    last_updated: str  # Changed to string type
    task_id: int

    @validator('ai_summary', pre=True)
    def parse_ai_summary(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return None
        return v
    
    @validator('deadline', pre=True)
    def format_deadline(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @validator('last_updated', pre=True)
    def format_last_updated(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @validator('ai_summary', pre=True)
    def parse_ai_summary(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return None
        return v

class TaskProgressResponse(BaseModel):
    task_id: int
    url: str
    status: str
    total_links: int
    processed_links: int
    scholarships_found: int
    progress_percentage: float
    start_time: Optional[str] = None  # Changed to string type
    end_time: Optional[str] = None    # Changed to string type
    error_message: Optional[str] = None
    processing_duration: Optional[str] = None

    @validator('start_time', 'end_time', pre=True)
    def format_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

class DetailedTaskStatusResponse(BaseModel):
    total_tasks: int
    pending: int
    completed: int
    in_progress: int
    failed: int
    total_scholarships: int
    average_confidence_score: float
    last_update: datetime
    tasks_progress: List[TaskProgressResponse]
    processing_rate: float  # scholarships per minute
    success_rate: float  # percentage
    system_uptime: str

class ScholarshipStats(BaseModel):
    total_count: int
    average_confidence: float
    by_field_of_study: Dict[str, int]
    by_level_of_study: Dict[str, int]
    recent_additions: List[ScholarshipResponse]
    daily_counts: Dict[str, int]  # Last 7 days
    amount_ranges: Dict[str, int]
    deadline_distribution: Dict[str, int]

class FilterParams(BaseModel):
    field_of_study: Optional[str] = None
    level_of_study: Optional[str] = None
    min_confidence: float = Field(0.0, ge=0.0, le=1.0)
    deadline_after: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    source_url: Optional[str] = None

# --- Helper Functions ---
def calculate_processing_rate(db: Session) -> float:
    """Calculate average scholarships processed per minute."""
    try:
        completed_progress = db.query(ScrapingProgress)\
            .filter(ScrapingProgress.status == "completed")\
            .all()
        
        if not completed_progress:
            return 0.0
        
        total_duration = 0
        total_scholarships = 0
        
        for progress in completed_progress:
            if progress.start_time and progress.end_time:
                duration = (progress.end_time - progress.start_time).total_seconds() / 60
                total_duration += duration
                total_scholarships += progress.scholarships_found
        
        return total_scholarships / total_duration if total_duration > 0 else 0.0
    except Exception:
        return 0.0

# --- Endpoints ---
@router.get("/status", response_model=DetailedTaskStatusResponse)
async def get_status(db: Session = Depends(get_db)):
    """Get detailed status of all scraping tasks including progress."""
    try:
        tasks = db.query(ScrapingTask).all()
        progress_records = db.query(ScrapingProgress).all()
        
        scholarship_stats = db.query(
            func.count(Scholarship.id).label('count'),
            func.avg(Scholarship.confidence_score).label('avg_confidence')
        ).first()

        # Calculate success rate
        total_completed = sum(1 for task in tasks if task.status == "completed")
        total_attempts = sum(task.success_count + task.fail_count for task in tasks)
        success_rate = (total_completed / total_attempts * 100) if total_attempts > 0 else 0

        tasks_progress = []
        for task in tasks:
            progress = next((p for p in progress_records if p.task_id == task.id), None)
            
            if progress:
                processing_duration = None
                if progress.start_time:
                    end = progress.end_time or datetime.utcnow()
                    duration = end - progress.start_time
                    processing_duration = str(duration)

                progress_percentage = 0
                if progress.total_links > 0:
                    progress_percentage = (progress.processed_links / progress.total_links) * 100

                tasks_progress.append(TaskProgressResponse(
                    task_id=task.id,
                    url=task.url,
                    status=task.status,
                    total_links=progress.total_links,
                    processed_links=progress.processed_links,
                    scholarships_found=progress.scholarships_found,
                    progress_percentage=progress_percentage,
                    start_time=progress.start_time,
                    end_time=progress.end_time,
                    error_message=progress.error_message,
                    processing_duration=processing_duration,
                    success_count=task.success_count,
                    fail_count=task.fail_count,
                    created_at=task.created_at,
                    last_run=task.last_run,
                    next_run=task.next_run
                ))

        processing_rate = calculate_processing_rate(db)

        return DetailedTaskStatusResponse(
            total_tasks=len(tasks),
            pending=sum(1 for task in tasks if task.status == "pending"),
            completed=sum(1 for task in tasks if task.status == "completed"),
            in_progress=sum(1 for task in tasks if task.status == "in_progress"),
            failed=sum(1 for task in tasks if task.status == "failed"),
            total_scholarships=scholarship_stats.count,
            average_confidence_score=float(scholarship_stats.avg_confidence or 0),
            last_update=datetime.utcnow(),
            tasks_progress=tasks_progress,
            processing_rate=processing_rate,
            success_rate=success_rate,
            system_uptime=str(datetime.utcnow() - min(task.created_at for task in tasks) if tasks else timedelta())
        )
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/scholarships/{scholarship_id}", response_model=ScholarshipResponse)
async def get_scholarship(scholarship_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific scholarship."""
    try:
        scholarship = db.query(Scholarship)\
            .filter(Scholarship.id == scholarship_id)\
            .first()

        if not scholarship:
            raise HTTPException(status_code=404, detail="Scholarship not found")

        return ScholarshipResponse(
            id=scholarship.id,
            title=scholarship.title,
            amount=scholarship.amount,
            deadline=scholarship.deadline.isoformat() if scholarship.deadline else None,
            field_of_study=scholarship.field_of_study,
            level_of_study=scholarship.level_of_study,
            eligibility_criteria=scholarship.eligibility_criteria,
            application_url=scholarship.application_url,
            source_url=scholarship.source_url,
            confidence_score=scholarship.confidence_score,
            ai_summary=scholarship.ai_summary,
            last_updated=scholarship.last_updated.isoformat() if scholarship.last_updated else None,
            task_id=scholarship.task_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scholarship {scholarship_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/scholarships", response_model=List[ScholarshipResponse])
async def get_scholarships(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    filters: FilterParams = Depends(),
    db: Session = Depends(get_db)
):
    """Get scholarships with advanced filtering."""
    try:
        query = db.query(Scholarship)\
            .filter(Scholarship.confidence_score >= filters.min_confidence)

        if filters.field_of_study:
            query = query.filter(Scholarship.field_of_study.ilike(f"%{filters.field_of_study}%"))
        if filters.level_of_study:
            query = query.filter(Scholarship.level_of_study == filters.level_of_study)
        if filters.deadline_after:
            query = query.filter(Scholarship.deadline >= filters.deadline_after)
        if filters.source_url:
            query = query.filter(Scholarship.source_url.ilike(f"%{filters.source_url}%"))

        scholarships = query.order_by(desc(Scholarship.last_updated))\
            .offset(skip)\
            .limit(limit)\
            .all()

        # Convert datetime objects to strings before returning
        return [
            ScholarshipResponse(
                id=s.id,
                title=s.title,
                amount=s.amount,
                deadline=s.deadline.isoformat() if s.deadline else None,
                field_of_study=s.field_of_study,
                level_of_study=s.level_of_study,
                eligibility_criteria=s.eligibility_criteria,
                application_url=s.application_url,
                source_url=s.source_url,
                confidence_score=s.confidence_score,
                ai_summary=s.ai_summary,
                last_updated=s.last_updated.isoformat() if s.last_updated else None,
                task_id=s.task_id
            ) 
            for s in scholarships
        ]

    except Exception as e:
        logger.error(f"Error getting scholarships: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/scholarships/stats", response_model=ScholarshipStats)
async def get_scholarship_stats(db: Session = Depends(get_db)):
    """Get comprehensive scholarship statistics."""
    try:
        # Basic stats
        stats = db.query(
            func.count(Scholarship.id).label('count'),
            func.avg(Scholarship.confidence_score).label('avg_confidence')
        ).first()

        # Field distribution
        field_distribution = dict(
            db.query(
                Scholarship.field_of_study,
                func.count(Scholarship.id)
            ).group_by(Scholarship.field_of_study).all()
        )

        # Level distribution
        level_distribution = dict(
            db.query(
                Scholarship.level_of_study,
                func.count(Scholarship.id)
            ).group_by(Scholarship.level_of_study).all()
        )

        # Daily counts for last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_counts = dict(
            db.query(
                func.date(Scholarship.last_updated),
                func.count(Scholarship.id)
            ).filter(Scholarship.last_updated >= seven_days_ago)
            .group_by(func.date(Scholarship.last_updated))
            .all()
        )

        # Recent additions
        recent = db.query(Scholarship)\
            .order_by(desc(Scholarship.last_updated))\
            .limit(5)\
            .all()

        return ScholarshipStats(
            total_count=stats.count,
            average_confidence=float(stats.avg_confidence or 0),
            by_field_of_study=field_distribution,
            by_level_of_study=level_distribution,
            recent_additions=recent,
            daily_counts={str(k): v for k, v in daily_counts.items()},
            amount_ranges={},  # Implement amount range distribution
            deadline_distribution={}  # Implement deadline distribution
        )
    except Exception as e:
        logger.error(f"Error getting scholarship stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tasks/{task_id}/progress", response_model=TaskProgressResponse)
async def get_task_progress(task_id: int, db: Session = Depends(get_db)):
    """Get detailed progress information for a specific task."""
    try:
        task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        progress = db.query(ScrapingProgress).filter(ScrapingProgress.task_id == task_id).first()
        if not progress:
            raise HTTPException(status_code=404, detail="Progress data not found")

        processing_duration = None
        if progress.start_time:
            end = progress.end_time or datetime.utcnow()
            duration = end - progress.start_time
            processing_duration = str(duration)

        progress_percentage = 0
        if progress.total_links > 0:
            progress_percentage = (progress.processed_links / progress.total_links) * 100

        return TaskProgressResponse(
            task_id=task.id,
            url=task.url,
            status=task.status,
            total_links=progress.total_links,
            processed_links=progress.processed_links,
            scholarships_found=progress.scholarships_found,
            progress_percentage=progress_percentage,
            start_time=progress.start_time,
            end_time=progress.end_time,
            error_message=progress.error_message,
            processing_duration=processing_duration,
            success_count=task.success_count,
            fail_count=task.fail_count,
            created_at=task.created_at,
            last_run=task.last_run,
            next_run=task.next_run
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/tasks")
async def add_task(data: UrlUpload, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Add a single URL for scraping."""
    try:
        existing_task = db.query(ScrapingTask)\
            .filter(ScrapingTask.url == data.url)\
            .first()

        if existing_task:
            if existing_task.status == "failed":
                existing_task.status = "pending"
                existing_task.error_message = None
                existing_task.next_run = datetime.utcnow()
                existing_task.fail_count = 0
                db.commit()
                return {"message": "Task reset for retry", "url": data.url}
            return {"message": "Task already exists", "url": data.url}

        task = ScrapingTask(
            url=data.url,
            status="pending",
            created_at=datetime.utcnow(),
            next_run=datetime.utcnow(),
            success_count=0,
            fail_count=0
        )
        db.add(task)
        db.commit()

        # Initialize progress tracking
        progress = ScrapingProgress(
            task_id=task.id,
            status="pending",
            total_links=0,
            processed_links=0,
            scholarships_found=0
        )
        db.add(progress)
        db.commit()

        return {
            "message": "Task added successfully",
            "url": data.url,
            "task_id": task.id
        }

    except Exception as e:
        logger.error(f"Error adding task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tasks/bulk")
async def create_scraping_tasks(
    data: BulkUrlUpload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Add multiple URLs for scraping with duplicate handling."""
    try:
        results = {
            "added": 0,
            "skipped": 0,
            "reset": 0,
            "total": len(data.urls),
            "tasks": []
        }

        for url in data.urls:
            existing_task = db.query(ScrapingTask)\
                .filter(ScrapingTask.url == url)\
                .first()

            if existing_task:
                if existing_task.status == "failed":
                    existing_task.status = "pending"
                    existing_task.error_message = None
                    existing_task.next_run = datetime.utcnow()
                    existing_task.fail_count = 0
                    results["reset"] += 1
                    results["tasks"].append({
                        "url": url,
                        "status": "reset",
                        "task_id": existing_task.id
                    })
                else:
                    results["skipped"] += 1
                    results["tasks"].append({
                        "url": url,
                        "status": "skipped",
                        "task_id": existing_task.id
                    })
                continue

            task = ScrapingTask(
                url=url,
                status="pending",
                created_at=datetime.utcnow(),
                next_run=datetime.utcnow(),
                success_count=0,
                fail_count=0
            )
            db.add(task)
            db.flush()  # Get the task ID without committing

            # Initialize progress tracking
            progress = ScrapingProgress(
                task_id=task.id,
                status="pending",
                total_links=0,
                processed_links=0,
                scholarships_found=0
            )
            db.add(progress)
            
            results["added"] += 1
            results["tasks"].append({
                "url": url,
                "status": "added",
                "task_id": task.id
            })

        db.commit()
        return results

    except Exception as e:
        logger.error(f"Error adding bulk tasks: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a specific scraping task and its related data."""
    try:
        task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Delete related records
        db.query(ScrapingProgress).filter(ScrapingProgress.task_id == task_id).delete()
        db.query(ScrapedLink).filter(ScrapedLink.task_id == task_id).delete()
        db.query(Scholarship).filter(Scholarship.task_id == task_id).delete()
        db.delete(task)
        db.commit()

        return {
            "message": "Task and related data deleted successfully",
            "task_id": task_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/delete_all")
async def delete_all_records(db: Session = Depends(get_db)):
    """Delete all records in the database, including tasks and related data."""
    try:
        # Delete in order to respect foreign key constraints
        db.query(ScrapingProgress).delete()
        db.query(ScrapedLink).delete()
        db.query(Scholarship).delete()
        db.query(ScrapingTask).delete()
        
        db.commit()
        return {
            "message": "All records deleted successfully",
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error deleting all records: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/tasks/{task_id}/retry")
async def retry_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry a failed task."""
    try:
        task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status not in ["failed", "completed"]:
            raise HTTPException(status_code=400, detail="Task must be failed or completed to retry")

        # Reset task status
        task.status = "pending"
        task.error_message = None
        task.next_run = datetime.utcnow()
        
        # Create new progress record
        progress = ScrapingProgress(
            task_id=task.id,
            status="pending",
            total_links=0,
            processed_links=0,
            scholarships_found=0
        )
        db.add(progress)
        db.commit()

        return {
            "message": "Task scheduled for retry",
            "task_id": task_id,
            "status": "pending",
            "next_run": task.next_run
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tasks/failed", response_model=List[TaskProgressResponse])
async def get_failed_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get list of failed tasks with their error messages."""
    try:
        tasks = db.query(ScrapingTask)\
            .filter(ScrapingTask.status == "failed")\
            .order_by(desc(ScrapingTask.last_run))\
            .offset(skip)\
            .limit(limit)\
            .all()

        failed_tasks = []
        for task in tasks:
            progress = db.query(ScrapingProgress)\
                .filter(ScrapingProgress.task_id == task.id)\
                .first()

            if progress:
                processing_duration = None
                if progress.start_time and progress.end_time:
                    duration = progress.end_time - progress.start_time
                    processing_duration = str(duration)

                failed_tasks.append(TaskProgressResponse(
                    task_id=task.id,
                    url=task.url,
                    status=task.status,
                    total_links=progress.total_links,
                    processed_links=progress.processed_links,
                    scholarships_found=progress.scholarships_found,
                    progress_percentage=(progress.processed_links / progress.total_links * 100) if progress.total_links > 0 else 0,
                    start_time=progress.start_time,
                    end_time=progress.end_time,
                    error_message=task.error_message,
                    processing_duration=processing_duration,
                    success_count=task.success_count,
                    fail_count=task.fail_count,
                    created_at=task.created_at,
                    last_run=task.last_run,
                    next_run=task.next_run
                ))

        return failed_tasks

    except Exception as e:
        logger.error(f"Error getting failed tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tasks/search")
async def search_tasks(
    query: str = Query(..., min_length=3),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Search tasks by URL and optionally filter by status."""
    try:
        task_query = db.query(ScrapingTask)\
            .filter(ScrapingTask.url.ilike(f"%{query}%"))

        if status:
            task_query = task_query.filter(ScrapingTask.status == status)

        tasks = task_query.all()
        
        return {
            "query": query,
            "status_filter": status,
            "count": len(tasks),
            "results": tasks
        }

    except Exception as e:
        logger.error(f"Error searching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

@router.post("/tasks/upload-urls")
async def upload_url_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload a file containing URLs for scraping.
    Accepts .txt or .csv files.
    """
    if not file.filename.endswith(('.txt', '.csv')):
        raise HTTPException(status_code=400, detail="Only .txt or .csv files are allowed")

    try:
        urls = await extract_urls_from_file(file)
        if not urls:
            raise HTTPException(status_code=400, detail="No valid URLs found in file")

        valid_urls = [url for url in urls if validate_url(url)]
        if not valid_urls:
            raise HTTPException(status_code=400, detail="No valid URLs found in file")

        # Use existing bulk upload logic
        bulk_upload = BulkUrlUpload(urls=valid_urls)
        response = await create_scraping_tasks(bulk_upload, background_tasks, db)

        return {
            "message": "File processed successfully",
            "total_urls_found": len(urls),
            "valid_urls": len(valid_urls),
            "tasks_created": response["added"],
            "tasks_skipped": response["skipped"],
            "tasks": response["tasks"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    

@router.get("/scholarships/export", response_model=List[ScholarshipResponse])
async def export_scholarships(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Export scholarships between dates."""
    try:
        query = db.query(Scholarship)
        
        if start_date:
            query = query.filter(Scholarship.created_at >= start_date)
        if end_date:
            query = query.filter(Scholarship.created_at <= end_date)
            
        scholarships = query.order_by(desc(Scholarship.created_at)).all()
        return scholarships
    except Exception as e:
        logger.error(f"Error exporting scholarships: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/scholarships/export/csv")
async def export_scholarships_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Export scholarships as CSV."""
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    try:
        scholarships = await export_scholarships(start_date, end_date, db)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            "Title", "Amount", "Deadline", "Field of Study", 
            "Level of Study", "Eligibility Criteria", "Application URL",
            "Source URL", "Confidence Score", "Last Updated"
        ])
        
        # Write data
        for scholarship in scholarships:
            writer.writerow([
                scholarship.title,
                scholarship.amount,
                scholarship.deadline.isoformat() if scholarship.deadline else "",
                scholarship.field_of_study,
                scholarship.level_of_study,
                scholarship.eligibility_criteria,
                scholarship.application_url,
                scholarship.source_url,
                scholarship.confidence_score,
                scholarship.last_updated.isoformat()
            ])
            
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=scholarships_export.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting scholarships to CSV: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")