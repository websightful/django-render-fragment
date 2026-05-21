import os
from types import SimpleNamespace

from django.template import Context, Template, TemplateSyntaxError
from django.test import RequestFactory, SimpleTestCase, override_settings

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

TEMPLATES_SETTING = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
        "APP_DIRS": False,
        "OPTIONS": {"context_processors": []},
    }
]


def _render(source, context=None):
    return Template(source).render(Context(context or {}))


@override_settings(TEMPLATES=TEMPLATES_SETTING)
class RenderFragmentTagTest(SimpleTestCase):
    def test_renders_in_place_with_kwargs(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/greeting.html" with name="World" %}'
        )
        self.assertEqual(out, "Hello, World!")

    def test_renders_in_place_with_kwargs_multiline(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment\n"fragments/greeting.html"\nwith name="World" %}'
        )
        self.assertEqual(out, "Hello, World!")

    def test_captures_into_variable_with_as(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/greeting.html" with name="Jane" as g %}'
            'before|{{ g }}|after'
        )
        self.assertEqual(out, "before|Hello, Jane!|after")

    def test_captures_into_variable_with_as_multiline(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment\n"fragments/greeting.html"\nwith\nname="Jane"\nas g %}'
            'before|{{ g }}|after'
        )
        self.assertEqual(out, "before|Hello, Jane!|after")

    def test_supports_extends_inside_fragment(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/card.html" with title="T" body="B" %}'
        )
        self.assertIn('<div class="card">', out)
        self.assertIn('<div class="card-header">T</div>', out)
        self.assertIn('<div class="card-body">B</div>', out)

    def test_parent_context_is_inherited(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/context_inherit.html" with item="X" %}',
            {"user": SimpleNamespace(name="Alice")},
        )
        self.assertEqual(out, "User: Alice, Item: X")

    def test_kwargs_override_parent_context(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/greeting.html" with name="Bob" %}',
            {"name": "Alice"},
        )
        self.assertEqual(out, "Hello, Bob!")

    def test_template_name_can_be_a_variable(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment tpl with name="V" %}',
            {"tpl": "fragments/greeting.html"},
        )
        self.assertEqual(out, "Hello, V!")

    def test_filter_expression_in_kwarg_value(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/greeting.html" with name=name|upper %}',
            {"name": "lower"},
        )
        self.assertEqual(out, "Hello, LOWER!")

    def test_request_is_forwarded_to_fragment(self):
        request = RequestFactory().get("/some/path/")
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/show_request.html" %}',
            {"request": request},
        )
        self.assertEqual(out, "Path: /some/path/")

    def test_render_without_with_or_as(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/greeting.html" %}',
            {"name": "Eve"},
        )
        self.assertEqual(out, "Hello, Eve!")

    def test_as_without_with_captures_into_variable(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/greeting.html" as g %}'
            '[{{ g }}]',
            {"name": "Z"},
        )
        self.assertEqual(out, "[Hello, Z!]")

    def test_missing_template_name_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            Template('{% load render_fragment_tags %}{% render_fragment %}')

    def test_with_without_args_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            Template(
                '{% load render_fragment_tags %}'
                '{% render_fragment "fragments/greeting.html" with %}'
            )

    def test_malformed_kwarg_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            Template(
                '{% load render_fragment_tags %}'
                '{% render_fragment "fragments/greeting.html" with foo %}'
            )

    def test_kwargs_without_with_keyword_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            Template(
                '{% load render_fragment_tags %}'
                '{% render_fragment "fragments/greeting.html" name="V" %}'
            )

    def test_as_without_varname_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            Template(
                '{% load render_fragment_tags %}'
                '{% render_fragment "fragments/greeting.html" as %}'
            )

    def test_only_isolates_from_parent_context(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/context_inherit.html" with item="X" only %}',
            {"user": SimpleNamespace(name="Alice")},
        )
        self.assertEqual(out, "User: , Item: X")

    def test_only_without_kwargs_yields_empty_context(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/greeting.html" only %}',
            {"name": "Parent"},
        )
        self.assertEqual(out, "Hello, !")

    def test_only_does_not_forward_request(self):
        request = RequestFactory().get("/some/path/")
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/show_request.html" only %}',
            {"request": request},
        )
        self.assertEqual(out, "Path: ")

    def test_only_with_kwargs_uses_only_those_values(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/greeting.html" with name="Pure" only %}',
            {"name": "Parent"},
        )
        self.assertEqual(out, "Hello, Pure!")

    def test_only_with_as_captures_into_variable(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/greeting.html" with name="Pure" only as g %}'
            'before|{{ g }}|after',
            {"name": "Parent"},
        )
        self.assertEqual(out, "before|Hello, Pure!|after")

    def test_only_without_with_and_with_as_captures(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/greeting.html" only as g %}'
            '[{{ g }}]',
            {"name": "Parent"},
        )
        self.assertEqual(out, "[Hello, !]")

    def test_only_supports_extends_inside_isolated_fragment(self):
        out = _render(
            '{% load render_fragment_tags %}'
            '{% render_fragment "fragments/card.html" with title="T" body="B" only %}'
        )
        self.assertIn('<div class="card">', out)
        self.assertIn('<div class="card-header">T</div>', out)
        self.assertIn('<div class="card-body">B</div>', out)

    def test_only_before_with_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            Template(
                '{% load render_fragment_tags %}'
                '{% render_fragment "fragments/greeting.html" only with name="X" %}'
            )

    def test_only_between_with_and_kwargs_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            Template(
                '{% load render_fragment_tags %}'
                '{% render_fragment "fragments/greeting.html" with only name="X" %}'
            )

