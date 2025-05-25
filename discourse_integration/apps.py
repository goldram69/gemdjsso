from django.apps import AppConfig

class DiscourseIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'discourse_integration'
    verbose_name = 'Discourse Integration'

    def ready(self):
        # Import signals
        import discourse_integration.signals # noqa: F401 
