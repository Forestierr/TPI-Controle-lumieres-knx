"""flask_test.py | Robin Forestier | 15.03.2022

This file is used to test the Flask installation.
"""

# Importing the Flask class from the flask module.
from flask import Flask

# This is creating an instance of the Flask class and assigning it to the variable `app`.
app = Flask(__name__)


@app.route('/')
def index():
    """Create the index page.

    :return: The index page.
    :rtype: str
    """

    return f"Hello World"


if __name__ == '__main__':
    # Running the app and create a local server.
    app.run(host='0.0.0.0', port=80, debug=True)
