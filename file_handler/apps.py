from django.apps import AppConfig


class FileHandlerConfig(AppConfig):
    name = 'file_handler'

    def ready(self):
        import file_handler.signals

