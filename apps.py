from django.apps import AppConfig


class Attendance2226Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance2226'

    def ready(self):
        import attendance2226.signals  # Ensures that signal handlers are registered
