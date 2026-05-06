import cv2
import csv
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANPRLMS.settings')
django.setup()
import numpy as np
from datetime import datetime
from difflib import SequenceMatcher
from ml.util import is_valid_plate_format, is_valid_plate
from ml.detector import process_frame
from collections import defaultdict, Counter
from django.conf import settings
from admin_panel.models import PlateList
import time

last_fetch = 0
plate_map = {}

def update_lists():
    global last_fetch, plate_map

    if time.time() - last_fetch > 5:  # refresh every 5 sec
        plates = PlateList.objects.all()
        plate_map = {
            p.plate_number: {
                "tag": p.tag,
                "type": p.list_type
            }
            for p in plates
        }
        last_fetch = time.time()

plate_history = defaultdict(list)   # car_id → list of plates
plate_registry = {}                 # final unique plates

#  similarity check (handles OCR mistakes)
def is_similar(p1, p2):
    return SequenceMatcher(None, p1, p2).ratio() > 0.85

CONTROL = {
    "RUN_STREAM": True,
    "RUN_DETECTION": True
}

# def run_realtime(video_path):
def generate_frames(video_path):
    cap = cv2.VideoCapture(video_path)

    #  create outputs folder
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("outputs/cars", exist_ok=True)
    csv_file = "outputs/realtime_log.csv"

    # create CSV with header if not exists
    if not os.path.exists(csv_file):
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "plate", "status"])

    while True:
        update_lists()
        ret, frame = cap.read()
        if not ret:
            # create black frame safely
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

        if not CONTROL["RUN_STREAM"]:
            #  show blank frame instead of breaking
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank, "VIDEO STOPPED", (200, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)
            _, buffer = cv2.imencode('.jpg', blank)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            continue
        
        if CONTROL["RUN_DETECTION"]:
            results = process_frame(frame)
        else:
            results = {"cars": [], "plates": {}}
            
        #  DRAW ALL CARS (IMPORTANT FIX)
        for (cx1, cy1, cx2, cy2) in results["cars"]:
            cv2.rectangle(frame, (cx1, cy1), (cx2, cy2), (0, 255, 0), 2)

        # for car_id in results:
        for car_id in results["plates"]:

            plate_bbox = results["plates"][car_id]["plate_bbox"]
            plate = results["plates"][car_id]["text"]

            #  ONLY IF PLATE EXISTS
            if plate_bbox is not None and plate is not None and plate != "UNKNOWN":
                x1, y1, x2, y2 = plate_bbox

                # validate plate
                if not (is_valid_plate_format(plate) and is_valid_plate(plate)):
                    continue
                plate = plate.strip().upper()

                #  store plate history per car
                plate_history[car_id].append(plate)

                # keep last few entries only
                plate_history[car_id] = plate_history[car_id][-10:]
                status = "DETECTING..."
                color = (255, 255, 0)  # default color (cyan)

                #  wait until stable detections
                if len(plate_history[car_id]) >= 1 or len(set(plate_history[car_id])) == 1:

                    # get best plate
                    best_plate = Counter(plate_history[car_id]).most_common(1)[0][0]

                    #  match with existing plates
                    matched_plate = None
                    for existing_plate in plate_registry:
                        if is_similar(existing_plate, best_plate):
                            matched_plate = existing_plate
                            break

                    plate_info = plate_map.get(best_plate)
                    if plate_info:
                        tag = plate_info["tag"] or "UNKNOWN"

                        if plate_info["type"] == "BLACKLIST":
                            status = f"BLACKLIST ({tag})"
                            color = (0, 0, 255)  #  red

                        elif plate_info["type"] == "WHITELIST":
                            status = f"{tag}"
                            color = (0, 255, 0)  #  green
                    else:
                        status = "UNKNOWN"
                        color = (0, 255, 255)  # yellow

                    #  SAVE only if new
                    if not matched_plate:
                        plate_registry[best_plate] = True
                        timestamp_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        with open(csv_file, "a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([timestamp_full, best_plate, status])
                            # ---- SAVE CAR IMAGE (existing) ----
                            car_path = os.path.join(settings.BASE_DIR, "static", "media", "cars", f"{best_plate}.jpg")
                            os.makedirs(os.path.dirname(car_path), exist_ok=True)
                            cv2.imwrite(car_path, frame)
                        print(f" FINAL SAVED: {best_plate}")

                    #  use best_plate for display
                    display_plate = best_plate
                else:
                    # not stable yet
                    display_plate = plate

                #  DRAW PLATE BOX + TEXT (optional)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(frame, display_plate, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.putText(frame, status, (x1, y1 - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        #  ENCODE FRAME
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        #  STREAM FRAME TO DJANGO
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()