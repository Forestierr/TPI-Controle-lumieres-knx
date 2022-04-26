"""entry_detect.py | Robin Forestier | 28.03.2022

[WARN] The camera is placed on top of the door.

This file is used to detect entry and exit. It uses PersonneDetect & PersonneTracking.
"""

# Imports
from datetime import datetime
import cv2
import requests
import threading

# import personally module
from sample.personne_detect import PersonneDetect
from sample.personne_tracking import PersonneTracking


def send(info):
    """Send the data to the server

    :param info: the information to send
    :type info: int
    """

    # It's getting the current time.
    t = datetime.now()
    current_time = t.strftime("%H:%M")

    # It's opening the file /sys/class/thermal/thermal_zone0/temp and reading the temperature.
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as ftemp:
            temp = int(int(ftemp.read()) / 1000)
    except OSError:
        temp = 0

    # It's creating a string that will be sent to the server.
    data = "{}{:03d}{}".format(current_time, temp, info)
    data = {'data': '$,RPWCSD,{:03d},{},0*'.format(len(data), data)}

    try:
        # It's sending the data to the server.
        # Change the url to your own server.
        r = requests.post("http://172.16.32.133/camera", data=data, timeout=0.5)

        # This is checking if the status code is bigger than 299. If it is, it's printing an error message.
        if r.status_code > 299:
            print("[Error] Communication error, code : ", r.status_code)
        else:
            # It's getting the data from the server.
            data = r.text
            # if the data is a correct trame ($,...,*)
            if data[0] == "$" and data[::-1][0] == "*":
                data = data.split(',')

                # Communication OK
                if data[1] == "RPWCOK":
                    print("ok")
                # Communication Error
                if data[1] == "RPWCER":
                    print("[ERROR] The cam had send a bad trame.")

    # It's catching the error if the server is not available.
    except requests.exceptions.RequestException as e:
        print(e)


if __name__ == '__main__':
    # It's opening the webcam.
    cap = cv2.VideoCapture(0)

    # It's creating a PersonneDetect object and storing it in the variable `detect`.
    detect = PersonneDetect()
    # It's creating a PersonneTracking object and storing it in the variable `tracking`.
    tracking = PersonneTracking()

    while True:
        # It's getting the frame from the webcam.
        ret, frame = cap.read()

        # It's resizing the frame to 640x480.
        frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_AREA)

        # It's detecting people in the frame.
        frame = detect.personne_detect(frame)
        # It's calculating the centroid of the detected people.
        tracking.calc_centroide(frame, detect.detected)

        # Checking if the personne is entry or exit.
        for inout in tracking.inout:
            if inout == 1:
                print("[INFO] Entrée")
            else:
                print("[INFO] Sortie")

            # Modified by FOR the 25.04.2022, add threading to send data to server
            # To avoid a lag in the image processing
            threading.Thread(target=send, args=(inout,)).start()

        # Clearing the list of detected people.
        tracking.inout.clear()

        # It's showing the image in a window.
        cv2.imshow("image", frame)

        # It's checking if the user press the key "q". If it is, it's breaking the loop.
        if cv2.waitKey(1) == ord("q"):
            break

    # It's closing the webcam and the window.
    cv2.destroyAllWindows()
    cap.release()
