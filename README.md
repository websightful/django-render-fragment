# django-render-fragment

[![PyPI version](https://img.shields.io/pypi/v/django-render-fragment)](https://pypi.org/project/django-render-fragment/)
![License](https://img.shields.io/pypi/l/django-render-fragment)
![Python versions](https://img.shields.io/pypi/pyversions/django-render-fragment)

Provides a Django template tag, `render_fragment`, that renders template fragments with full support for `{% extends %}`. It lets you build reusable HTML components — cards, buttons, badges, form fields, list items — on top of shared base templates, the same way regular Django pages do.

Perfect for:

* Reusable UI components (cards, buttons, badges, alerts)
* Form-field wrappers built on a shared base layout
* List or grid item templates rendered inside a loop
* Email and document partials that share a common skeleton
* htmx / hotwire fragments that compose with a base template

## Why Use This?

Django's built-in `{% include %}` tag does not support `{% extends %}` inside the included template, which makes it awkward to build component libraries where each component inherits from a shared base layout.

`render_fragment` renders the target template through `render_to_string`, so `{% extends %}` works exactly the same as it does for any top-level template. You get real HTML components with all of Django's template-inheritance machinery available.

A base layout:

```django
{# components/_base_card.html #}
<div class="card">
  <div class="card-header">{% block card_title %}{% endblock %}</div>
  <div class="card-body">{% block card_body %}{% endblock %}</div>
</div>
```

A component that extends it:

```django
{# components/card.html #}
{% extends "components/_base_card.html" %}

{% block card_title %}{{ title }}{% endblock %}

{% block card_body %}{{ body }}{% endblock %}
```

Used from any page:

```django
{% load render_fragment_tags %}

{% render_fragment "components/card.html" with title="Welcome" body=intro only %}
```

## Design Philosophy

* Minimal — one tag, no surprises
* No external dependencies — pure Django
* Built on `render_to_string` so `{% extends %}` just works
* Explicit isolation via `only`, matching `{% include %}` conventions
* Safe and predictable behavior
* Suitable for reusable Django apps

## Installation

```bash
pip install django-render-fragment
```

## Setup

Add it to your Django project:

```python
INSTALLED_APPS = [
    ...
    "render_fragment",
]
```

## Usage

Load the tag library in any template that needs it:

```django
{% load render_fragment_tags %}
```

### Full syntax

```django
{% render_fragment template_name [with k=v ...] [only] [as varname] %}
```

| Part | Optional | Description |
| --- | --- | --- |
| `template_name` | required | Literal string or a context variable resolving to a template path. |
| `with k=v ...` | optional | Keyword arguments layered on top of the (inherited) context. |
| `only` | optional | Render in isolation: ignore parent context and `request`. |
| `as varname` | optional | Store the rendered output in `varname` instead of writing in place. |

By default the fragment inherits the full parent context plus the current `request`, so context processors and tags such as `{% csrf_token %}` keep working inside the fragment. The `only` modifier turns the fragment into a pure function of its declared inputs.

### Rendering in place

```django
{% render_fragment "components/greeting.html" with name=user.first_name %}
```

### Capturing into a variable

```django
{% render_fragment "components/button.html" with label="Save" variant="primary" as save_btn %}

<form method="post">
    {% csrf_token %}
    ...
    {{ save_btn }}
</form>
```

### Using `{% extends %}` inside the fragment

The fragment is rendered through `render_to_string`, so it can extend any base template:

```django
{# templates/components/_base_card.html #}
<article class="card">
    <header>{% block card_title %}{% endblock %}</header>
    <section>{% block card_body %}{% endblock %}</section>
</article>
```

```django
{# templates/components/product_card.html #}
{% extends "components/_base_card.html" %}

{% block card_title %}{{ product.name }}{% endblock %}

{% block card_body %}{{ product.summary }}{% endblock %}
```

```django
{% for product in products %}
    {% render_fragment "components/product_card.html" with product=product only %}
{% endfor %}
```

### Isolating components with `only`

Without `only`, the fragment sees every variable from the surrounding template. That is convenient for ad-hoc partials but risky for a component library: a card might silently start depending on whichever variables happen to be in scope.

`only` makes the component a pure function of its declared inputs:

```django
{% render_fragment "components/card.html" with title="Hi" body="There" only %}
```

Inside the fragment only `title` and `body` are visible. Neither the parent context nor `request` is forwarded — pass them explicitly when needed:

```django
{% render_fragment "components/comment_form.html" with post=post request=request only %}
```

This is the recommended default for any template you intend to reuse from multiple call sites.

## Multiline support

Set `RENDER_FRAGMENT_MULTILINE_TAGS = True` in your Django settings to support multiline tags like:

```django
{% render_fragment 
  "components/comment_form.html" with 
  post=post 
  request=request 
  only 
%}
```

Note that by setting this, you will be able to use multiple lines for other template tags too.

## Caching fragments

Because `only` makes a fragment depend on exactly the values you pass in, it composes very cleanly with Django's built-in `{% cache %}` tag.

### Caching a self-contained component

```django
{% load cache render_fragment_tags %}

{% cache 600 product_card product.id product.updated_at %}
    {% render_fragment "components/product_card.html" with product=product only %}
{% endcache %}
```

The `vary_on` values (`product.id`, `product.updated_at`) form the cache key, so the cached HTML is invalidated automatically when the product changes. Because the fragment uses `only`, you can be confident that nothing outside `product` affects its output.

### Caching per `request.user`

For fragments that render differently per user (a "save / unsave" button, a personalised greeting, a permission-gated panel), include `request.user.id` in `vary_on`:

```django
{% load cache render_fragment_tags %}

{% cache 300 save_button request.user.id product.id %}
    {% render_fragment "components/save_button.html"
         with product=product user=request.user only %}
{% endcache %}
```

For anonymous users `request.user.id` resolves to `None`, which is a valid and stable cache-key component.

### Caching per language

```django
{% load cache i18n render_fragment_tags %}

{% get_current_language as LANGUAGE_CODE %}
{% cache 3600 hero_banner LANGUAGE_CODE %}
    {% render_fragment "components/hero.html" only %}
{% endcache %}
```

### Tips

* Always pair `{% cache %}` with `only` for reusable components, so the cache key fully captures the fragment's inputs.
* Use `request.user.id` (not `request.user`) in `vary_on` — model instances get stringified into cache keys, which can be expensive or unstable.
* Use a dedicated cache backend (`CACHES['render_fragment']`) and `{% cache ... using="render_fragment" %}` when you want a different eviction policy from the default cache.

## Performance

`render_fragment` is more expensive than `{% include %}` because every call dispatches through `render_to_string`, which builds a fresh context and runs Django's `{% extends %}` machinery for the fragment. That extra work is what makes `{% extends %}`-based components possible in the first place.

The repository ships a benchmark script, `benchmark_performance.py`, that renders the same final HTML with both approaches:

* a document calling `{% render_fragment %}` 25 times against a child template that `{% extends %}` a shared base layout,
* a document calling `{% include %}` 25 times against an equivalent self-contained template.

A representative run (Django 6.0, Python 3.14, CPython on a developer laptop, 200 renders × 5 repeats):

```
{% render_fragment %} + extends   best=2.23 ms   per inclusion ≈ 89 µs
{% include %} (single file)       best=1.50 ms   per inclusion ≈ 60 µs
```

So `render_fragment` costs roughly **1.5× a plain `{% include %}`**, or about **~30 µs of extra overhead per inclusion** on this hardware. Numbers will vary across machines and Django versions — run the script in your environment to get a figure that matches your workload.

### Practical implications

* For a typical page rendering a handful of components, the overhead is in the **tens-of-microseconds-per-component** range and is dominated by everything else the view does (DB queries, serialization, middleware).
* For pages that render the same component **many times per request** (long lists, dashboards, tables), the overhead adds up linearly. In those cases:
  * Wrap each fragment in `{% cache %}` with `only`, as shown above, so repeated requests skip the work entirely.
  * Or, if you do not actually need `{% extends %}` for that particular component, prefer a plain `{% include %}` of a self-contained template — `render_fragment` is meant for components that genuinely benefit from template inheritance.
* The overhead is **per inclusion**, not per render, so caching the surrounding view fragment (or using template-fragment caching) is usually more effective than micro-optimising the components themselves.

## `django-render-fragment` in Production

`django-render-fragment` is used in production at

- [PyBazaar](https://www.pybazaar.com)
- [Make Impact dot org](https://make-impact.org)

## Testing

The package is tested against multiple Django versions using `tox`.

To run tests locally:
```bash
tox
```

## License

MIT License
