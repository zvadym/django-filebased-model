How it use
==========

Create model example 
--------------------

```python 
class SharedFile(filemodel.Model):
    root_path = settings.EMPLOYEES_SHARE_PATH
    create_dt = filemodel.Field('Created date')
    size = filemodel.Field('Size')

    class Meta(object):
        verbose_name = 'File'
        verbose_name_plural = 'My Files'

    def __init__(self, *args, **kwargs):
        super(SharedFile, self).__init__(*args, **kwargs)
        self.create_dt = time.ctime(os.path.getctime(self.full_path))
        self.size = os.stat(self.full_path).st_size

    def get_url(self):
        return reverse('documents_my_files_detail', args=(self.pk,))

    def has_permissions(self, employee):
        return self.related_path.startswith(employee.username)
```

Use example
------------

```python
class MyFilesListView(ListView):
    def on_dispatch(self):
        super(MyFilesListView, self).on_dispatch()
        self.files = SharedFile.objects.directory(self.request.user.username, include_sub_directories=False).all()
```

