from django.urls import path, include

urlpatterns = [
    # 其他路径...
    path('api/oauth/', include('oAuth.urls')),
    # ...
] 