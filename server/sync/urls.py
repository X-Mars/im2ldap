from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import LDAPConfigViewSet, SyncConfigViewSet, SyncLogViewSet, user_trend_data, get_user_stats

router = DefaultRouter()
router.register('ldap-configs', LDAPConfigViewSet)
router.register('sync-configs', SyncConfigViewSet)
router.register('sync-logs', SyncLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('user-trend/', user_trend_data, name='user-trend'),
    path('user-stats/', get_user_stats, name='user-stats'),
] 