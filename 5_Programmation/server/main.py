"""main.py | Robin Forestier | 2021 / 2022

Goal : Create a user interface to control the light of the ELO's workshop.

Explanation :   I use Flask for create a Web server.
                A shield is plug on the Raspberry Pi (server) with opto-isolator to ABB module with the GPIO.

TPI : For my IPT, I have to create a settings page controlling the time range where the cameras have the right
      to request a modification of the lights.
      I have to create a manual mode, to modify the date and time. I also need to see the status of the cameras and be
      able to change the passwords.

Raspberry Pi pinout usage :
    +---------------------------------+
    | Raspberry Pi 3B+                |  +------------------------+
    |                            +--+ |  | Shield Octo            |
    |                            |  | |  |                        |
    |          GPIO 2  |         |  | |  | X1 / DRV3 |            |
    |          GPIO 3  |         |  | |  | X1 / DRV4 |            |
    |          GPIO 4  |         |  | |  | X2 / DRV1 |            |
    |                  |         |  | |  |           |            |
    |          GPIO 10 |         |  | |  | X3 / DRV3 |            |
    |          GPIO 9  |         |  | |  | X3 / DRV2 |            |
    |          GPIO 11 | GPIO 8  |  | |  | X3 / DRV4 | X3 / DRV1  |
    |                  | GPIO 7  |  | |  |           | X2 / DRV4  |
    |          GPIO 0  | GPIO 1  |  | |  | X1 / DRV1 | X1 / DRV2  |
    |          GPIO 5  |         |  | |  | X2 / DRV2 |            |
    |          GPIO 6  |         |  | |  | X2 / DRV3 |            |
    |                            |  | |  +------------------------+
    |                            |  | |
    |                            +--+ |
    |                                 |
    |                     +-------+   |
    |  +----+   +----+    |       |   |
    |  |    |   |    |    |       |   |
    |  |    |   |    |    |       |   |
    +--+----+---+----+----+-------+---+

GitLab : http://172.16.32.230/Forestier/controle-des-lumieres-knx
         http://172.16.32.230/Forestier/tpi_forestier_gestion_lumiere_knx
XWiki :
    https://xwiki.serverelo.org/xwiki/bin/view/Centre%20de%20Formation%20ELO/Projets/Controle%20des%20lumières%20KNX/
    https://xwiki.serverelo.org/xwiki/bin/view/Centre%20de%20Formation%20ELO/Travaux-diplome/
    TPI_Forestier_Gestion_Lumiere_KNX/Documentation/
"""

# Importing the necessary modules to run the code.
import logging
import os
import pickle
import subprocess
import threading
import time
from datetime import datetime, timedelta
import numpy as np

# Import flask
from flask import Flask, render_template, request, session, url_for, redirect, flash, abort
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

# Creating a class called Table.
from table.table import Table
# Creating a class called Table2 that inherits from Table.
from table.table import Table2

# The above code is importing the RPi.GPIO module and setting it to use the BCM pin numbering scheme.
try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # GPIO 0 to 11 in output mode at 0
    for i in range(12):
        GPIO.setup(i, GPIO.OUT, initial=GPIO.LOW)

    # it's a raspberry pi !
    rpi = True
except ImportError:
    # it's not a raspberry pi !
    rpi = False

