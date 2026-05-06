from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, StreamingHttpResponse
from ml.realtime import generate_frames
import ml.realtime as rt
from django.http import HttpResponse
from django.conf import settings
import os
import csv
from django.http import JsonResponse
from ml.video_processing import process_video
from django.core.files.storage import FileSystemStorage
import threading
from ml.video_processing import STOP_FLAG
from datetime import datetime
from django.contrib.auth import logout
from admin_panel.models import PlateList
from django.shortcuts import get_object_or_404
from django.utils.timezone import localtime, localdate
from django.db import IntegrityError
from django.contrib import messages
from django.urls import reverse
from django.core.cache import cache


# Create your views here.

def guard_login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check user in database
        user = authenticate(request,username=username,password=password)

        if user:
            if user.role != 'guard':
                return render(request, "guard_login.html", {'error': 'Not a guard'})
            auth_login(request, user)
            return redirect('guard_dashboard')
        else:
            return render(request, "guard_login.html", {'error': 'Invalid username or password'})
    return render(request, "guard_login.html")

@login_required
def guard_dashboard(request):
    if request.user.role != 'guard':
        return redirect('signup')


    return render(request,"guard_dashboard.html")


def logout_view(request):
    logout(request) 
    response = redirect('home')

    # prevent browser back cache
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response

def video_feed(request):
    VIDEO_PATH = os.path.join(settings.BASE_DIR, "static/videos/demo.mp4")
    return StreamingHttpResponse(
        generate_frames(VIDEO_PATH),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

def stop_video(request):
    rt.CONTROL["RUN_STREAM"] = False
    return HttpResponse("Video stopped")

def start_video(request):
    rt.CONTROL["RUN_STREAM"] = True
    return HttpResponse("Video started")

def stop_detection(request):
    rt.CONTROL["RUN_DETECTION"] = False
    return HttpResponse("Detection Stopped")

def start_detection(request):
    rt.CONTROL["RUN_DETECTION"] = True
    return HttpResponse("Detection Started")

def get_realtime_data(request):
    data = []
    today_count = 0
    latest_plate = ""
    latest_status = ""
    alerts = []
    today_date = localdate()
    today_alert_count = 0

    try:
        with open("outputs/realtime_log.csv", "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = row.get("timestamp", "")
                plate = row.get("plate", "")
                status = row.get("status", "")
                record = {
                    "datetime": row["timestamp"],
                    "plate": plate,
                    "status": status,
                    "image": f"media/cars/{plate}.jpg"
                }

                data.append(record)

                # ALERT DETECTION
                if status and "BLACKLIST" in status.upper():

                    alerts.append({
                        "datetime": timestamp,
                        "plate": plate,
                        "status": status
                    })

                    # count today's blacklist alerts
                    try:
                        row_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").date()
                        if row_date == today_date:
                            today_alert_count += 1
                    except:
                        pass

                # count today's entries
                try:
                    row_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").date()
                    if row_date == datetime.today().date():
                        today_count += 1

                except:
                    pass

    except Exception as e:
        print("CSV ERROR:", e)

    data = list(reversed(data))
    alerts = list(reversed(alerts))[:10]

    cache_key = "last_alerts"
    last_alerts = set(cache.get(cache_key, []))

    new_alerts = []

    for alert in alerts:
        key = f"{alert['plate']}_{alert['datetime']}"

        if key not in last_alerts:
            new_alerts.append(alert)
            last_alerts.add(key)

    # keep only last 100 entries
    cache.set(cache_key, list(last_alerts)[-100:], timeout=3600)

    # latest detection
    if data:
        latest = data[0]
        latest_plate = latest.get("plate", "")
        latest_status = latest.get("status", "")

    q = request.GET.get("q", "").strip().lower()

    if q:
        filtered = []
        for d in data:
            plate = str(d.get("plate", "")).strip().lower()
            if q in plate:
                filtered.append(d)
        data = filtered

    page_number = request.GET.get("page", 1)
    paginator = Paginator(data, 4)
    page = paginator.get_page(page_number)

    return JsonResponse({
        "records": list(page),
        "has_next": page.has_next(),
        "has_prev": page.has_previous(),
        "page": page.number,
        "total_records": paginator.count,

        # dashboard cards
        "today_count": today_count,
        "latest_plate": latest_plate,
        "latest_status": latest_status,

        # popup alerts (only new ones)
        "alerts": new_alerts,

        # TODAY BLACKLIST COUNT
        "today_alert_count": today_alert_count
    })

# global flag
PROCESSING_STATUS = {
    "running": False
}

def guard_smart_scan(request):
    if request.method == "POST" and request.FILES.get("video"):
        
        video_file = request.FILES["video"]
        print("Processing started")


        # Save inside static/videos/
        upload_dir = os.path.join(settings.BASE_DIR, "static/videos")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, video_file.name)

        # Save file
        with open(file_path, "wb+") as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)

        print(" Video saved at:", file_path)

        # mark processing started
        PROCESSING_STATUS["running"] = True
        STOP_FLAG["stop"] = False

        def run_processing():
            try:
                process_video(file_path)
            except Exception as e:
                print(" Error in processing:", e)
            finally:
                PROCESSING_STATUS["running"] = False
                print(" Processing finished") 

        #  Run processing (background)
        threading.Thread(target=run_processing).start()

        return JsonResponse({
            "message": "Processing started",
            "running": True   
        })

    return render(request, "guard_smart_scan.html")

