import os
import traceback  # ADD THIS IMPORT
from datetime import date, datetime  # ADD datetime import
from sqlalchemy import create_engine, Column, Integer, String, Enum, Date
from sqlalchemy.orm import declarative_base, sessionmaker
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration - deferred until needed
db_url = None
engine = None
SessionLocal = None
Base = declarative_base()

def init_db():
    """Initialize database connection when needed"""
    global db_url, engine, SessionLocal
    
    if db_url is not None:
        return  # Already initialized
    
    try:
        # Dynamically choose which secrets module to use (LOCAL or AWS)
        if os.getenv("ENV") == "AWS":
            from app.secrets import get_secret  # fetches from AWS Secrets Manager
        else:
            from app.secrets_local import get_secret  # local testing

        # Load database credentials
        secret = get_secret()
        db_url = f"mysql+pymysql://{secret['username']}:{secret['password']}@{secret['host']}:3306/{secret['dbname']}"
        
        # Create engine and session factory
        engine = create_engine(db_url, echo=True)
        SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Create a dummy engine to prevent crashes during import
        db_url = "sqlite:///:memory:"
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# ==========================
# Define Task model
# ==========================
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)
    status = Column(Enum("Todo", "In Progress", "Done"), default="Todo", nullable=False)
    priority = Column(Enum("Low", "Medium", "High"), default="Medium", nullable=False)
    due_date = Column(Date, nullable=True)
    position = Column(Integer, nullable=True)  # For drag-and-drop ordering.

def create_tables():
    """Create tables if they don't exist"""
    try:
        init_db()  # Ensure DB is initialized.
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")

# ===========================
# Database helper functions
# ===========================
def get_session():
    """Get a database session, initializing DB if needed"""
    init_db()
    return SessionLocal()

def parse_date(date_string):
    """Safely parse date string to date object"""
    if not date_string:
        return None
    try:
        if isinstance(date_string, date):
            return date_string
        if isinstance(date_string, datetime):
            return date_string.date()
        # Parse string date
        return datetime.strptime(str(date_string), '%Y-%m-%d').date()
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse date '{date_string}': {e}")
        return None

def fetch_todo(order_by_position=True, filter_status=None):
    """Fetch all tasks, optionally filtering by status."""
    try:
        logger.info("fetch_todo called")
        with get_session() as session:
            query = session.query(Task)
            if filter_status:
                query = query.filter(Task.status == filter_status)
            if order_by_position:
                query = query.order_by(Task.position)
            else:
                query = query.order_by(Task.id)
            
            tasks = query.all()
            logger.info(f"DEBUG: Found {len(tasks)} tasks in database")
            
            result = []
            for task in tasks:
                task_data = {
                    "id": task.id,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": None,
                    "position": task.position,
                }
                
                # Handle due_date safely
                if task.due_date:
                    if hasattr(task.due_date, 'isoformat'):
                        # It's a date object
                        task_data["due_date"] = task.due_date.isoformat()
                    else:
                        # It's already a string or other type
                        task_data["due_date"] = str(task.due_date)
                        logger.warning(f"Task {task.id} has string due_date: {task.due_date}")
                
                result.append(task_data)
            
            return result
            
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        logger.error(traceback.format_exc())
        return []

def insert_new_task(description, status="Todo", priority="Medium", due_date=None, position=None):
    """Insert a new task."""
    try:
        with get_session() as session:
            if position is None:
                max_pos = session.query(Task.position).order_by(Task.position.desc()).first()
                position = (max_pos[0] or 0) + 1 if max_pos else 1
            
            # Parse due_date to ensure it's a proper date object
            parsed_due_date = parse_date(due_date)
            
            task = Task(
                description=description,
                status=status,
                priority=priority,
                due_date=parsed_due_date,
                position=position
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            logger.info(f"Inserted task with ID: {task.id}")
            return task.id
    except Exception as e:
        logger.error(f"Error inserting task: {e}")
        return None

def update_task(task_id, description=None, status=None, priority=None, due_date=None, position=None):
    """Update a task."""
    try:
        with get_session() as session:
            task = session.get(Task, task_id)
            if not task:
                logger.error(f"Task {task_id} not found for update")
                return False
            if description is not None:
                task.description = description
            if status is not None:
                task.status = status
            if priority is not None:
                task.priority = priority
            if due_date is not None:
                # Parse due_date to ensure it's a proper date object
                task.due_date = parse_date(due_date)
            if position is not None:
                task.position = position
            session.commit()
            logger.info(f"Updated task {task_id}")
            return True
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        return False

def remove_task_by_id(task_id):
    """Delete a task."""
    try:
        with get_session() as session:
            task = session.get(Task, task_id)
            if not task:
                logger.error(f"Task {task_id} not found for deletion")
                return False
            session.delete(task)
            session.commit()
            logger.info(f"Deleted task {task_id}")
            return True
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        return False

def reorder_tasks(task_list):
    """Reorder tasks based on a list of dicts [{'id': 1, 'position': 2}, ...]."""
    try:
        with get_session() as session:
            for task_info in task_list:
                task = session.get(Task, task_info["id"])
                if task:
                    task.position = task_info["position"]
            session.commit()
            logger.info(f"Reordered {len(task_list)} tasks")
            return True
    except Exception as e:
        logger.error(f"Error reordering tasks: {e}")
        return False

# Initialize database on module import
init_db()