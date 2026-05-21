import re
from django.apps import AppConfig
from django.conf import settings
from django.template import base


class RenderFragmentConfig(AppConfig):
    name = "render_fragment"

    def ready(self):
        allow_multiline = getattr(settings, "RENDER_FRAGMENT_MULTILINE_TAGS", False)

        if allow_multiline:
            base.tag_re = re.compile(base.tag_re.pattern, re.DOTALL)
