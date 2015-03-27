import os


class FileQuerySet(object):

    def __init__(self, manager, related_path='', include_sub_directories=True):
        self.include_sub_directories = include_sub_directories
        self.related_path = related_path
        self.model = manager.model
        self.qs = self.get_directory_files(related_path)

    def __iter__(self):
        return iter(self.qs)

    def __len__(self):
        return len(self.qs)

    def __getitem__(self, i):
        return self.qs[i]

    def get_directory_files(self, path):
        full_path = self.get_full_path(path)
        files = []
        for obj_name in os.listdir(full_path):
            full_obj_path = os.path.join(full_path, obj_name)
            related_obj_path = os.path.join(path, obj_name)

            if os.path.isfile(full_obj_path):
                files.append(self.model(related_path=related_obj_path))
            elif os.path.isdir(full_obj_path) and self.include_sub_directories:
                files.extend(self.get_directory_files(related_obj_path))

        return files

    def get_full_path(self, path=''):
        path = os.path.join(self.model.root_path, path)
        if not os.path.isdir(path):
            raise ValueError
        return path

    def count(self):
        return len(self)

    def delete(self):
        for obj in self.qs:
            obj.delete()
        return True

    def get(self, *args, **kwargs):
        pk = kwargs.get('pk', None) or args[0]

        for obj in self.qs:
            if obj.id == pk:
                return obj
        raise ValueError('File not found')

    def all(self):
        return self

    def filter(self, *args, **kwargs):
        raise NotImplementedError


class FileManager(object):
    model = None

    def __init__(self, model_class):
        self.model = model_class

    def get_queryset(self, related_path='', include_sub_directories=True):
        return FileQuerySet(manager=self, related_path=related_path, include_sub_directories=include_sub_directories)

    def directory(self, path='', include_sub_directories=True):
        """
        Get qs for given path
        """
        return self.get_queryset(related_path=path, include_sub_directories=include_sub_directories)

    def get(self, *args, **kwargs):
        return self.get_queryset().get(*args, **kwargs)

    def all(self):
        return self.get_queryset().all()

    def filter(self, *args, **kwargs):
        return self.get_queryset().filter(*args, **kwargs)

