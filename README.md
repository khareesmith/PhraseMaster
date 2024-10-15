# Phrase Craze

Phrase Craze was a web-based game where users can select a category, receive a challenge generated by GPT-4o, and vote on challenges submitted by other users. The game was designed to be fun and engaging while showcasing the capabilities of GPT in generating creative content.

Honestly, this project died out because I wasn't having as much fun with it. Feel free to use this for something!

## Features

- **Daily Challenges**: Users receive a new challenge every day in one of nine categories.
- **Voting System**: Players vote on the best submissions from the previous day.
- **Leaderboard**: A daily leader is crowned based on the votes.

## Installation

To run the PhraseMaster application locally, follow these steps:

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/PhraseMaster.git
    cd PhraseMaster
    ```

2. **Create and activate a virtual environment**:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    Create a `.env` file in the root directory and add the following variables:
    ```env
    FLASK_APP=run.py
    FLASK_ENV=development
    DATABASE_URL= postgresql_database_url
    OPENAI_API_KEY= openai_api_key
    ```

5. **Start the Flask application**:
    ```sh
    flask run
    ```

## File Structure

- `run.py`: The entry point of the application.
- `app/`: Contains the main application code.
  - `__init__.py`: Initializes the Flask app and its configurations.
  - `models.py`: Defines the database models.
  - `routes.py`: Defines the application routes.
  - `templates/`: Contains HTML templates for the web pages.
  - `static/`: Contains static files like CSS, JavaScript, and images.
  - `utils/`: Contains utility files that allow PhraseMaster to work.

- `requirements.txt`: Lists the Python dependencies.
- `.env`: Environment variables file (not included in the repository for security reasons).

## Usage

1. **Select a category**: Choose from one of the four available categories.
2. **Receive a challenge**: GPT-4 generates a unique challenge based on the selected category.
3. **Submit your response**: Complete the challenge and submit your entry.
4. **Vote on submissions**: Vote on other players' submissions from the previous day.
5. **Leaderboard**: Check the leaderboard to see who the daily leader is.

## License

PhraseMaster is licensed under the MIT License. See `LICENSE` for more information.
