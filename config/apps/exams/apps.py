# from django.apps import AppConfig

# class ExamsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'apps.exams'

#     def ready(self):
#         import apps.exams.signals  # ✅ This will now be called


from django.apps import AppConfig

class ExamsConfig(AppConfig):
    name = "apps.exams"
    def ready(self):
        import apps.exams.signals
