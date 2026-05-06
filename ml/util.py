import re
import easyocr
import string
from difflib import get_close_matches
from collections import defaultdict
from difflib import SequenceMatcher
import os
import cv2

os.makedirs("outputs/cars", exist_ok=True)

def is_similar(p1, p2):
    return SequenceMatcher(None, p1, p2).ratio() > 0.9

# Initialize the OCR reader
reader = easyocr.Reader(['en'], gpu=True)

valid_states = [
    'AN','AP','AR','AS','BR','CH','CG','DD','DL','DN','GA',
    'GJ','HR','HP','JH','JK','KA','KL','LA','LD','MH','ML',
    'MN','MP','MZ','NL','OD','PB','RJ','SK','TN','TR',
    'TS','UK','UP','WB'
]

def is_valid_plate_format(text):
    return license_complies_format(text) or license_complies_special_format(text)

def is_valid_plate(text):
    return 9 <= len(text) <= 10

def valid_state(text):
    return text[:2] in valid_states

def clean_text(text):
    # remove everything except letters & digits
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text

def normalize_plate(text):
    # if length is 9, assume missing digit after state
    if len(text) == 9:
        text = text[:2] + '0' + text[2:]
    return text

def correct_state(text):
    if len(text) < 2:
        return text
    
    state = text[:2]

    # if already valid → return
    if state in valid_states:
        return text

    #  find closest match
    match = get_close_matches(state, valid_states, n=1, cutoff=0.5)

    if match:
        corrected_state = match[0]
        return corrected_state + text[2:]

    return text

def write_csv(results, output_path):
    """
    Write the results to a CSV file.

    Args:
        results (dict): Dictionary containing the results.
        output_path (str): Path to the output CSV file.
    """
    with open(output_path, 'w') as f:
        f.write('{},{},{},{},{},{},{}\n'.format('frame_nmr', 'car_id', 'car_bbox',
                                                'license_plate_bbox', 'license_plate_bbox_score', 'license_number',
                                                'license_number_score'))

        for frame_nmr in results.keys():
            for car_id in results[frame_nmr].keys():
                print(results[frame_nmr][car_id])
                if 'car' in results[frame_nmr][car_id].keys() and \
                   'license_plate' in results[frame_nmr][car_id].keys() and \
                   'text' in results[frame_nmr][car_id]['license_plate'].keys():
                    f.write('{},{},{},{},{},{},{}\n'.format(frame_nmr,
                                                            car_id,
                                                            '[{} {} {} {}]'.format(
                                                                results[frame_nmr][car_id]['car']['bbox'][0],
                                                                results[frame_nmr][car_id]['car']['bbox'][1],
                                                                results[frame_nmr][car_id]['car']['bbox'][2],
                                                                results[frame_nmr][car_id]['car']['bbox'][3]),
                                                            '[{} {} {} {}]'.format(
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][0],
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][1],
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][2],
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][3]),
                                                            results[frame_nmr][car_id]['license_plate']['bbox_score'],
                                                            results[frame_nmr][car_id]['license_plate']['text'],
                                                            results[frame_nmr][car_id]['license_plate']['text_score'])
                            )
        f.close()

def license_complies_format(text):
    """
    Valid Indian license plate format:
    e.g. UP32AB1234
    """
    pattern = r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,2}[0-9]{3,4}$'
    return re.match(pattern, text) is not None

def license_complies_special_format(text):
    """
    Allow formats like:
    DL2CAT4762
    DL7CD5017
    """
    pattern = r'^[A-Z]{2}[0-9]{1}[A-Z]{3}[0-9]{4}$'
    return re.match(pattern, text) is not None


def fix_series_O_to_Q(text):
    text = list(text)

    # series = positions 4,5
    if len(text) >= 6:
        series = text[4:6]

        # if contains O → possible OCR mistake
        if 'O' in series:
            # heuristic: Q is less common, but appears in some series
            # replace only if both are letters
            for i in range(4, 6):
                if text[i] == 'O':
                    text[i] = 'Q'

    return ''.join(text)


def format_license(text):
    text = list(text)

    for i in range(len(text)):

        # State code (letters)
        if i < 2:
            if text[i] in ['0']:
                text[i] = 'O'
            if text[i] in ['1']:
                text[i] = 'I'
            if text[i] in ['W']:
                text[i] = 'U'
            if text[i] in ['B']:
                text[i] = 'P'
            if text[i] in ['N']:
                text[i] = 'D'

        # RTO code (digits)
        elif i in [2, 3]:
            if text[i] in ['O']:
                text[i] = '0'
            if text[i] in ['I']:
                text[i] = '1'
            if text[i] in ['Z']:
                text[i] = '7'
            if text[i] in ['B']:
                text[i] = '8'
            if text[i] in ['E']:
                text[i] = '8'

        # Series (letters)
        elif 4 <= i <= 5:
            if text[i] in ['0']:
                text[i] = 'O'
            if text[i] in ['1']:
                text[i] = 'I'
            if text[i] in ['5']:
                text[i] = 'S'
            if text[i] in ['8']:
                text[i] = 'B'

        # Number (digits)
        elif i >= 6:
            if text[i] in ['O']:
                text[i] = '0'
            if text[i] in ['S']:
                text[i] = '5'
            if text[i] in ['B']:
                text[i] = '8'
            if text[i] in ['Q']:
                text[i] = '0'
            if text[i] in ['J']:
                text[i] = '3'
            if text[i] in ['G']:
                text[i] = '9'
            if text[i] in ['U']:
                text[i] = '0'
            if text[i] in ['A']:
                text[i] = '4'

    return ''.join(text)


