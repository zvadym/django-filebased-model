import os
import copy
import hashlib
from django.apps import apps
from django.db.models.base import ModelBase
from django.utils.encoding import python_2_unicode_compatible

from .manager import FileManager
from .fields import Field


class ModelMeta(ModelBase):
    """
    Metaclass for file models.

    Inherits from models.base.ModelBase to simulate the model behavior.
    Otherwise shortcuts like get_object_or_404() don't work

    """
    def __new__(mcs, name, bases, attrs):
        super_new = type.__new__
        # Ensure initialization is only performed for subclasses of BaseModel
        # (excluding Model class itself).
        parents = [b for b in bases if isinstance(b, ModelMeta)]
        if not parents:
            return super_new(mcs, name, bases, attrs)

        # Collect and move fields to self.fields dict
        fields = {}
        for base in parents:
            for attr_name, attr in base.__dict__.items():
                if not attr_name.startswith('__') and isinstance(attr, Field):
                    fields[attr_name] = attr

        for attr_name, attr in attrs.items():
            if isinstance(attr, Field):
                setattr(attr, 'name', attr_name)
                fields[attr_name] = attr
                del attrs[attr_name]

        # Other data
        meta_attr = attrs.pop('Meta', None)
        module = attrs.pop('__module__')
        app_config = apps.get_containing_app_config(module)

        attrs['fields'] = fields

        new_class = super_new(mcs, name, bases, attrs)

        # Check ROOT_PATH
        assert new_class.root_path, "ROOT path required"

        # Manager
        manager = FileManager(model_class=new_class)
        setattr(new_class, 'objects', manager)
        setattr(new_class, '_default_manager', manager)

        # Meta class
        meta = meta_attr or getattr(new_class, 'Meta', None)
        if not meta:
            class Meta(object):
                pass
            meta = Meta

        meta.get_field = lambda self, field_name: self.model.fields.get(field_name, None)

        if not hasattr(meta, 'verbose_name'):
            setattr(meta, 'verbose_name', name)

        if not hasattr(meta, 'verbose_name_plural'):
            setattr(meta, 'verbose_name_plural', '%ss' % meta.verbose_name)

        meta_obj = meta()
        setattr(meta_obj, 'object_name', name)
        setattr(meta_obj, 'app_label', app_config.label)
        setattr(meta_obj, 'virtual_fields', [])
        setattr(meta_obj, 'concrete_fields', [])
        setattr(meta_obj, 'many_to_many', [])

        setattr(new_class, '_meta', meta_obj)
        return new_class


@python_2_unicode_compatible
class BaseModel(object):
    """
    Tried as much as possible to repeat the implementation of django.db.models.Model
    It makes possible for `frigg` to work with filemodel as with django.db.models.Model
    without any additional hooks
    """
    __metaclass__ = ModelMeta

    related_path = None

    # Root directory
    root_path = None

    # Manager
    objects = None

    # Base Fields
    id = Field('ID')
    full_path = Field()
    name = Field('Name')

    # Link
    pk = id

    DoesNotExist = ValueError

    def __init__(self, related_path, **kwargs):
        # Update Meta class
        setattr(self._meta, 'model', self)

        # Copy fields
        fields = copy.deepcopy(self.fields)
        for field in fields.values():
            setattr(field, 'model', self)
        self.fields = fields

        # Root directory required
        if not self.root_path:
            raise NotImplementedError('Root directory required')

        # Set required fields
        self.related_path = related_path
        full_path = os.path.join(self.root_path, related_path)
        if not os.path.isfile(full_path):
            raise ValueError

        self.full_path = full_path
        self.name = full_path.split('/')[-1]

        # Set ID
        md5 = hashlib.md5()
        md5.update(self.related_path)
        self.pk = self.id = md5.hexdigest()

        # Set field values from kwargs
        for name, value in kwargs.items():
            if name in self.fields:
                setattr(self, name, value)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

    def __str__(self):
        return '%s' % self.name

    def delete(self):
        os.remove(self.full_path)
