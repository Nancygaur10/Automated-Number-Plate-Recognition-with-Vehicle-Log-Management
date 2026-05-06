import numpy as np
import cv2
from collections import Counter
from ml.sort.sort import *
from ml.util import *
from ultralytics import YOLO
from django.conf import settings
import torch
import os

BEST_MODEL_PATH = os.path.join(settings.BASE_DIR, "ml/best.pt")
COCO_MODEL_PATH = os.path.join(settings.BASE_DIR, "ml/yolov8s.pt")

# load models ONCE
coco_model = YOLO(COCO_MODEL_PATH)
license_plate_detector = YOLO(BEST_MODEL_PATH)
device = "cuda" if torch.cuda.is_available() else "cpu"
coco_model.to('cuda')
license_plate_detector.to('cuda')

saved_thresh_count = 0
vehicles = [2]

mot_tracker = Sort()
best_plate_per_car = {}

def get_best_plate(plates):
    return Counter(plates).most_common(1)[0][0]

def process_frame(frame):
    results_frame = {}
    all_cars = [] 

    detections = coco_model(frame, conf=0.15)[0].cpu()
    detections_ = []

    for detection in detections.boxes.data.tolist():
        x1, y1, x2, y2, score , class_id = detection
        if int(class_id) in vehicles:
            detections_.append([x1, y1, x2, y2, score])

    if len(detections_) == 0:
        detections_array = np.empty((0, 5))
    else:
        detections_array = np.array(detections_)
        if detections_array.ndim == 1:
            detections_array = np.expand_dims(detections_array, axis=0)

    track_ids = mot_tracker.update(detections_array)

    #store ALL detected cars first
    for track in track_ids:
        xcar1, ycar1, xcar2, ycar2, car_id = track

        car_bbox = [int(xcar1), int(ycar1), int(xcar2), int(ycar2)]
        all_cars.append(car_bbox) 

        results_frame[car_id] = {
            "car_bbox": car_bbox,
            "plate_bbox": None,
            "text": None
        }

    license_plates = license_plate_detector(frame, conf=0.15)[0].cpu()

    for license_plate in license_plates.boxes.data.tolist():
        x1, y1, x2, y2, score , class_id = license_plate

        xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)

        if car_id == -1:
            continue

        pad = 5
        x1 = max(0, int(x1) - pad)
        y1 = max(0, int(y1) - pad)
        x2 = int(x2) + pad
        y2 = int(y2) + pad

        crop = frame[int(y1):int(y2), int(x1):int(x2), :]
        crop = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_LINEAR)

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        #  Step 1: remove noise but keep edges
        gray = cv2.bilateralFilter(gray, 11, 17, 17)

        #  Step 2: improve contrast (better than equalizeHist)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)

        #  Step 3: adaptive threshold (VERY IMPORTANT)
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11, 2
        )

        #  Step 4: remove small noise
        kernel = np.ones((3,3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        text, score = read_license_plate(thresh)

        plate_text = text if text else "UNKNOWN"

        if car_id not in best_plate_per_car:
            best_plate_per_car[car_id] = []

        if plate_text != "UNKNOWN":
            if car_id not in best_plate_per_car:
                best_plate_per_car[car_id] = []

            best_plate_per_car[car_id].append(plate_text)

            best_text = get_best_plate(best_plate_per_car[car_id])

            results_frame[car_id]["plate_bbox"] = [x1, y1, x2, y2]
            results_frame[car_id]["text"] = best_text
            results_frame[car_id]["score"] = score

    # FINAL RETURN (IMPORTANT CHANGE)
    return {
        "cars": all_cars,          # ✅ ALL cars
        "plates": results_frame    # ✅ plate-linked cars
    }