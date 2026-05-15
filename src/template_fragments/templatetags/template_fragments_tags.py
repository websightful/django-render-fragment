from django import template
from django.template.base import token_kwargs
from django.template.loader import render_to_string

register = template.Library()


class RenderFragmentNode(template.Node):
    """Render a separate template, inheriting the current context.

    The included template is rendered through ``render_to_string`` so it can
    use ``{% extends %}`` to compose with a base layout (for example, an HTML
    component built on top of a generic card or form-field base template).

    When ``isolated`` is true the fragment is rendered with only the explicit
    keyword arguments visible; the parent context and the request are not
    forwarded. This mirrors the ``only`` modifier of Django's ``{% include %}``
    and makes the fragment behave like a pure function of its inputs, which is
    the right default for reusable HTML components.
    """

    def __init__(self, template_name, extra_context, asvar=None, isolated=False):
        self.template_name = template_name
        self.extra_context = extra_context
        self.asvar = asvar
        self.isolated = isolated

    def render(self, context):
        template_name = self.template_name.resolve(context)

        values = {
            name: var.resolve(context) for name, var in self.extra_context.items()
        }

        if self.isolated:
            fragment_context = values
            request = None
        else:
            fragment_context = context.flatten()
            fragment_context.update(values)
            # The request is forwarded so that context processors and tags
            # such as {% csrf_token %} keep working inside the fragment.
            request = context.get("request")

        rendered = render_to_string(
            template_name,
            context=fragment_context,
            request=request,
        )

        if self.asvar:
            context[self.asvar] = rendered
            return ""
        return rendered


@register.tag(name="render_fragment")
def do_render_fragment(parser, token):
    """Parse ``{% render_fragment "name.html" [with k=v ...] [only] [as varname] %}``.

    The template name may be any expression (literal or variable). Keyword
    arguments after ``with`` are layered on top of the current context. The
    ``only`` modifier renders the fragment in isolation, with just the explicit
    keyword arguments visible. When ``as varname`` is given, the rendered
    output is stored in the context under ``varname`` instead of being written
    out in place.
    """
    bits = token.split_contents()
    tag_name = bits[0]

    if len(bits) < 2:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' tag requires at least one argument: the template name."
        )

    template_name = parser.compile_filter(bits[1])
    remaining = bits[2:]

    asvar = None
    if len(remaining) >= 2 and remaining[-2] == "as":
        asvar = remaining[-1]
        remaining = remaining[:-2]
    elif remaining and remaining[-1] == "as":
        raise template.TemplateSyntaxError(
            f"'{tag_name}' expected a variable name after 'as'."
        )

    isolated = False
    if remaining and remaining[-1] == "only":
        isolated = True
        remaining = remaining[:-1]

    extra_context = {}
    if remaining:
        if remaining[0] != "with":
            raise template.TemplateSyntaxError(
                f"'{tag_name}' expected 'with' before keyword arguments, "
                f"got '{remaining[0]}'."
            )
        kwarg_bits = remaining[1:]
        if not kwarg_bits:
            raise template.TemplateSyntaxError(
                f"'{tag_name}' expected at least one 'name=value' pair after 'with'."
            )
        # 'only' must come after the kwargs, never inside them.
        if "only" in kwarg_bits:
            raise template.TemplateSyntaxError(
                f"'{tag_name}' 'only' must appear after all 'with' arguments."
            )
        extra_context = token_kwargs(kwarg_bits, parser, support_legacy=False)
        if not extra_context or kwarg_bits:
            raise template.TemplateSyntaxError(
                f"'{tag_name}' arguments after 'with' must be in 'name=value' form."
            )

    return RenderFragmentNode(template_name, extra_context, asvar, isolated)
