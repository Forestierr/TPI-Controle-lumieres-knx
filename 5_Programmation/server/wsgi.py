"""wsgi.py | Robin Forestier | 2021 / 2022

This file is only used to run the server by Gunicorn.
"""

# This is importing the app from the main.py file.
from main import app

if __name__ == "__main__":
    # Running the app.
    app.run()
