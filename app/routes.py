from flask import Blueprint, request, jsonify, render_template
from app import database
import logging

logger = logging.getLogger(__name__)

# Create Blueprint.
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    try:
        logger.info("📄 Loading index page")
        items = database.fetch_todo()
        logger.info(f"📊 Fetched {len(items)} tasks for index page")
        return render_template('index.html', items=items)
    except Exception as e:
        logger.error(f"❌ Error in index route: {e}")
        return render_template('index.html', items=[])

@bp.route('/health')
def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        # Test database connection
        tasks = database.fetch_todo()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "task_count": len(tasks)
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
    

@bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        logger.info("📋 GET /tasks endpoint called")
        tasks = database.fetch_todo()
        logger.info(f"✅ Returning {len(tasks)} tasks")
        return jsonify(tasks)
    except Exception as e:
        logger.error(f"❌ Error in GET /tasks: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/tasks', methods=['POST'])
def add_task():
    try:
        data = request.get_json()
        logger.info(f"➕ POST /tasks called with data: {data}")
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        task_id = database.insert_new_task(
            description=data.get('description'),
            status=data.get('status', 'Todo'),
            priority=data.get('priority', 'Medium'),
            due_date=data.get('due_date')
        )
        
        if task_id:
            logger.info(f"✅ Task created with ID: {task_id}")
            return jsonify({"id": task_id}), 201
        else:
            logger.error("❌ Failed to create task")
            return jsonify({"error": "Failed to create task"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error in POST /tasks: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        data = request.get_json()
        logger.info(f"✏️ PUT /tasks/{task_id} called with data: {data}")
        
        success = database.update_task(
            task_id=task_id,
            description=data.get('description'),
            status=data.get('status'),
            priority=data.get('priority'),
            due_date=data.get('due_date')
        )
        
        if success:
            logger.info(f"✅ Task {task_id} updated successfully")
            return jsonify({"message": "Task updated"})
        else:
            logger.error(f"❌ Task {task_id} not found")
            return jsonify({"error": "Task not found"}), 404
            
    except Exception as e:
        logger.error(f"❌ Error in PUT /tasks/{task_id}: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        logger.info(f"🗑️ DELETE /tasks/{task_id} called")
        
        success = database.remove_task_by_id(task_id)
        if success:
            logger.info(f"✅ Task {task_id} deleted successfully")
            return jsonify({"message": "Task deleted"})
        else:
            logger.error(f"❌ Task {task_id} not found")
            return jsonify({"error": "Task not found"}), 404
            
    except Exception as e:
        logger.error(f"❌ Error in DELETE /tasks/{task_id}: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/tasks/reorder', methods=['POST'])
def reorder_tasks():
    try:
        data = request.get_json()
        logger.info(f"🔄 POST /tasks/reorder called with: {data}")
        
        success = database.reorder_tasks(data.get('tasks', []))
        if success:
            logger.info("✅ Tasks reordered successfully")
            return jsonify({"message": "Tasks reordered"})
        else:
            logger.error("❌ Failed to reorder tasks")
            return jsonify({"error": "Failed to reorder tasks"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error in POST /tasks/reorder: {e}")
        return jsonify({"error": str(e)}), 500

# Debug endpoint to test database
@bp.route('/debug/db-test')
def debug_db_test():
    try:
        logger.info("🔍 Testing database operations")
        
        # Test fetch
        tasks = database.fetch_todo()
        
        # Test insert
        test_id = database.insert_new_task(
            description="Debug test task",
            status="Todo",
            priority="Medium"
        )
        
        # Test update
        if test_id:
            database.update_task(test_id, status="Done")
        
        # Test delete
        if test_id:
            database.remove_task_by_id(test_id)
            
        return jsonify({
            "fetch_count": len(tasks),
            "test_insert_id": test_id,
            "tasks": tasks
        })
        
    except Exception as e:
        logger.error(f"❌ Debug test failed: {e}")
        return jsonify({"error": str(e)}), 500