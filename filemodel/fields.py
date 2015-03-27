from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Field(object):
    """
    Field class
    """
    def __init__(self, verbose_name=None):
        self.verbose_name = verbose_name

    def __str__(self):
        """ Return "app_label.model_label.field_name". """
        model = self.model
        app = model._meta.app_label
        return '%s.%s.%s' % (app, model._meta.object_name, self.name)