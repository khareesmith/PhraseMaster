# app.py
# Entry point for running the PhraseMaster Flask application
from app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)