def read_license_plate(license_plate_crop):
    detections = reader.readtext(license_plate_crop)

    for detection in detections:
        bbox, text, score = detection

        text = text.upper()

        #  STEP 1: clean noise
        text = clean_text(text)

        #  fix length
        text = normalize_plate(text)

        #  STEP 2: fix characters
        text = format_license(text)

        #  Step 3: apply O → Q fix ONLY when confidence is low
        if score < 0.7:
            text = fix_series_O_to_Q(text)

        #  Step 4: correct state
        text = correct_state(text)

         #  Step 5: validate
        if is_valid_plate_format(text) and is_valid_plate(text):
            return text, score
        print("OCR RAW:", text, "SCORE:", score)

    return None, None


def get_car(license_plate, vehicle_track_ids):
    x1, y1, x2, y2, score , class_id = license_plate

    best_match = None
    max_area = 0

    for j in range(len(vehicle_track_ids)):
        xcar1, ycar1, xcar2, ycar2, car_id = vehicle_track_ids[j]

        # intersection
        xi1 = max(x1, xcar1)
        yi1 = max(y1, ycar1)
        xi2 = min(x2, xcar2)
        yi2 = min(y2, ycar2)

        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)

        if inter_area > max_area:
            max_area = inter_area
            best_match = vehicle_track_ids[j]

    if best_match is not None:
        return best_match

    return -1, -1, -1, -1, -1

# final CSV should have columns: frame_nmr, car_id, license_number, confidence
def write_final_csv(results, frames, output_path):
    plate_history = defaultdict(list)

    #  collect all plates per car (with frame)
    for frame_nmr in results:
        for car_id in results[frame_nmr]:

            plate_data = results[frame_nmr][car_id]['license_plate']
            text = plate_data['text']
            score = plate_data['text_score']

            # skip bad data
            if text == "UNKNOWN" or score < 0.5:
                continue

            timestamp = results[frame_nmr][car_id]['license_plate'].get('timestamp', '')

            plate_history[car_id].append((text, score, frame_nmr, timestamp))

    #  function to pick best plate
    def get_best_plate(plates):
        score_map = {}

        #  Step 1: group by plate text
        for text, score, frame, timestamp in plates:
            if text not in score_map:
                score_map[text] = []
            score_map[text].append((score, frame, timestamp))

        #  Step 2: keep ONLY valid format plates
        valid_score_map = {}
        for text in score_map:
            if is_valid_plate_format(text):   #  important filter
                valid_score_map[text] = score_map[text]

        #  Step 3: fallback if no valid plates found
        if valid_score_map:
            score_map = valid_score_map

        best_text = None
        best_score_final = 0
        best_frame = None

        #  Step 4: select best plate
        for text in score_map:
            scores_frames = score_map[text]

            max_score = max(s for s, _, _ in scores_frames)
            freq = len(scores_frames)

            #  combine confidence + frequency
            final_score = 0.8 * max_score + 0.2 * (freq / 10)
            final_score = min(1.0, final_score)

            if final_score > best_score_final:
                best_score_final = final_score
                best_text = text

                # pick frame with highest score
                best_entry = max(scores_frames, key=lambda x: x[0])
                best_frame = best_entry[1]
                best_timestamp = best_entry[2]

        return best_text, best_score_final, best_frame, best_timestamp
    #  write final CSV
    with open(output_path, 'w') as f:
        f.write('time,license_number,confidence\n')

        final_plates = {}

        for car_id in plate_history:
            best_text, best_score, best_frame,best_timestamp = get_best_plate(plate_history[car_id])

            if not is_valid_plate_format(best_text):
                continue

            matched_plate = None

            #  merge similar plates
            for plate in final_plates:
                if is_similar(plate, best_text):
                    matched_plate = plate
                    break

            if matched_plate:
                continue   # already stored

            final_plates[best_text] = (best_timestamp, best_score, best_frame)

        for plate in final_plates:
            timestamp, score, frame_nmr = final_plates[plate]

            #  get frame
            frame = frames[frame_nmr].copy()

            #  OPTIONAL: draw bounding box (if you want)
            for car_id in results[frame_nmr]:
                data = results[frame_nmr][car_id]
                if data['license_plate']['text'] == plate:

                    cx1, cy1, cx2, cy2 = map(int, data['car']['bbox'])
                    px1, py1, px2, py2 = map(int, data['license_plate']['bbox'])

                    cv2.rectangle(frame, (cx1, cy1), (cx2, cy2), (0,255,0), 2)
                    cv2.rectangle(frame, (px1, py1), (px2, py2), (0,0,255), 2)
                    break

            # save image
            img_path = f"outputs/cars/{plate}.jpg"
            cv2.imwrite(img_path, frame)

            confidence_percent = round(score * 100)

            f.write(f"{timestamp},{plate},{confidence_percent}%\n")