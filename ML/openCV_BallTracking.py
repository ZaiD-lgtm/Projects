import cv2 as cv
import numpy as np
import math

cap = cv.VideoCapture("volleyball_match.mp4")
object_detector = cv.createBackgroundSubtractorKNN(history=3, detectShadows=False)

desired_ratio = 1
err = 0.15
min_area = 200
max_area = 500
kernel = np.ones((3,3), np.uint8)

court_corners = np.array([
    [312, 170],  # top left
    [1000, 170],  # top right
    [1200, 707],  # bottom right
    [114, 707]    # bottom left
], dtype=np.int32)


if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fps = int(cap.get(cv.CAP_PROP_FPS))

fourcc = cv.VideoWriter_fourcc(*'XVID')
out = cv.VideoWriter('OpenCV_Zaid_Task6.mp4', fourcc, fps, (frame_width, frame_height))


pause = False
while cap.isOpened():
    if not pause:
        ret, frame = cap.read()
        if not ret:
            print("No Frames Received!")
            break

        frame_blurred = cv.GaussianBlur(frame, (7, 7), 0)
        cv.imshow("Gaussian Blurred", frame_blurred)
        mask = object_detector.apply(frame)

        #covering the field
        # cv.polylines(frame, [court_corners], isClosed=True, color=(0, 255, 0), thickness=3)
        # box_mask = np.zeros_like(frame[:,:,0])
        # cv.fillPoly(box_mask,[court_corners],color=0)
        # cv.imshow("box")

        lower_thresh, mask = cv.threshold(mask, 200, 255, cv.THRESH_BINARY)
        mask = cv.erode(mask, kernel, iterations=1)
        mask = cv.dilate(mask,kernel,iterations =1)
        # mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel, iterations=1)


        contours, lower_thresh = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        cv.imshow("Eroded", mask)

        for contour in contours:
            area = cv.contourArea(contour)
            if min_area < area < max_area:
                perimeter = cv.arcLength(contour, True)
                if perimeter == 0:
                    continue
                circularity = 4 * math.pi * area / (perimeter * perimeter)
                if circularity > 0.7:
                    x, y, w, h = cv.boundingRect(contour)
                    cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    m = cv.moments(contour)
                    if m["m00"] != 0:
                        cx = int(m["m10"] / m["m00"])
                        cy = int(m["m01"] / m["m00"])
                        cv.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                    cv.drawContours(frame, [contour], -1, (0, 0, 255), 2)

        out.write(frame)

        cv.imshow('Rectangle', frame)

    key = cv.waitKey(30) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(" "):
        pause = not pause

cap.release()
out.release()
cv.destroyAllWindows()
