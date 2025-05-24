from django.apps import AppConfig

class DiscourseIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'discourse_integration'
    verbose_name = 'Discourse Integration'

    def ready(self):
        import discourse_integration.signals # Import signals
