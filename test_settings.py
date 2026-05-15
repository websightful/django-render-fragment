import sys
from pathlib import Path

# Expose the src/ layout package without requiring an editable install,
# so both `python -m django test` and benchmark_performance.py can import
# the `render_fragment` app directly from the working tree.
_SRC_DIR = Path(__file__).resolve().parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

SECRET_KEY = "test"

INSTALLED_APPS = [
    "render_fragment",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [],
        },
    },
]
