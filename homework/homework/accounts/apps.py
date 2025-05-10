# factory/apps.py
from django.apps import AppConfig

class FactoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals  # signals.py dosyasını yükle
