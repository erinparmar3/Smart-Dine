from django.apps import AppConfig


class HomeConfig(AppConfig):
    name = 'home'

    def ready(self):
        # Django 4.2 + Python 3.14 compatibility:
        # django.template.context.BaseContext.__copy__ uses copy(super()),
        # which breaks on Python 3.14 for admin changelist rendering.
        import sys
        if sys.version_info < (3, 14):
            return

        from django.template.context import BaseContext

        if getattr(BaseContext, "_py314_copy_patch_applied", False):
            return

        def _base_context_copy(self):
            duplicate = object.__new__(self.__class__)
            duplicate.__dict__ = self.__dict__.copy()
            duplicate.dicts = self.dicts[:]
            return duplicate

        BaseContext.__copy__ = _base_context_copy
        BaseContext._py314_copy_patch_applied = True
