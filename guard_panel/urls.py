from guard_panel import views
from django.urls import path

urlpatterns = [
    path("guard_login/", views.guard_login_view, name="guard_login"),
    path("guard_dashboard/", views.guard_dashboard, name='guard_dashboard'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('start_video/', views.start_video, name='start_video'),
    path('stop_video/', views.stop_video, name='stop_video'),
    path('stop_detection/', views.stop_detection, name='stop_detection'),
    path('start_detection/', views.start_detection, name='start_detection'),
    path("realtime-data/", views.get_realtime_data, name="realtime_data"),
    path("guard_smart_scan/", views.guard_smart_scan, name='guard_smart_scan'),
    path("processing-status/", views.processing_status),
    path("stop-processing/", views.stop_processing),
    path("video-results/", views.get_video_results),
    path("guard_vehicle_records/", views.guard_vehicle_records, name='guard_vehicle_records'),
    path("vehicle-data/", views.vehicle_data, name="vehicle_data"),
    path("download-scan-data/", views.download_scan_data, name="download_scan_data"),
    path('logout/', views.logout_view, name='logout'),
]
