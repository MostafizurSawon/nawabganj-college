# from django.apps import AppConfig


# class AdmissionsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'apps.admissions'


from django.apps import AppConfig

class AdmissionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admissions"

    def ready(self):
        from . import signals  
