from django.urls import path

from .views import (
    UserPreferenceView,
    credential_list,
    credential_detail,
    activate_credential,
    provider_options,
)

urlpatterns = [
    path("api/preferences/", UserPreferenceView.as_view(), name="user-preferences"),
    path("api/credentials/", credential_list, name="credential-list"),
    path("api/credentials/<int:pk>/", credential_detail, name="credential-detail"),
    path("api/credentials/activate/", activate_credential, name="credential-activate"),
    path("api/credentials/options/", provider_options, name="credential-options"),
]
