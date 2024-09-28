import numpy as np
import cv2
import pynput
import time
from mss import mss
from pynput.mouse import Button, Controller
from pynput.keyboard import Key

#Controller is a global var to avoid having to declare a new controller
def mouse_move(mouse,x,y):
    mouse.position = (x,y)

def mouse_click(mouse):
    mouse.click(Button.left,1)

def mouse_drag(mouse,x,y):
    mouse.press(Button.left)
    mouse.move = (0,-200)
    time.sleep(3)
    mouse.release(Button.left)

def key_press(keyboard,Key):
    keyboard.press(Key)

def capture_screen():
    """Captures the screen using MSS and converts it to a numpy array for CV2"""
    with mss() as sct:
        monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
        #output = "sct-{top}x{left}_{width}x{height}.png".format(**monitor)

        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

def non_max_suppression_fast(boxes, overlapThresh=0.5):
    """Some stonks thing to remove multiple detections on the same position"""
    if len(boxes) == 0:
        return []

    # Convert to float if necessary
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    # Initialize the list of picked indexes
    pick = []

    # Get coordinates of bounding boxes
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    # Compute the area of the bounding boxes and sort by the bottom-right y-coordinate
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(y2)

    # Keep looping while some indexes still remain in the indexes list
    while len(idxs) > 0:
        # Grab the last index in the indexes list, add the index value to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        # Find the largest (x, y) coordinates for the start of the bounding box
        # and the smallest (x, y) coordinates for the end of the bounding box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        # Compute the width and height of the bounding box
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        # Compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]

        # Delete all indexes from the index list that have an overlap greater than the threshold
        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0])))

    # Return only the bounding boxes that were picked
    return boxes[pick].astype("int")


def debug_match_image(template_path ,threshold=0.8):
    """Same as match_image but draws the rectangle"""
    screenshot = capture_screen()
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template image '{template_path}' not found.")
    template_height, template_width = template.shape[:2]

    # Perform template matching
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

    # Get locations where the match confidence exceeds the threshold
    locations = np.where(result >= threshold)
    boxes = []
    # List to hold the center coordinates of all detected elements
    found_elements = []

    # Loop through all the matching locations
    for pt in zip(*locations[::-1]):  # Switch columns and rows
        top_left = pt
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        boxes.append([top_left[0], top_left[1], bottom_right[0], bottom_right[1]])


    boxes = np.array(boxes)

    # Apply non-maximum suppression to remove overlapping boxes
    filtered_boxes = non_max_suppression_fast(boxes)

    # List to hold the center coordinates of all filtered elements
    found_elements = []

    # Draw the filtered boxes and calculate center points
    for (x1, y1, x2, y2) in filtered_boxes:
        # Draw a rectangle around the filtered element
        cv2.rectangle(screenshot, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)

        # Calculate the center of the found element
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        # Add the center coordinates to the list
        found_elements.append((center_x, center_y))

    # Display the screenshot with rectangles drawn around the detected elements
    cv2.imshow('Detected Elements', screenshot)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Return the list of center coordinates of all found elements or None if no elements found
    if len(found_elements) == 0:
        return None
    
    return found_elements

    
def match_image(template_path ,threshold=0.8):
    screenshot = capture_screen()
    """Finds the image specified and returns the centre coordinates"""
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template image '{template_path}' not found.")
    template_height, template_width = template.shape[:2]

    # Perform template matching
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

    # Get locations where the match confidence exceeds the threshold
    locations = np.where(result >= threshold)
    boxes = []

    found_elements = []

    # Loop through all the matching locations
    for pt in zip(*locations[::-1]):  # Switch columns and rows
        top_left = pt
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        boxes.append([top_left[0], top_left[1], bottom_right[0], bottom_right[1]])

    boxes = np.array(boxes)

    # Apply non-maximum suppression to remove overlapping boxes
    filtered_boxes = non_max_suppression_fast(boxes)

    # List to hold the center coordinates of all filtered elements
    found_elements = []

    # Draw the filtered boxes and calculate center points
    for (x1, y1, x2, y2) in filtered_boxes:
        # Draw a rectangle around the filtered element
        #cv2.rectangle(screenshot, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)

        # Calculate the center of the found element
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        # Add the center coordinates to the list
        found_elements.append((center_x, center_y))

    # Return the list of center coordinates of all found elements or None if no elements found
    if len(found_elements) == 0:
        return None
    
    return found_elements

def click_matching(mouse, image_path):
    """Waits for an image to match and click centre of the image"""
    found = match_image(image_path)

    #Searches until Image Found if supposed to be found
    if found is None:
        time.sleep(3)
        click_matching(mouse,image_path)

    else:
        x,y = found[0]
        mouse_move(mouse,x,y)
        mouse_click(mouse)
        time.sleep(2)
        
def press_matching(keyboard,key,image_path):
    """Waits for an image to match and presses a key"""
    found = match_image(image_path)

    #Searches until Image Found if supposed to be found
    if found is None:
        time.sleep(3)
        press_matching(keyboard,key,image_path)

    else:
        time.sleep(2)
        x,y = found[0]
        key_press(keyboard,key)
        
        
        

#dk if i need this for element checking
def element_exist(img_path):
    return match_image(img_path)

#320 289