# The above code is creating a log file called log.log and setting the format of the log file to the time, the level of
# the log message and the message itself.
logging.basicConfig(filename="log.log", format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# This is creating a new Flask object.
app = Flask(__name__)

# This is the configuration for the application.
app.config.update(
    SECRET_KEY='somesecretkeythatonlyishouldknow',
    SQLALCHEMY_DATABASE_URI="sqlite:///db.sqlite3",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_TYPE='sqlalchemy',
    SESSION_COOKIE_NAME='MyBeautifulCookies',
    SESSION_COOKIE_SAMESITE='Strict',
)

# This is creating a database object that will be used to access the database.
db = SQLAlchemy(app)
# This is telling Flask to use SQLAlchemy as the database.
app.config['SESSION_SQLALCHEMY'] = db
# This is creating a session object that will be used to store and retrieve session data from the user's browser.
sess = Session(app)
db.create_all()

# Ip of the server (for the local user) use to skip authentication.
# Checking if the IP address of the machine that is running the script is in the list of IP addresses that are
# automatically login.
authorize_ip = ["localhost", "127.0.0.1", "172.16.32.133"]

# Value of the buttons and the colors for the map light, each element is a string "off".
buttonSts_p1 = ["off"] * 8
buttonSts_p2 = ["off"] * 8
color = ["#333333"] * 8
# possible warning (like temp alert).
warning = ""


class User:
    """User : create different user for the login"""

    def __init__(self, id, username, password):
        """
        The __init__ function is a constructor method that is called when an object is created

        :param id: The id of the user
        :type id: int
        :param username: The username of the user
        :type username: str
        :param password: The password of the user
        :type password: str
        """

        self.id = id
        self.username = username
        self.password = password


# For the page: login 2
mot_de_pass = []

mode_manuel = 0
"""mode_manuel (int) is set if a user activate it on the settings page. (0 -> disable, 1 -> enable)"""

mode_heure_manuel = [0, 0, 0]
"""mode_heure_manuel (list) is use to store:
1. (boolean) set if mode heure manuel activated.
2. (int) current day. 0 to 6 -> 0 is monday.
3. () delta time.
"""

cam_connect = [[False, "", "b8:27:eb:26:5a:95", 0], [False, "", "b8:27:eb:ce:4f:78", 0]]
"""cam_connect (list) of the authorized camera.
To check the authorisation, I used the mac adresse.
1. (str) True if connected.
2. (str) Ip adresse.
3. (str) Mac adresse.
"""

# This is a timedelta object. It is a duration expressing the difference between two dates.
TURNOFFTIME = timedelta(minutes=1)
"""TURNOFFTIME (timedelta) is the time duration before the light turn off."""

cam_send_turn_off = []

number_of_people = 0
"""number_of_people (int) is the number of people in the room."""

# Try to open password.pickle. this file contains the 3 passwords.
try:
    # This code is opening a pickle file and reading it.
    with open('password.pickle', 'rb') as f:
        # This code is loading the pickle file.
        password = pickle.load(f)
except OSError:
    # This code is creating a pickle file that contains a list of passwords.
    with open('password.pickle', 'wb') as f:
        password = ["elo", "admin", "1234"]
        pickle.dump(password, f, pickle.HIGHEST_PROTOCOL)

users = []
"""
user (list) is a list of User objects.
    elo - basic user / can only modifie light
    admin - all access (settings access)
    local - only used for the raspberry why the touchscreen (server) / can access to settings with login page 2 
            / don't have to login to control the light.
"""
# Create the users.
users.append(User(id=1, username='elo', password=password[0]))
users.append(User(id=2, username='admin', password=password[1]))
users.append(User(id=3, username='local', password=password[2]))


def gpio_modif():
    """gpio_modif : modif all gpio"""
    if rpi:
        for i in range(8):
            if buttonSts_p1[i] == "off":
                # OFF
                GPIO.output(i, 0)
            else:
                # ON
                GPIO.output(i, 1)
                # time.sleep(1)     #security time for fuses
    else:
        pass


def get_time():
    """Get the current time and day

    :return: A tuple containing the current time and the current day of the week.
    :rtype: tuple
    """

    # The above code is creating a global variable called mode_heure_manuel.
    global mode_heure_manuel

    # This code is checking if the first element of the list mode_heure_manuel is equal to 1.
    # If the first element is 1 the mode hour manuel is set.
    # The current hour become current hour + delta time.
    if mode_heure_manuel[0] == 1:
        t = datetime.now() + mode_heure_manuel[2]
        current_time = t.strftime("%H:%M")
        current_day = mode_heure_manuel[1]
    else:
        # Creating a time object.
        t = time.localtime()
        # The above code is creating a string of the current time in hours and minutes (10:10).
        current_time = time.strftime("%H:%M", t)
        # This code is checking the current day of the week and then using that to determine
        # which day of the week it is (0 is monday, 6 is sunday).
        current_day = datetime.today().weekday()

    return current_time, current_day


def myping(host):
    """myping : check if a host is up

    :param host: The host to check.
    :type host: str
    :return: True if the host is up, False if not.
    :rtype: bool
    """

    # Checking if the host is empty. If it is empty, it will return False.
    if host == "":
        return False

    if rpi:
        # This code is using the subprocess module to run the ping command on a host.
        response = str(subprocess.check_output(["ping", "-c", "1", host]))
    else:
        # This code is using the os.popen() function to ping the host.
        response = os.popen("ping -n 1 " + host).read()

    # The above code is checking to see if the ping was successful.
    if "0 received" in response:
        return False
    else:
        return True


def getmacadd(host):
    """getmacadd : get the mac adresse of a host

    :param host: The host to check.
    :type host: str
    :return: The mac adresse of the host.
    :rtype: str
    """

    # This code is using the ping function to ping the host.
    rep = myping(host)
    if rep:
        # The above code is using the subprocess module to run the arp command on the host machine. The arp command is
        # used to display the ARP (Address Resolution Protocol) table. The arp table contains the hardware (MAC) address
        # for each IP address on the local area network.
        answer = str(subprocess.check_output(["arp", "-a", host]))

        if "aucune" in answer:
            return False
        else:
            # Splitting the answer into a list of words.
            answer = answer.split(" ")
            # Return only the MAC address
            return answer[3]
    else:
        return False


@app.errorhandler(HTTPException)
def handle_exception(e):
    """handle_exception : handle http error

    :param e: The http error.
    :type e: HTTPException
    :return: The HTML error page.
    :rtype: render_template
    """

    e = str(e)  # 404 not ...  :  The request URL ...
    code = e.split(":")  # 404 Not Found

    # This is a function that takes in an error code and returns the error page for that error.
    return render_template('404.html', error=code[1], title=code[0]), code[0][0:3]


@app.route("/login", methods=['POST', 'GET'])
@app.route("/", methods=['POST', 'GET'])
def login():
    """login : login page
    Receive from POST : username / password
    We first check if username existe and after password.
    If it's a bad username or pass we flash the error.

    :return: The login page.
    :rtype: render_template
    """

    # Creating a variable called current_time that is equal to the current time.
    current_time, _ = get_time()
    # This code is getting the user's IP address and returning it.
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    # check for authorized ip
    for i in authorize_ip:
        if ip == i:
            logging.info("create local user" + str(ip))
            session['user_id'] = 3
            return redirect(url_for('page1'))

    # This code is checking to see if the user is logged in.
    # If they are, then they will be directed to the page 1.
    if session.get("user_id") is not None:
        return redirect(url_for('page1'))

    # This code is checking to see if the request method is a POST. If it is, it will run the code below.
    if request.method == 'POST':
        # This code is removing the user_id from the session.
        session.pop('user_id', None)

        username = request.form['username']
        password = request.form['password']

        try:
            # This code is using a list comprehension to search for a user with a given username.
            user = [x for x in users if x.username == username][0]
            # The above code is checking if the user exists and if the password is correct.
            if user and user.password == password:
                # Login accepted
                session['user_id'] = user.id
                logging.info("New login username : " + username + " ip : " + str(ip))
                return redirect(url_for('page1'))
            elif user.password != password:
                # bad password, logging it and flash the error
                logging.warning("bad password : " + username + " ip : " + str(ip))
                flash("Bad password")

            return redirect(url_for('login'))

        except IndexError:
            # bad username, logging it and flash the error
            logging.warning("bad username : " + username + " ip : " + str(ip))
            flash("Bad username")
            return redirect(url_for('login'))

    return render_template("login.html", time=current_time, warning=warning)


@app.route("/login2", methods=['POST', 'GET'])
def login2():
    """The login2 function is the second page of the login page.
    It is only for the touch screen. It is called when the user want to go in the settings page.
    It checks if the user has entered the correct password. If the user has entered the correct
    password, the user is redirected to the settings page.

    :return: The login2.html template is being returned.
    :rtype: render_template
    """

    # Creating a function that will return the current time.
    current_time, _ = get_time()
    # This code is getting the user's IP address and returning it.
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    # The above code is checking if the IP address of the user is in the list of authorized IP addresses.
    if ip not in authorize_ip:
        return redirect(url_for('login'))

    global mot_de_pass

    # This code is checking to see if the request method is a POST. If it is, it will run the code below.
    if request.method == 'POST':
        button_click = request.form.get('btn')

        # Checking if the button click is a number between 0 and 9.
        if button_click in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            # The above code is adding in the list all the buttons that are clicked.
            mot_de_pass.append(button_click)

        # Checking if the button click is 10 (Effacer)
        if button_click == "10":
            # Clear the list
            mot_de_pass = []

        # Checking if the button click is 11 (Submit)
        if button_click == "11":
            # The code above is taking the list of characters and joining them together to form a string.
            mot_de_pass = "".join(mot_de_pass)
            # This code is using a list comprehension to find the user named "local" and then returning that user.
            user = [x for x in users if x.username == "local"][0]
            # The above code is checking if the password entered by the user is the same as the password stored in the
            # database.
            if mot_de_pass == user.password:
                mot_de_pass = []
                return redirect(url_for('settings', authorized=1))

            mot_de_pass = []

    return render_template('login2.html', mdp=mot_de_pass, time=current_time, warning=warning)


@app.route("/page1", methods=['POST', 'GET'])
def page1():
    """This function is used to display the page 1
    It is the first page of the application.

    :return: The html page is being returned.
    :rtype: render_template
    """

    # Creating a function that will return the current time.
    current_time, _ = get_time()

    # This code is checking to see if the user is logged in. If they are not logged in, then they are redirected to the
    # login page.
    if session.get("user_id") is None:
        return redirect(url_for('login'))

    # This code is checking if all the elements in the list are equal to "on".
    if all(elem == "on" for elem in buttonSts_p1):
        # Button "all on" in page 2 is turn to "on"
        buttonSts_p2[0] = "on"
    else:
        buttonSts_p2[0] = "off"

    # This code is checking to see if the request method is a POST. If it is, it will run the code below.
    if request.method == 'POST':
        # Checking if the button has been pressed.
        if request.form['button_p1'] == '1':
            if buttonSts_p1[0] == "on":
                buttonSts_p1[0] = "off"
                color[0] = "#333333"
            else:
                buttonSts_p1[0] = "on"
                color[0] = "#FFFFFF"
        elif request.form['button_p1'] == '2':
            if buttonSts_p1[1] == "on":
                buttonSts_p1[1] = "off"
                color[1] = "#333333"
            else:
                buttonSts_p1[1] = "on"
                color[1] = "#FFFFFF"
        elif request.form['button_p1'] == '3':
            if buttonSts_p1[2] == "on":
                buttonSts_p1[2] = "off"
                color[2] = "#333333"
            else:
                buttonSts_p1[2] = "on"
                color[2] = "#FFFFFF"
        elif request.form['button_p1'] == '4':
            if buttonSts_p1[3] == "on":
                buttonSts_p1[3] = "off"
                color[3] = "#333333"
            else:
                buttonSts_p1[3] = "on"
                color[3] = "#FFFFFF"
        elif request.form['button_p1'] == '5':
            if buttonSts_p1[4] == "on":
                buttonSts_p1[4] = "off"
                color[4] = "#333333"
            else:
                buttonSts_p1[4] = "on"
                color[4] = "#FFFFFF"
        elif request.form['button_p1'] == '6':
            if buttonSts_p1[5] == "on":
                buttonSts_p1[5] = "off"
                color[5] = "#333333"
            else:
                buttonSts_p1[5] = "on"
                color[5] = "#FFFFFF"
        elif request.form['button_p1'] == '7':
            if buttonSts_p1[6] == "on":
                buttonSts_p1[6] = "off"
                color[6] = "#333333"
            else:
                buttonSts_p1[6] = "on"
                color[6] = "#FFFFFF"
        elif request.form['button_p1'] == '8':
            if buttonSts_p1[7] == "on":
                buttonSts_p1[7] = "off"
                color[7] = "#333333"
            else:
                buttonSts_p1[7] = "on"
                color[7] = "#FFFFFF"
        elif request.form['button_p1'] == 'page_2':
            return redirect(url_for('page2'))
        else:
            pass

        gpio_modif()

    return render_template('page1.html', button=buttonSts_p1, color=color, time=current_time, warning=warning)


@app.route("/page2", methods=['POST', 'GET'])
def page2():
    """This function is used to display the page 2
    It is the second page of the application.

    :return: The page is being rendered.
    :rtype: render_template
    """

    # Creating a variable called current_time that is equal to the current time.
    current_time, _ = get_time()

    # This code is checking to see if the user is logged in. If they are not logged in, then they are redirected to the
    # login page.
    if session.get("user_id") is None:
        return redirect(url_for('login'))

    # This code is checking to see if the request method is a POST. If it is, it will run the code below.
    if request.method == 'POST':
        # All on
        if request.form['button_p1'] == '1':
            buttonSts_p2[0] = "on"
            for i in range(8):
                buttonSts_p1[i] = "on"
                color[i] = "#FFFFFF"
        # All off
        elif request.form['button_p1'] == '2':
            buttonSts_p2[1] = "off"
            for i in range(8):
                buttonSts_p1[i] = "off"
                buttonSts_p2[i] = "off"
                color[i] = "#333333"
        # 1 / 2
        elif request.form['button_p1'] == '3':
            buttonSts_p2[0] = "off"
            buttonSts_p2[1] = "off"

            for i in range(0, 8, 2):
                color[i] = "#FFFFFF"
                color[i + 1] = "#333333"

                buttonSts_p1[i] = "on"
                buttonSts_p1[i + 1] = "off"
        # Left
        elif request.form['button_p1'] == '4':
            buttonSts_p2[0] = "off"
            buttonSts_p2[1] = "off"

            for i in range(0, 8):
                if i < 3:
                    color[i] = "#FFFFFF"
                    buttonSts_p1[i] = "on"
                else:
                    color[i] = "#333333"
                    buttonSts_p1[i] = "off"
        # Right
        elif request.form['button_p1'] == '5':
            buttonSts_p2[0] = "off"
            buttonSts_p2[1] = "off"

            for i in range(0, 8):
                if i > 3 and i != 7:
                    color[i] = "#FFFFFF"
                    buttonSts_p1[i] = "on"
                else:
                    color[i] = "#333333"
                    buttonSts_p1[i] = "off"

        elif request.form['button_p1'] == 'page_1':
            return redirect(url_for('page1'))
        else:
            pass

        gpio_modif()

    return render_template('page2.html', button=buttonSts_p2, color=color, time=current_time, warning=warning)


@app.route("/settings", methods=['POST', 'GET'])
def settings():
    """The settings page is used to change the settings of the application.

    :return: The settings.html template is being returned.
    :rtype: render_template
    """

    id = session.get("user_id")
    authorized = request.args.get('authorized')

    # Get the id for the session.
    # If == None --> go to th page login.
    # If == 3 (local) --> go to the page login 2 or settings if password ok
    # If == 1 (elo) --> remove the id / error 418
    if id is None:
        return redirect(url_for('login'))
    elif id == 3 and authorized != "1":
        return redirect(url_for('login2'))
    elif id == 1:
        session.pop("user_id")
        abort(418)

    # Calling a function that will return the current time.
    current_time, _ = get_time()
    # This code is getting the user's IP address and returning it.
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    global mode_manuel
    global mode_heure_manuel
    global cam_connect

    t = Table()
    t2 = Table2()

    # This code is checking to see if the request method is a POST. If it is, it will run the code under it.
    if request.method == 'POST':

        # This code is getting the data from the form and putting it into variables.
        btn_tbl_1 = request.form.get('btn_tbl_1')
        btn_tbl_2 = request.form.get('btn_tbl_2')
        nouvelle_heure = request.form.get('time')
        supprimer = request.form.get('supp')

        manuel = request.form.get('manuel')
        heure_man = request.form.get('heure_manuel')
        heure_man_btn = request.form.get('heure_manuel_btn')

        modif_mdp = request.form.get('modif_mdp')
        password = request.form.get('password')
        new_password = request.form.get('new_password')

        if btn_tbl_1:
            # The above code is converting the number of table's cell into a row and column number.
            btn_click = float(btn_tbl_1)
            row = int(btn_click)
            column = round((btn_click - row) * 10)

            # This code is calling "modif_table".
            t.modif_table(row, column)
            t.set_table()

        if btn_tbl_2:
            # The above code is converting the number of table's cell into a row and column number.
            btn_click = float(btn_tbl_2)
            row = int(btn_click)
            column = round((btn_click - row) * 10)

            # This code is calling "modif_table" for table 2.
            t2.modif_table(row, column)
            t2.set_table()

        if nouvelle_heure:
            # Adding a custom line to the table.
            t.add_custom_line(nouvelle_heure)
            t.set_table()
            t.set_colonne_heure()

        if supprimer:
            # Deleting the custom line in the table 1.
            t.del_custom_line(supprimer)

        if manuel:
            # This code is inverting the manual mode.
            mode_manuel = 1 - int(manuel)

        if heure_man_btn:
            # This code is inverting the manual mode.
            mode_heure_manuel[0] = 1 - int(heure_man_btn)

            if mode_heure_manuel[0] == 1:
                # Converting the time from the website into a datetime object.
                # Then it is subtracting the current time from the time from the website.
                # Then it is converting the timedelta object into a string.
                x = datetime.fromisoformat(heure_man)
                diff = x - datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")
                diff = timedelta(seconds=diff.seconds)

                # Store the new day (0 is monday).
                mode_heure_manuel[1] = x.weekday()
                # Store the delta time
                mode_heure_manuel[2] = diff

            else:
                # The above code is setting mode_heure_manuel to 0.
                mode_heure_manuel = [0, 0, 0]

            # Creating a function that will be used to get the current time.
            current_time, _ = get_time()

        if modif_mdp:
            # This code is searching the list of users for the user with the same username as the one who is trying to
            # change their password.
            user = [x for x in users if x.username == modif_mdp][0]
            # The above code is checking if the user exists and if the password is correct.
            if user and user.password == password:
                # Checking if the user has selected the local option and if the new password is not only number.
                if modif_mdp == "local" and not new_password.isdigit():
                    flash("New password for local user can only contains numbers")
                else:
                    logging.info("Modification password : " + modif_mdp + " new : " + new_password + " ip : " + str(ip))
                    user.password = new_password

                    # Save the new password on the pickle file
                    with open('password.pickle', 'rb') as f:
                        passw = pickle.load(f)
                    with open('password.pickle', 'wb') as f:
                        passw[int(user.id) - 1] = new_password
                        pickle.dump(passw, f, pickle.HIGHEST_PROTOCOL)

            elif user.password != password:
                # bad password, logging it and flash the error
                logging.warning("Try to modify the password but introduce wrong password : " + modif_mdp + " ip : " + str(ip))
                flash("Wrong password")

    table = t.get_table()
    heure = t.get_colonne_heure()
    new_heure = t.get_new_colonne_heure()

    table2 = t2.get_table()
    name_t2 = t2.get_name()

    return render_template('settings.html', table=table, heure=heure, new_heure=new_heure, table2=table2,
                           name_t2=name_t2, mode_manuel=mode_manuel, mode_heure_manuel=mode_heure_manuel[0],
                           cam_conn=cam_connect, time=current_time, warning=warning)


@app.route('/camera', methods=['POST', 'GET'])
def camera():
    """The camera is only here to receive data from the camera. The script is checking mac address to verify if the
    sender is a RPi camera. If it is, the server is checking if the data is corresponding with the ELO protocol
    (the first byte is 0x55 and the last byte is 0xAA). If it is, the server is checking if the data is corresponding.

    :return: The server is returning the string '$,RPWCOK,002,ok,0*' or '$,RPWCER,005,error,0*'  to the camera.
    :rtype: str
    """

    global cam_connect
    global buttonSts_p1
    global color
    global cam_send_turn_off
    global number_of_people

    # This code is getting the user's IP address and returning it.
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    # Calling a function that will return the current time.
    current_time, current_day = get_time()
    # This code is retrieving the user's id from the session.
    id = session.get("user_id")

    # Check if the user have an id
    # if yes => 404
    if id is not None:
        abort(404)
    # else check is mac add
    else:
        # This code is using the getmacadd function to get the mac address of the ip address.
        mac_add = getmacadd(ip)

        # The above code is checking to see if the MAC address of the camera is in the list of MAC addresses of the
        # cameras that are connected to the system.
        # If the MAC address is not in the list, error 404.
        if not any(mac_add in x for x in cam_connect) or mac_add is False:
            abort(404)

    # Checking if the request method is POST. If it is, it will run the code below.
    if request.method == 'POST':
        data = request.form.get('data')
        # Checking if the data is not empty.
        if data:
            # Verify if data received corresponding with ELO communication protocol
            if data[0] == "$" and data[::-1][0] == "*":
                # The above code is reading the data from the file and splitting it into a list.
                data = data.split(',')
                # RPWCSD is the header (Raspberry Pi Wi-Fi Camera Send Data)
                if data[1] == "RPWCSD":
                    # Length of the data
                    length = int(data[2])
                    # Time when it was sent
                    h = data[3][0:5]
                    # Temperature of the camera
                    cam_temp = int(data[3][5:length - 1])
                    # data : 1 entry, 0 exit
                    d = data[3][length - 1]

                    # The code is checking to see if the temperature is greater than 70 degrees.
                    # If it is, it will update the temperature in the cam_connect list. If not, it will update
                    # the temperature in the cam_connect list as 0.
                    if cam_temp > 70:
                        cam_connect[[mac_add in x for x in cam_connect].index(True)][3] = cam_temp
                    else:
                        cam_connect[[mac_add in x for x in cam_connect].index(True)][3] = 0

                    # The code is checking to see if the data is 1. If it is, it will increment the number of people
                    # else it will decrement the number of people.
                    if d == "1":
                        number_of_people = number_of_people + 1
                    elif d == "0" and number_of_people > 0:
                        number_of_people = number_of_people - 1

                    logging.info(" *** Number of people : " + str(number_of_people) + " ***")

                    # if manuel mode is disabled check for the request
                    # Checking if the user has selected the manual mode. If they have, then the program will not check
                    # the Table value.
                    if not mode_manuel:
                        # Creating two table object.
                        t = Table()
                        table = t.get_table()
                        table_heure = t.get_colonne_heure()

                        t2 = Table2()
                        table2 = t2.get_table()

                        # The above code is splitting the current_time string into two variables: current_h and
                        # current_min.
                        current_h, current_min = [x for x in current_time.split(":")]

                        # Find out in which time slot you are in.
                        for i in reversed(range(len(table_heure))):
                            # Splitting the string into two parts, one for the hours and one for the minutes.
                            h, m = table_heure[i].split(":")
                            if current_h == h and current_min >= m:
                                # if the box is orange
                                if table[i][int(current_day)] == 1 or table[i][int(current_day)] == 3:
                                    # Turn on the light
                                    if d == "1":
                                        # Taking the transpose of the table2 array.
                                        array_t2 = np.array(table2).T

                                        # The above code is selecting the correct row from the array_t2 based on the
                                        # current_day.
                                        array_t2 = array_t2[int(current_day)]
                                        # This code is converting the string values of the button status to integer
                                        # value of 0 or 1.
                                        array_comp = [0 if x == "off" else 1 for x in buttonSts_p1]
                                        # This code is taking the two arrays and comparing them to each other element by
                                        # element.
                                        # Then do an OR operation to turn on the new light without modifying the other.
                                        array_t2_or = [a or b for a, b in zip(array_t2, array_comp)]

                                        # If the value is 0, it will be "off", otherwise it will be "on".
                                        buttonSts_p1 = ["off" if x == 0 else "on" for x in array_t2_or]
                                        # If the value is 0, it will be "#333333", otherwise it will be "#FFFFFF".
                                        color = ["#333333" if x == 0 else "#FFFFFF" for x in array_t2_or]

                                        # Reset cam_send_turn_off
                                        cam_send_turn_off = []

                                        # Turn on the light
                                        gpio_modif()
                                        logging.info(" *** Camera turn on the light. *** ")
                                    elif d == "0" and number_of_people == 0:
                                        # Add the current_time in cam_send_turn_off.
                                        # After TURNOFFTIME if any other action is arrive turn off all light
                                        cam_send_turn_off.append(current_time)
                                break

                    # This code is checking the list of camera IP addresses and if the IP address is not in the list, it
                    # will add it to the list.
                    for i, x in enumerate(cam_connect):
                        if mac_add in x and ip not in x:
                            cam_connect[i][1] = ip
                            logging.info(" *** New camera : " + ip + " *** ")

                # Return OK to the camera with respecting the protocol of communication ELO.
                return '$,RPWCOK,002,ok,0*'

    # Return error to the camera with respecting the protocol of communication ELO.
    return '$,RPWCER,005,error,0*'


@app.before_first_request
def activate_job():
    """activate_job : fonction to run job on background of the web server (with thread)

    :return: None
    :rtype: None
    """

    def run_job():
        """run_job : run background job (run every minute).
        Automatically turn off the light.
        Check temperature of the Raspberry Pi

        :return: None
        :rtype: None
        """

        global mode_manuel
        global mode_heure_manuel
        global cam_connect
        global cam_send_turn_off
        global TURNOFFTIME
        global number_of_people

        current_time, _ = get_time()
        saved_time = current_time

        logging.debug(" *** Starting while loop *** ")

        # While loop that will run forever.
        while True:
            # Wait a minute.
            while saved_time == current_time:
                current_time, current_day = get_time()

            saved_time = current_time

            # The above code is checking if the current time is 00:00 (midnight).
            # If it is, it sets the mode_manuel to 0 and the mode_heure_manuel to [0, 0, 0].
            if current_time == "00:00":
                number_of_people = 0
                mode_manuel = 0
                mode_heure_manuel = [0, 0, 0]
                logging.info(" *** Reset midnight ***")

            # check for automatic off on the table 1 or if camera requested a shutdown
            if not mode_manuel:
                # Getting all the value of the table 1.
                t = Table()
                table = t.get_table()
                table_heure = t.get_colonne_heure()

                # Check for automatic turn off
                for i in range(len(table_heure)):
                    # Check if current_time is equal to one of the times in the table.
                    if current_time == table_heure[i]:
                        # Ff the box in the table is blue.
                        if table[i][int(current_day)] > 1:
                            # Turn all off.
                            logging.info(" *** Server turn all off automatically ***")

                            for x in range(8):
                                buttonSts_p1[x] = "off"
                                buttonSts_p2[x] = "off"
                                color[x] = "#333333"

                # Checks if the camera has requested a shutdown
                for time_turn_off in cam_send_turn_off:
                    # Compares the current time with the time of the requests add to TURNOFFTIME.
                    time_add = datetime.strptime(time_turn_off, '%H:%M') + TURNOFFTIME
                    time_add = time_add.strftime("%H:%M")
                    if current_time == time_add:
                        # Clear the requests list
                        cam_send_turn_off = []

                        # Split the current time
                        current_h, current_min = [x for x in current_time.split(":")]

                        # Find out what time slot you are in
                        for j in reversed(range(len(table_heure))):
                            h, m = table_heure[j].split(":")
                            if current_h == h and current_min >= m:
                                # If camera as authorisation
                                if table[j][int(current_day)] == 1 or table[j][int(current_day)] == 3:
                                    # Turn all off.
                                    logging.info(" *** Camera turn all the light off ***")

                                    for x in range(8):
                                        buttonSts_p1[x] = "off"
                                        buttonSts_p2[x] = "off"
                                        color[x] = "#333333"

                # Update GPIO
                gpio_modif()

            # The above code is reading the temperature of the CPU only if it's running on a RPi.
            if rpi:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as ftemp:
                    global warning
                    temp = int(ftemp.read()) / 1000
                    # This code is checking the temperature and if it is greater than 60 it will send a warning.
                    if temp > 60:
                        logging.warning(" *** Temp = " + str(int(temp)) + "°C *** ")
                        warning = "Temp = " + str(int(temp)) + "°C"
                    else:
                        warning = ""

            # The above code is checking to see if the cameras are online.
            for i in range(len(cam_connect)):
                ip_cam = cam_connect[i][1]
                cam_connect[i][0] = myping(ip_cam)

    # This code is creating a thread that will run the run_job function.
    thread = threading.Thread(target=run_job)
    thread.start()


if __name__ == "__main__":
    logging.info(" *** Starting server *** ")
    app.run(host='0.0.0.0', port=80, debug=False)
    GPIO.cleanup()
    logging.info(" *** Server stopped *** ")
