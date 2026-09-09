from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from chat.api_views import ViewCSVExportView

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT Auth
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Chat application
    # CSV Export
    path("api/exports/<str:filename>/", ViewCSVExportView.as_view(), name="csv_export"),

    # Chat application
    path("", include("chat.urls")),

    # Settings panel
    path("settings/", include("settings_panel.urls")),
]