from django import forms
from django.forms import fields, ValidationError
from django.forms.widgets import Textarea, Widget
import jsonschema
from jsonfield.fields import JSONFormField
import json
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

class JSONEditorWidget(Widget):

    template_name = 'django_jsonforms/jsoneditor.html'

    class Media:
        js = ('django_jsonforms/jsoneditor.min.js', 'django_jsonforms/jsoneditor_init.js')

    def __init__(self, schema, options, *args, **kwargs):
        super(JSONEditorWidget, self).__init__(*args, **kwargs)
        self.schema = schema
        self.options = options

    def get_context(self, name, value, attrs):
        context = super(JSONEditorWidget, self).get_context(name, value, attrs)

        if isinstance(self.schema, dict):
            context.update({'schema': json.dumps(self.schema)})
        else:
            context.update({'schema_url': self.schema})

        if isinstance(self.options, dict):
            context.update({'options': json.dumps(self.options)})
        else:
            context.update({'options_url': self.options})

        context['widget']['type'] = 'hidden'
        return context

class JSONSchemaField(JSONFormField):

    def __init__(self, schema, options, *args, **kwargs):
        super(JSONSchemaField, self).__init__(*args, **kwargs)

        self.schema = self.load(schema)

        self.widget = JSONEditorWidget(schema=schema, options=options)

    def load(self, value):
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            if (settings.STATIC_ROOT):
                file_path = os.path.join(settings.STATIC_ROOT, value)
                if os.path.isfile(file_path):
                    static_file = open(file_path, 'r')
                    json_value = json.loads(static_file.read())
                    static_file.close()
                    return json_value
                else:
                    raise FileNotFoundError('File could not be found')
            else:
                raise ImproperlyConfigured('STATIC_ROOT is not set')

    def clean(self, value):
        value = super(JSONSchemaField, self).clean(value)

        try:
            jsonschema.validate(value, self.schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(message=e.message)

        return value

class JSONSchemaForm(forms.Form):

    def __init__(self, schema, options, *args, **kwargs):
        super(JSONSchemaForm, self).__init__(*args, **kwargs)
        self.fields['json'] = JSONSchemaField(schema=schema, options=options)