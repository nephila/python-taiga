import re


class SearchableList(list):
    def get(self, **query):
        for obj in self:
            ok_obj = True
            for key, value in query.items():
                if key not in obj.__dict__ or obj.__dict__[key] != value:
                    ok_obj = False
            if ok_obj:
                return obj

    def filter(self, **query):  # noqa: A003
        result_objs = []
        for obj in self:
            ok_obj = True
            for key, value in query.items():
                if key not in obj.__dict__ or obj.__dict__[key] != value:
                    ok_obj = False
            if ok_obj:
                result_objs.append(obj)
        return result_objs


class Resource:
    def __init__(self, requester):
        self.requester = requester


class ListResource(Resource):
    """ListResource model

    Base class for methods that operates on a list of resources (:py:meth:`list`, :py:meth:`get`, :py:meth:`delete`).

    :param requester: :class:`Requester` instance
    """

    def list(self, pagination=True, page_size=None, page=None, **queryparams):  # noqa: A003
        """
        Retrieves a list of objects.

        By default uses local cache and remote pagination

        If pagination is used and no page is requested (the default), all the
        remote objects are retrieved and appended in a single list.

        If pagination is disabled, all the objects are fetched from the
        endpoint and returned. This may trigger some parsing error if the
        result set is very large.

        :param pagination: Use pagination (default: `True`)
        :param page_size: Size of the pagination page (default: `100`).
                          Any non numeric value will be casted to the
                          default value
        :param page: Page number to retrieve (default: `None`). Ignored if
                     `pagination` is `False`
        :param queryparams: Additional filter parameters as accepted by the
                            remote API
        :return: <SearchableList>
        """
        if page_size and pagination:
            try:
                page_size = int(page_size)
            except (ValueError, TypeError):
                page_size = 100
            queryparams["page_size"] = page_size
        if page and pagination:
            queryparams["page"] = page
        result = self.requester.get(self.instance.endpoint, query=queryparams, paginate=pagination)
        objects = SearchableList()
        objects.extend(self.parse_list(result.json()))
        if result.headers.get("X-Pagination-Next", False) and not page:
            next_page = 2
        else:
            next_page = None
        while next_page:
            pageparams = queryparams.copy()
            pageparams["page"] = next_page
            result = self.requester.get(
                self.instance.endpoint,
                query=pageparams,
            )
            objects.extend(self.parse_list(result.json()))
            if result.headers.get("X-Pagination-Next", False):
                next_page += 1
            else:
                next_page = None
        return objects

    def get(self, resource_id):
        response = self.requester.get("/{endpoint}/{id}", endpoint=self.instance.endpoint, id=resource_id)
        return self.instance.parse(self.requester, response.json())

    def delete(self, resource_id, query=None):
        self.requester.delete("/{endpoint}/{id}", endpoint=self.instance.endpoint, id=resource_id, query=query)
        return self

    def _new_resource(self, **attrs):
        response = self.requester.post(self.instance.endpoint, **attrs)
        return self.instance.parse(self.requester, response.json())

    @classmethod
    def parse(cls, requester, entries):
        """Parse a JSON array into a list of model instances."""
        result_entries = SearchableList()
        if entries:
            for entry in entries:
                result_entries.append(cls.instance.parse(requester, entry))
        return result_entries

    def parse_list(self, entries):
        """Parse a JSON array into a list of model instances."""
        result_entries = SearchableList()
        if entries:
            for entry in entries:
                result_entries.append(self.instance.parse(self.requester, entry))
        return result_entries


class InstanceResource(Resource):
    """InstanceResource model

    Base class for methods that operates on a single resource (:py:meth:`update`, :py:meth:`patch`, :py:meth:`delete`).

    :param requester: :class:`Requester` instance
    :param params: :various parameters
    """

    endpoint = ""

    parser = {}

    allowed_params = []

    repr_attribute = "name"

    def __init__(self, requester, **params):
        import dateutil.parser

        self.requester = requester
        for key, value in params.items():
            if key in ["created_date", "modified_date"]:
                if re.compile(r"\d+-\d+-\d+T\d+:\d+:\d+\+0000").match(value):
                    d = dateutil.parser.parse(value)
                    value = d.astimezone(dateutil.tz.tzlocal())
            setattr(self, key, value)

    def update(self, **args):
        """
        Update the current :class:`InstanceResource`
        """
        self_dict = self.to_dict()
        if args:
            self_dict = dict(list(self_dict.items()) + list(args.items()))
        response = self.requester.put("/{endpoint}/{id}", endpoint=self.endpoint, id=self.id, payload=self_dict)
        obj_json = response.json()
        if "version" in obj_json:
            self.__dict__["version"] = obj_json["version"]
        return self

    def patch(self, fields, **args):
        """
        Patch the current :class:`InstanceResource`
        """
        self_dict = {key: value for (key, value) in self.to_dict().items() if key in fields}
        if args:
            self_dict = dict(list(self_dict.items()) + list(args.items()))
        response = self.requester.patch("/{endpoint}/{id}", endpoint=self.endpoint, id=self.id, payload=self_dict)
        obj_json = response.json()
        if "version" in obj_json:
            self.__dict__["version"] = obj_json["version"]
        return self

    def delete(self, query=None):
        """
        Delete the current :class:`InstanceResource`
        """
        self.requester.delete("/{endpoint}/{id}", endpoint=self.endpoint, id=self.id, query=query)
        return self

    def to_dict(self):
        """
        Get a dictionary representation of :class:`InstanceResource`
        """
        self_dict = {}
        for key, value in self.__dict__.items():
            if self.allowed_params and key in self.allowed_params:
                self_dict[key] = value
        return self_dict

    @classmethod
    def parse(cls, requester, entry):
        """
        Turns a JSON object into a model instance.
        """
        if not isinstance(entry, dict):
            return entry
        for key_to_parse, cls_to_parse in cls.parser.items():
            if key_to_parse in entry:
                entry[key_to_parse] = cls_to_parse.parse(requester, entry[key_to_parse])
        return cls(requester, **entry)

    def __repr__(self):
        try:
            return "{}({})".format(self.__class__.__name__, self.id)
        except AttributeError:
            return "{}({})".format(self.__class__.__name__, id(self))

    def __str__(self):
        return self._rp()

    def _rp(self):
        attr = getattr(self, self.repr_attribute, None)
        if attr:
            return "{}".format(attr)
        else:
            return repr(self)
