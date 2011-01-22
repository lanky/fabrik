"""
This class when mixed into a form class provides hooks for template designers to 
access individual fields or sets of fields based on various criteria such as field 
name prefix or fields appearing before or after certain fields in the form, while 
still being able to use the as_* form rendering methods against these fields. 

Credits:
--------

Stephen McDonald <steve@jupo.org>

License:
--------

Creative Commons Attribution-Share Alike 3.0 License
http://creativecommons.org/licenses/by-sa/3.0/

When attributing this work, you must maintain the Credits
paragraph above.
"""

from copy import copy
from itertools import dropwhile, takewhile
from re import match
 
from django.utils.datastructures import SortedDict
 

class FormsetForm(object):
    """
    Form mixin that gives template designers greater control over form field 
    rendering while still using the as_* methods. The following methods return 
    a copy of the form with only a subset of fields that can then be rendered
    with as_* methods.
    
    {{ form.PREFIX_fields.as_* }} - fields with a name starting with PREFIX
    {{ form.FIELD_field.as_* }} - a single field with the name FIELD
    {{ form.fields_before_FIELD.as_* }} - fields before the field named FIELD
    {{ form.fields_after_FIELD.as_* }} - fields after the field named FIELD
    {{ form.other_fields.as_* }} - fields not yet accessed as a formset
 
    CSS classes are also added to the rendered fields. These are the lowercase 
    classname of the widget, eg "textinput" or "checkboxinput", and if the field 
    is required the class of "required" is also added.
    """
 
    def _fieldset(self, field_names):
        """
        Return a subset of fields by making a copy of the form containing only 
        the given field names and adding extra CSS classes to the fields.
        """
        fieldset = copy(self)
        if not hasattr(self, "_fields_done"):
            self._fields_done = []
        else:
            # all fieldsets will contain all non-field errors, so for fieldsets
            # other than the first ensure the call to non-field errors does nothing
            fieldset.non_field_errors = lambda *args: None
        field_names = filter(lambda f: f not in self._fields_done, field_names)
        fieldset.fields = SortedDict([(f, self.fields[f]) for f in field_names])
        for field in fieldset.fields.values():
            field.widget.attrs["class"] = field.widget.__class__.__name__.lower()
            if field.required:
                field.widget.attrs["class"] += " required"
        self._fields_done.extend(field_names)
        return fieldset
 
    def __getattr__(self, name):
        """
        Dynamic fieldset caller - matches requested attribute name against 
        pattern for creating the list of field names to use for the fieldset. 
        """
        filters = (
            ("^other_fields$", lambda: 
                self.fields.keys()),
            ("^(\w*)_fields$", lambda name: 
                [f for f in self.fields.keys() if f.startswith(name)]),
            ("^(\w*)_field$", lambda name: 
                [f for f in self.fields.keys() if f == name]),
            ("^fields_before_(\w*)$", lambda name: 
                takewhile(lambda f: f != name, self.fields.keys())),
            ("^fields_after_(\w*)$", lambda name: 
                list(dropwhile(lambda f: f != name, self.fields.keys()))[1:]),
        )
        for filter_exp, filter_func in filters:
            filter_args = match(filter_exp, name)
            if filter_args is not None:
                return self._fieldset(filter_func(*filter_args.groups()))
        raise AttributeError(name)