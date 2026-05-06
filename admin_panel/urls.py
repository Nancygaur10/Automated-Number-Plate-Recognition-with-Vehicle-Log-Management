from admin_panel import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin_login/",views.admin_login_view,name="admin_login"),
    path("admin_dashboard/", views.admin_dashboard, name='admin_dashboard'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('start_video/', views.start_video, name='start_video'),
    path('stop_video/', views.stop_video, name='stop_video'),
    path('stop_detection/', views.stop_detection, name='stop_detection'),
    path('start_detection/', views.start_detection, name='start_detection'),
    path("realtime-data/", views.get_realtime_data, name="realtime_data"),
    path("smart_scan/", views.smart_scan, name='smart_scan'),
    path("processing-status/", views.processing_status),
    path("stop-processing/", views.stop_processing),
    path("video-results/", views.get_video_results),
    path("vehicle_records/", views.vehicle_records, name='vehicle_records'),
    path("vehicle-data/", views.vehicle_data, name="vehicle_data"),
    path("download-scan-data/", views.download_scan_data, name="download_scan_data"),
    path('logout/', views.logout_view, name='logout'),
    path("blacklist_whitelist/", views.blacklist_whitelist, name='blacklist_whitelist'),
    path("blacklist-data/", views.blacklist_data, name="blacklist_data"),
    path('add-blacklist/', views.add_blacklist, name='add_blacklist'),
    path("delete-plate/<int:id>/", views.delete_plate, name="delete_plate"),
    path("get-tags/", views.get_tags, name="get_tags"),
    path("get-counts/", views.get_counts, name="get_counts"),
    path("export_csv/", views.export_csv, name="export_csv"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
