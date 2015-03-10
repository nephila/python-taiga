import dateutil.parser
import re
import six


class SearchableList(list):

    def get(self, **query):
        for obj in self:
            ok_obj = True
            for key, value in six.iteritems(query):
                if key not in obj.__dict__ or obj.__dict__[key] != value:
                    ok_obj = False
            if ok_obj:
                return obj

    def filter(self, **query):
        result_objs = []
        for obj in self:
            ok_obj = True
            for key, value in six.iteritems(query):
                if key not in obj.__dict__ or obj.__dict__[key] != value:
                    ok_obj = False
            if ok_obj:
                result_objs.append(obj)
        return result_objs


class Resource(object):

    def __init__(self, requester):
        self.requester = requester


class ListResource(Resource):

    def list(self, **queryparams):
        result = self.requester.get(
            self.instance.endpoint, query=queryparams
        )
        objects = self.parse_list(result.json())
        return objects

    def get(self, resource_id):
        response = self.requester.get(
            '/{endpoint}/{id}',
            endpoint=self.instance.endpoint, id=resource_id
        )
        return self.instance.parse(self.requester, response.json())

    def delete(self, resource_id):
        self.requester.delete(
            '/{endpoint}/{id}',
            endpoint=self.instance.endpoint, id=resource_id
        )
        return self

    def _new_resource(self, **attrs):
        response = self.requester.post(
            self.instance.endpoint, **attrs
        )
        return self.instance.parse(self.requester, response.json())

    @classmethod
    def parse(cls, requester, entries):
        """Parse a JSON array into a list of model instances."""
        result_entries = SearchableList()
        for entry in entries:
            result_entries.append(cls.instance.parse(requester, entry))
        return result_entries

    def parse_list(self, entries):
        """Parse a JSON array into a list of model instances."""
        result_entries = SearchableList()
        for entry in entries:
            result_entries.append(self.instance.parse(self.requester, entry))
        return result_entries


class InstanceResource(Resource):

    endpoint = ''

    parser = {}

    allowed_params = []

    repr_attribute = 'name'

    def __init__(self, requester, **params):
        self.requester = requester
        for key, value in six.iteritems(params):
            if key in ['created_date', 'modified_date']:
                if re.compile('\d+-\d+-\d+T\d+:\d+:\d+\+0000').match(value):
                    d = dateutil.parser.parse(value)
                    value = d.astimezone(dateutil.tz.tzlocal())
            if six.PY2:
                value = self._encode_element(value)
            setattr(self, key, value)

    def _encode_element(self, element):
        if isinstance(element, six.string_types):
            return element.encode('utf-8')
        elif isinstance(element, list):
            for idx, value in enumerate(element):
                element[idx] = self._encode_element(value)
            return element
        elif isinstance(element, dict):
            for key, value in six.iteritems(element):
                element[key] = self._encode_element(value)
            return element
        else:
            return element

    def update(self):
        self.requester.put(
            '/{endpoint}/{id}', endpoint=self.endpoint,
            id=self.id, payload=self.to_dict()
        )
        return self

    def delete(self):
        self.requester.delete(
            '/{endpoint}/{id}', endpoint=self.endpoint,
            id=self.id
        )
        return self

    def to_dict(self):
        self_dict = {}
        for key, value in six.iteritems(self.__dict__):
            if self.allowed_params and key in self.allowed_params:
                self_dict[key] = value
        return self_dict

    @classmethod
    def parse(cls, requester, entry):
        """Parse a JSON object into a model instance."""
        for key_to_parse, cls_to_parse in six.iteritems(cls.parser):
            if key_to_parse in entry:
                entry[key_to_parse] = cls_to_parse.parse(
                    requester, entry[key_to_parse]
                )
        return cls(requester, **entry)

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.id)

    def __str__(self):
        return self._rp()

    def __unicode__(self):
        return self._rp().decode('utf-8')

    def _rp(self):
        attr = getattr(self, self.repr_attribute, None)
        if attr:
            return '{0}'.format(attr)
        else:
            return repr(self)
