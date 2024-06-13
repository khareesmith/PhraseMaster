# Entry point for running the PhraseMaster Flask application
from app import create_app
import os

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    if os.getenv('FLASK_ENV') == 'development':
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000)
    else:
        app.run(host='0.0.0.0', port=5000)