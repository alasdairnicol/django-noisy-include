"""
Copied from Django with minor modifications

Copyright (c) Django Software Foundation and individual contributors
(see LICENSE.django)
"""
from django.utils import six

from django.template.loader_tags import construct_relative_path, IncludeNode

from django.template.library import Library
from django.template.base import token_kwargs
from django.template.exceptions import TemplateSyntaxError

register = Library()


class NoisyIncludeNode(IncludeNode):
    def render(self, context):
        """
        Render the specified template and context. Cache the template object
        in render_context to avoid reparsing and loading when used in a for
        loop.
        """
        try:
            template = self.template.resolve(context)
            # Does this quack like a Template?
            if not callable(getattr(template, 'render', None)):
                # If not, we'll try our cache, and get_template()
                template_name = template
                cache = context.render_context.dicts[0].setdefault(self, {})
                template = cache.get(template_name)
                if template is None:
                    template = context.template.engine.get_template(template_name)
                    cache[template_name] = template
            # Use the base.Template of a backends.django.Template.
            elif hasattr(template, 'template'):
                template = template.template
            values = {
                name: var.resolve(context)
                for name, var in six.iteritems(self.extra_context)
            }
            if self.isolated_context:
                return template.render(context.new(values))
            with context.push(**values):
                return template.render(context)
        except Exception:
            raise


@register.tag('include')
def do_include(parser, token):
    """
    Loads a template and renders it with the current context. You can pass
    additional context using keyword arguments.
    Example::
        {% include "foo/some_include" %}
        {% include "foo/some_include" with bar="BAZZ!" baz="BING!" %}
    Use the ``only`` argument to exclude the current context when rendering
    the included template::
        {% include "foo/some_include" only %}
        {% include "foo/some_include" with bar="1" only %}
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "%r tag takes at least one argument: the name of the template to "
            "be included." % bits[0]
        )
    options = {}
    remaining_bits = bits[2:]
    while remaining_bits:
        option = remaining_bits.pop(0)
        if option in options:
            raise TemplateSyntaxError('The %r option was specified more '
                                      'than once.' % option)
        if option == 'with':
            value = token_kwargs(remaining_bits, parser, support_legacy=False)
            if not value:
                raise TemplateSyntaxError('"with" in %r tag needs at least '
                                          'one keyword argument.' % bits[0])
        elif option == 'only':
            value = True
        else:
            raise TemplateSyntaxError('Unknown argument for %r tag: %r.' %
                                      (bits[0], option))
        options[option] = value
    isolated_context = options.get('only', False)
    namemap = options.get('with', {})
    bits[1] = construct_relative_path(parser.origin.template_name, bits[1])
    return NoisyIncludeNode(parser.compile_filter(bits[1]), extra_context=namemap,
                            isolated_context=isolated_context)
