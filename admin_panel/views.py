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
from .models import PlateList
from django.shortcuts import get_object_or_404
from django.utils.timezone import localtime, localdate
from django.db import IntegrityError
from django.contrib import messages
from django.urls import reverse
from django.core.cache import cache

# Create your views here.

def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check user in database
        user = authenticate(request,username=username,password=password)

        if user:
            if user.role != 'admin':
                return render(request, "admin_login.html", {'error': 'Not an admin'})
            auth_login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, "admin_login.html", {'error': 'Invalid username or password'})
    return render(request, "admin_login.html")

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('signup')
    return render(request, "admin_dashboard.html")

def logout_view(request):
    logout(request)  #  destroys session
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
    # ALL today's alerts
    today_alerts = []

    for row in data:
        status = row["status"]
        timestamp = row["datetime"]

        if "BLACKLIST" in status.upper():
            try:
                row_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").date()
                if row_date == today_date:
                    today_alerts.append({
                        "datetime": timestamp,
                        "plate": row["plate"],
                        "status": status
                    })
            except:
                pass

    # latest first
    today_alerts = list(reversed(today_alerts))

    cache_key = "last_alerts"
    last_alerts = set(cache.get(cache_key, []))

    new_alerts = []

    for alert in today_alerts:
        key = f"{alert['plate']}_{alert['datetime']}"

        if key not in last_alerts:
            new_alerts.append(alert)
            last_alerts.add(key)

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
        "alerts": today_alerts,        # FULL LIST (for panel)
        "new_alerts": new_alerts,      # ONLY NEW (for popup)

        # TODAY BLACKLIST COUNT
        "today_alert_count": today_alert_count
    })

# global flag
PROCESSING_STATUS = {
    "running": False
}

def smart_scan(request):
    if request.method == "POST" and request.FILES.get("video"):
        
        video_file = request.FILES["video"]
        print(" Processing started")


        # Save inside static/videos/
        upload_dir = os.path.join(settings.BASE_DIR, "static/videos")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, video_file.name)

        # Save file
        with open(file_path, "wb+") as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)

        print(" Video saved at:", file_path)

        #  mark processing started
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

        # Run processing (background)
        threading.Thread(target=run_processing).start()

        return JsonResponse({
            "message": "Processing started",
            "running": True   
        })

    return render(request, "smart_scan.html")

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

def vehicle_records(request):
    return render(request, "vehicle_records.html")

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

def get_tags(request):
    list_type = request.GET.get("type", "BLACKLIST").upper()
    tags = TAGS.get(list_type, [])
    return JsonResponse({"tags": tags})

def blacklist_whitelist(request):

    tab = request.GET.get("tab", "blacklist")
    query = request.GET.get('q', '')
    tag = request.GET.get('tag', '')
    # status = request.GET.get('status', '')

    plates = PlateList.objects.all().order_by('-added_on')

    #  Search
    if query:
        plates = plates.filter(plate_number__icontains=query)

    #  Tag (notes)
    if tag:
        plates = plates.filter(tag=tag)

    #  Status
    # if status:
    #     plates = plates.filter(list_type=status)

    #  Tab filter
    if tab == "blacklist":
        plates = plates.filter(list_type="BLACKLIST")
    elif tab == "whitelist":
        plates = plates.filter(list_type="WHITELIST")

    #  Pagination
    paginator = Paginator(plates, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # counts
    blacklist_count = PlateList.objects.filter(list_type='BLACKLIST').count()
    whitelist_count = PlateList.objects.filter(list_type='WHITELIST').count()

    return render(request, "blacklist_whitelist.html", {
        "plates": page_obj,
        "tab": tab,
        "query": query,
        "tag": tag,
        # "status": status,
        "blacklist_count": blacklist_count,
        "whitelist_count": whitelist_count
    })

def delete_plate(request, id):
    if request.method == "POST":
        plate = get_object_or_404(PlateList, id=id)
        plate.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False})

def blacklist_data(request):
    page = int(request.GET.get("page", 1))
    query = request.GET.get("q", "")
    tab = request.GET.get("tab", "blacklist")
    tag = request.GET.get("tag", "")


    plates = PlateList.objects.all()

    #  TAB FILTER (MOST IMPORTANT FIX)
    if tab == "blacklist":
        plates = plates.filter(list_type="BLACKLIST")
    elif tab == "whitelist":
        plates = plates.filter(list_type="WHITELIST")
        
    if tag:
        plates = plates.filter(tag=tag)

    if query:
        plates = plates.filter(plate_number__icontains=query)

    paginator = Paginator(plates, 7)
    page_obj = paginator.get_page(page)

    data = []
    for p in page_obj:
        data.append({
            "id": p.id,
            "plate": p.plate_number,
            "tag": p.tag,
            "notes": p.notes,
            "image": p.image.url if p.image else None,
            "date": localtime(p.added_on).strftime("%b %d, %Y %I:%M %p"),
            "user": p.added_by.username if p.added_by else "N/A",
            "list_type": p.list_type,
        })

    return JsonResponse({
        "records": data,
        "page": page_obj.number,
        "has_next": page_obj.has_next(),
        "has_prev": page_obj.has_previous(),
        "total_records": paginator.count
    })
    
def add_blacklist(request):
    if request.method == "POST":
        plate = request.POST.get("plate_number")

        if not plate:
            messages.error(request, "Plate number is required.")
            return redirect(f"{reverse('blacklist_whitelist')}?tab=blacklist")

        tag = request.POST.get("tag")
        notes = request.POST.get("notes")
        image = request.FILES.get("image")

        list_type = request.POST.get("list_type") or "BLACKLIST"
        list_type = list_type.upper()

        try:
            PlateList.objects.create(
                plate_number=plate,
                list_type=list_type,
                tag=tag,
                notes=notes,
                image=image,
                added_by=request.user
            )
            messages.success(request, "Vehicle added successfully!")

        except IntegrityError:
            messages.error(request, "This license plate is already exists!")

        return redirect(f"{reverse('blacklist_whitelist')}?tab={list_type.lower()}")
    
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