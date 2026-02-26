import os
from flask import Flask, jsonify, send_from_directory
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the correct paths - IMPORTANT: Use absolute paths
base_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(base_dir, "app")
template_dir = os.path.join(app_dir, "templates")
static_dir = os.path.join(app_dir, "static")

logger.info(f"Base directory: {base_dir}")
logger.info(f"App directory: {app_dir}")
logger.info(f"Template directory: {template_dir}")
logger.info(f"Static directory: {static_dir}")

# Create Flask app with explicit static folder configuration
app = Flask(__name__, 
    template_folder=template_dir,
    static_folder=static_dir,
    static_url_path='/static'
)

# Manual static file route as fallback
@app.route('/static/<path:subpath>')
def serve_static(subpath):
    try:
        response = send_from_directory(static_dir, subpath)
        logger.info(f"Served static file: {subpath}")
        return response
    except Exception as e:
        logger.error(f"Error serving static file {subpath}: {e}")
        return f"Static file not found: {subpath}", 404

# Test static files endpoint
@app.route('/debug/static-files')
def debug_static_files():
    static_files = {
        'modal.js': os.path.exists(os.path.join(static_dir, 'script/modal.js')),
        'custom.css': os.path.exists(os.path.join(static_dir, 'styles/custom.css')),
        'static_dir': static_dir,
        'files_found': []
    }
    
    # List all static files
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            static_files['files_found'].append(os.path.join(root, file))
    
    return jsonify(static_files)

# Enhanced health endpoint
@app.route('/health')
def health():
    try:
        from app import database
        tasks = database.fetch_todo()
        
        # Test static files
        modal_exists = os.path.exists(os.path.join(static_dir, 'script/modal.js'))
        css_exists = os.path.exists(os.path.join(static_dir, 'styles/custom.css'))
        
        return jsonify({
            "status": "healthy", 
            "message": "Application is running",
            "database": f"Connected - {len(tasks)} tasks found",
            "static_files": {
                "modal.js": modal_exists,
                "custom.css": css_exists
            },
            "environment": os.getenv("ENV", "Not set")
        })
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "error": str(e)
        }), 500

# Root endpoint
@app.route('/')
def index():
    try:
        from flask import render_template
        from app import database
        
        logger.info("Loading index page")
        items = database.fetch_todo()
        logger.info(f"Fetched {len(items)} tasks from database")
        
        # Log static file URLs for debugging
        logger.info(f"Static URL path: {app.static_url_path}")
        logger.info(f"Static folder: {app.static_folder}")
        
        return render_template('index.html', items=items)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        logger.error(traceback.format_exc())
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Todo App - Error</title></head>
        <body>
            <h1>Todo App - Error</h1>
            <p>Error loading page: {e}</p>
            <p><a href="/health">Health Check</a></p>
            <p><a href="/debug/static-files">Debug Static Files</a></p>
            <p><a href="/tasks">Tasks API</a></p>
        </body>
        </html>
        """

# Initialize database and routes
try:
    from app import database
    database.create_tables()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    
try:
    from app.routes import bp
    app.register_blueprint(bp)
    logger.info("Routes registered successfully")
except Exception as e:
    logger.error(f"Routes registration failed: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
    