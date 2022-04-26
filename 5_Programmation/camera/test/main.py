"""main.py | Robin Forestier

Fichier de test pour Opencv
"""

# `import cv2` imports the OpenCV library, while `import numpy as np` imports the numpy library.
import cv2
import numpy as np

# Show information about OpenCV
print(__doc__)
print("[INFO] Version d'OpenCV : ", cv2.__version__)
print("[INFO] Version de numpy : ", np.__version__)
print("\n[INFO] Press any buton to quit.")

# Reading the image and storing it in the variable `img`.
img = cv2.imread("test.png")

# Displaying the image `img` in a window called `test`.
cv2.imshow("test", img)

# `cv2.waitKey(0)` waits for a key to be pressed. `cv2.destroyAllWindows()` destroys all windows.
cv2.waitKey(0)
cv2.destroyAllWindows()
