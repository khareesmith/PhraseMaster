# Entry point for running the PhraseMaster Flask application
from app import create_app

# Create the Flask application instance
app = create_app()

# Run the application
if __name__ == "__main__":
   app.run(debug=True)