def processing_status(request):
    return JsonResponse({
        "running": PROCESSING_STATUS["running"]
    })

def stop_processing(request):
    STOP_FLAG["stop"] = True
    PROCESSING_STATUS["running"] = False
    return JsonResponse({"stopped": True})

def get_video_results(request):
    data = []

    file_path = os.path.join(settings.BASE_DIR, "outputs", "final_video_results.csv")

    query = request.GET.get("q", "").strip().upper()

    #  If file not exists → return empty
    if not os.path.exists(file_path):
        return JsonResponse({
        "records": [],
        "page": 1,
        "has_next": False,
        "has_prev": False,
        "total": 0
    })

    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            plate = row.get("license_number", "").upper()

            #  APPLY SEARCH FILTER
            if query and query not in plate:
                continue

            data.append({
                "time": row["time"],
                "plate": row["license_number"],
                "confidence": row["confidence"],
                "image": f"media/cars/{row['license_number']}.jpg"
            })

    #  PAGINATION
    page_number = request.GET.get("page", 1)
    paginator = Paginator(data, 5)  # 5 rows per page

    page = paginator.get_page(page_number)

    return JsonResponse({
        "records": list(page),
        "page": page.number,
        "has_next": page.has_next(),
        "has_prev": page.has_previous(),
        "total": paginator.count
    })

def guard_vehicle_records(request):
    return render(request, "guard_vehicle_records.html")

def vehicle_data(request):

    q = request.GET.get("q", "").strip().upper()
    date = request.GET.get("date", "")
    status = request.GET.get("status", "")
    page = int(request.GET.get("page", 1))

    csv_path = "outputs/realtime_log.csv"

    data = []

    # read CSV
    if os.path.exists(csv_path):
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    "datetime": row["timestamp"],
                    "plate": row["plate"],
                    "status": row["status"],
                    "image": f"media/cars/{row['plate']}.jpg"
                })

    #  filters
    if q:
        data = [d for d in data if q in d["plate"]]

    if date:
        data = [d for d in data if d["datetime"].startswith(date)]

    if status:
        data = [d for d in data if d["status"] == status]

    #  latest first
    data = list(reversed(data))

    #  pagination
    per_page = 7
    total = len(data)
    start = (page - 1) * per_page
    end = start + per_page

    paginated = data[start:end]

    return JsonResponse({
        "records": paginated,
        "page": page,
        "total_records": total,
        "has_next": end < total,
        "has_prev": start > 0
    })

def download_scan_data(request):
    file_path = os.path.join(settings.BASE_DIR, "outputs", "final_video_results.csv")

    if not os.path.exists(file_path):
        return HttpResponse("No data available")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="scan_data.csv"'

    with open(file_path, "r") as f:
        response.write(f.read())

    return response

TAGS = {
    "BLACKLIST": ["Stolen", "Unauthorized", "Suspicious"],
    "WHITELIST": ["VIP", "Staff", "Resident"]
}

def get_counts(request):
    blacklist_count = PlateList.objects.filter(list_type="BLACKLIST").count()
    whitelist_count = PlateList.objects.filter(list_type="WHITELIST").count()

    return JsonResponse({
        "blacklist": blacklist_count,
        "whitelist": whitelist_count
    })

def export_csv(request):
    tab = request.GET.get("tab", "blacklist")
    query = request.GET.get("q", "")
    tag = request.GET.get("tag", "")

    plates = PlateList.objects.all()

    #  Tab filter
    if tab == "blacklist":
        plates = plates.filter(list_type="BLACKLIST")
    elif tab == "whitelist":
        plates = plates.filter(list_type="WHITELIST")

    #  Search filter
    if query:
        plates = plates.filter(plate_number__icontains=query)

    #  Tag filter
    if tag:
        plates = plates.filter(tag=tag)

    #  Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vehicle_data.csv"'

    writer = csv.writer(response)
    writer.writerow(["Plate", "Tag", "Notes", "List Type", "Added On", "Added By"])

    for p in plates:
        writer.writerow([
            p.plate_number,
            p.tag,
            p.notes,
            p.list_type,
            p.added_on.strftime("%Y-%m-%d %H:%M"),
            p.added_by.username if p.added_by else "N/A"
        ])

    return response

def get_plate_status(plate_number):
    from .models import PlateList

    plate = PlateList.objects.filter(plate_number=plate_number).first()

    if not plate:
        return "UNKNOWN"

    return plate.tag or "UNKNOWN"