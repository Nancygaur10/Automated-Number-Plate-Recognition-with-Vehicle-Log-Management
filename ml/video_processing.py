import cv2
import os
import time
from ml.detector import process_frame
from ml.util import write_final_csv
from django.conf import settings
from collections import defaultdict

plate_frames = defaultdict(list) 
STOP_FLAG = {"stop": False}

def process_video(file_path):
    global best_plate_data
    best_plate_data = {}
    cap = cv2.VideoCapture(file_path)

    #  Check if video opened
    if not cap.isOpened():
        print(" Error: Cannot open video")
        return

    # FPS safety
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30

    os.makedirs("outputs", exist_ok=True)

    results = {}
    frame_nmr = -1
    frames = {}

    while True:
        if STOP_FLAG["stop"]:
            print(" Processing force stopped")
            break
        
        ret, frame = cap.read()
        if not ret:
            break

        frame_nmr += 1
        frames[frame_nmr] = frame.copy() 
        results[frame_nmr] = {}
        saved_cars = set()

        #  timestamp
        seconds = frame_nmr / fps
        timestamp = time.strftime("%H:%M:%S", time.gmtime(seconds))

        #  detection
        frame_data = process_frame(frame)

        plates = frame_data["plates"] 

        for car_id in plates:

            plate = plates[car_id]["text"]
            score = plates[car_id].get("score", 0)

            if plate == "UNKNOWN":
                continue

            if plates[car_id]["plate_bbox"] is None:
                continue

            # timestamp
            seconds = frame_nmr / fps
            timestamp = time.strftime("%H:%M:%S", time.gmtime(seconds))

            # CHECK BEST SCORE
            if plate not in best_plate_data or score > best_plate_data[plate]["score"]:

                #  Save BEST detection
                best_plate_data[plate] = {
                    "score": score,
                    "frame_nmr": frame_nmr,
                    "timestamp": timestamp,
                    "car_bbox": plates[car_id]["car_bbox"],
                    "plate_bbox": plates[car_id]["plate_bbox"]
                }

            # store for CSV
            results[frame_nmr][car_id] = {
                'car': {
                    'bbox': plates[car_id]["car_bbox"]
                },
                'license_plate': {
                    'bbox': plates[car_id]["plate_bbox"],
                    'text': plate,
                    'bbox_score': 1,
                    'text_score': score,
                    'timestamp': timestamp
                }
            }

    car_save_dir = os.path.join(settings.BASE_DIR, "static", "media", "cars")
    os.makedirs(car_save_dir, exist_ok=True)

    for plate, data in best_plate_data.items():

        frame = frames[data["frame_nmr"]]

        x1, y1, x2, y2 = data["car_bbox"]
        car_img = frame[y1:y2, x1:x2]

        filename = f"{plate}.jpg"
        car_path = os.path.join(car_save_dir, filename)

        cv2.imwrite(car_path, car_img)

        print(f" Saved BEST frame for {plate} (score={data['score']})")

    #  release video
    cap.release()
    print(" Video processing completed")

    # Absolute output path
    output_dir = os.path.join(settings.BASE_DIR, "outputs")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "final_video_results.csv")

    write_final_csv(results, frames, output_path)

    print(" Final CSV saved at:", output_path)