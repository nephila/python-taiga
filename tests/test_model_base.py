import datetime
import json
import unittest
from unittest.mock import patch

from taiga.models import Projects
from taiga.models.base import InstanceResource, ListResource, SearchableList
from taiga.requestmaker import RequestMaker

from .tools import MockResponse, create_mock_json


class Fake(InstanceResource):
    endpoint = "fakes"

    allowed_params = ["param1", "param2"]

    repr_attribute = "param1"

    def my_method(self):
        response = self.requester.get("/users/{id}/starred", id=self.id)
        return Projects.parse(response.json(), self.requester)


class Fakes(ListResource):
    instance = Fake


class FakeHeaders(dict):
    sequence = []
    counter = -1

    def __init__(self, sequence=None, *args, **kwargs):
        self.sequence = sequence or []
        self.counter = -1
        super().__init__(*args, **kwargs)

    def get(self, k, d=None):
        self.counter += 1
        return self.sequence[self.counter]


class TestModelBase(unittest.TestCase):
    def test_encoding(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        param2 = {"list": ["Caf\xe9 project", "Andrea"], "dict": {"el1": "Andrea", "el2": "Caf\xe9 project"}}
        fake = Fake(rm, id=1, param1="Caf\xe9 project", param2=param2)
        self.assertEqual(fake.param1, "Café project")
        self.assertEqual(fake.param2["list"][0], "Café project")
        self.assertEqual(fake.param2["dict"]["el2"], "Café project")

    @patch("taiga.requestmaker.RequestMaker.put")
    def test_call_model_base_update(self, mock_requestmaker_put):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.update()
        mock_requestmaker_put.assert_called_once_with(
            "/{endpoint}/{id}", endpoint="fakes", id=1, payload=fake.to_dict()
        )

    @patch("taiga.requestmaker.RequestMaker.put")
    def test_call_model_base_update_with_params(self, mock_requestmaker_put):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.update(comment="comment")
        dict_res = fake.to_dict()
        dict_res["comment"] = "comment"
        mock_requestmaker_put.assert_called_once_with("/{endpoint}/{id}", endpoint="fakes", id=1, payload=dict_res)

    @patch("taiga.requestmaker.RequestMaker.put")
    def test_call_model_base_update_with_version(self, mock_requestmaker_put):
        mock_requestmaker_put.return_value = MockResponse(200, '{"version": 2}')
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.update()
        mock_requestmaker_put.assert_called_once_with(
            "/{endpoint}/{id}", endpoint="fakes", id=1, payload=fake.to_dict()
        )
        self.assertEqual(fake.version, 2)

    @patch("taiga.requestmaker.RequestMaker.patch")
    def test_call_model_base_patch(self, mock_requestmaker_patch):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.patch(["param1"])
        mock_requestmaker_patch.assert_called_once_with(
            "/{endpoint}/{id}", endpoint="fakes", id=1, payload={"param1": "one"}
        )

    @patch("taiga.requestmaker.RequestMaker.patch")
    def test_call_model_base_patch_with_params(self, mock_requestmaker_patch):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.patch(["param1"], comment="comment")
        dict_res = fake.to_dict()
        dict_res["comment"] = "comment"
        mock_requestmaker_patch.assert_called_once_with(
            "/{endpoint}/{id}", endpoint="fakes", id=1, payload={"param1": "one", "comment": "comment"}
        )

    @patch("taiga.requestmaker.RequestMaker.patch")
    def test_call_model_base_patch_with_version(self, mock_requestmaker_patch):
        mock_requestmaker_patch.return_value = MockResponse(200, '{"version": 2}')
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.patch(["param1"], version=1)
        mock_requestmaker_patch.assert_called_once_with(
            "/{endpoint}/{id}", endpoint="fakes", id=1, payload={"param1": "one", "version": 1}
        )
        self.assertEqual(fake.version, 2)

    @patch("taiga.requestmaker.RequestMaker.delete")
    def test_call_model_base_delete(self, mock_requestmaker_delete):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.delete()
        mock_requestmaker_delete.assert_called_once_with("/{endpoint}/{id}", endpoint="fakes", id=1, query=None)

    @patch("taiga.requestmaker.RequestMaker.delete")
    def test_call_model_base_delete_with_query(self, mock_requestmaker_delete):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.delete(2)
        mock_requestmaker_delete.assert_called_once_with("/{endpoint}/{id}", endpoint="fakes", id=1, query=2)

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_call_model_base_get_element(self, mock_requestmaker_get):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fakes = Fakes(rm)
        fakes.get(1)
        mock_requestmaker_get.assert_called_once_with("/{endpoint}/{id}", endpoint="fakes", id=1)

    @patch("taiga.requestmaker.RequestMaker.delete")
    def test_call_model_base_delete_element(self, mock_requestmaker_delete):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.delete()
        mock_requestmaker_delete.assert_called_once_with("/{endpoint}/{id}", endpoint="fakes", id=1, query=None)

    @patch("taiga.requestmaker.RequestMaker.delete")
    def test_call_model_base_delete_element_with_query(self, mock_requestmaker_delete):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.delete(1)
        mock_requestmaker_delete.assert_called_once_with("/{endpoint}/{id}", endpoint="fakes", id=1, query=1)

    @patch("taiga.requestmaker.RequestMaker.delete")
    def test_call_model_base_delete_element_from_list(self, mock_requestmaker_delete):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fakes = Fakes(rm)
        fakes.delete(1)
        mock_requestmaker_delete.assert_called_once_with("/{endpoint}/{id}", endpoint="fakes", id=1, query=None)

    @patch("taiga.requestmaker.RequestMaker.delete")
    def test_call_model_base_delete_element_from_list_with_query(self, mock_requestmaker_delete):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fakes = Fakes(rm)
        fakes.delete(1, 2)
        mock_requestmaker_delete.assert_called_once_with("/{endpoint}/{id}", endpoint="fakes", id=1, query=2)

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_call_model_base_list_elements(self, mock_requestmaker_get):
        js_list = json.loads(create_mock_json("tests/resources/fakes_list_success.json"))
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fakes = Fakes(rm)

        data = json.dumps(js_list)
        mock_requestmaker_get.return_value = MockResponse(200, data)
        f_list = fakes.list()
        mock_requestmaker_get.assert_called_with("fakes", query={}, paginate=True)
        self.assertEqual(len(f_list), 9)

        data = json.dumps(js_list[0])
        mock_requestmaker_get.return_value = MockResponse(200, data)
        f_list = fakes.list(id=1)
        mock_requestmaker_get.assert_called_with("fakes", query={"id": 1}, paginate=True)
        self.assertEqual(len(f_list), 1)

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_call_model_base_list_page_size(self, mock_requestmaker_get):
        js_list = json.loads(create_mock_json("tests/resources/fakes_list_success.json"))
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fakes = Fakes(rm)

        data = json.dumps(js_list)
        mock_requestmaker_get.return_value = MockResponse(
            200, data, FakeHeaders([True, True, False], **{"X-Pagination-Next": True})
        )
        f_list = fakes.list(page_size=2)
        mock_requestmaker_get.assert_called_with("fakes", query={"page": 3, "page_size": 2})
        self.assertEqual(len(f_list), 27)

        data = json.dumps(js_list)
        mock_requestmaker_get.return_value = MockResponse(200, data)
        f_list = fakes.list(page_size="wrong")
        mock_requestmaker_get.assert_called_with("fakes", query={"page_size": 100}, paginate=True)
        self.assertEqual(len(f_list), 9)

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_call_model_base_list_elements_no_paginate(self, mock_requestmaker_get):
        js_list = json.loads(create_mock_json("tests/resources/fakes_list_success.json"))
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fakes = Fakes(rm)

        data = json.dumps(js_list)
        mock_requestmaker_get.return_value = MockResponse(200, data)
        f_list = fakes.list(pagination=False)
        mock_requestmaker_get.assert_called_with("fakes", query={}, paginate=False)
        self.assertEqual(len(f_list), 9)

        data = json.dumps(js_list[0])
        mock_requestmaker_get.return_value = MockResponse(200, data)
        f_list = fakes.list(id=1, pagination=False)
        mock_requestmaker_get.assert_called_with("fakes", query={"id": 1}, paginate=False)
        self.assertEqual(len(f_list), 1)

    @patch("taiga.requestmaker.requests.get")
    def test_call_model_base_list_elements_no_paginate_check_requests(self, mock_requestmaker_get):
        js_list = json.loads(create_mock_json("tests/resources/fakes_list_success.json"))
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fakes = Fakes(rm)

        data = json.dumps(js_list)
        mock_requestmaker_get.return_value = MockResponse(200, data)
        f_list = fakes.list(pagination=False)
        mock_requestmaker_get.assert_called_with(
            "fakehost/api/v1/fakes",
            verify=True,
            params={},
            headers={
                "x-disable-pagination": "True",
                "Content-type": "application/json",
                "Authorization": "Bearer faketoken",
            },
        )
        self.assertEqual(len(f_list), 9)

    @patch("taiga.requestmaker.requests.get")
    def test_call_model_base_list_elements_paginate_check_requests(self, mock_requestmaker_get):
        js_list = json.loads(create_mock_json("tests/resources/fakes_list_success.json"))
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fakes = Fakes(rm)

        data = json.dumps(js_list)
        mock_requestmaker_get.return_value = MockResponse(200, data)
        f_list = fakes.list()
        mock_requestmaker_get.assert_called_with(
            "fakehost/api/v1/fakes",
            verify=True,
            params={},
            headers={
                "x-lazy-pagination": "True",
                "Content-type": "application/json",
                "Authorization": "Bearer faketoken",
            },
        )
        self.assertEqual(len(f_list), 9)

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_call_model_base_list_elements_single_page(self, mock_requestmaker_get):
        js_list = json.loads(create_mock_json("tests/resources/fakes_list_success.json"))
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fakes = Fakes(rm)

        data = json.dumps(js_list[:5])
        mock_requestmaker_get.return_value = MockResponse(200, data)
        f_list = fakes.list(page_size=5, page=1)
        self.assertEqual(len(f_list), 5)
        mock_requestmaker_get.assert_called_with("fakes", query={"page_size": 5, "page": 1}, paginate=True)

        data = json.dumps(js_list[5:])
        mock_requestmaker_get.return_value = MockResponse(200, data)
        f_list = fakes.list(page_size=5, page=2)
        self.assertEqual(len(f_list), 4)
        mock_requestmaker_get.assert_called_with("fakes", query={"page_size": 5, "page": 2}, paginate=True)

    def test_to_dict_method(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two", param3="three")
        expected_dict = {"param1": "one", "param2": "two"}
        self.assertEqual(len(fake.to_dict()), 2)
        self.assertEqual(fake.to_dict(), expected_dict)

    def test_searchable_list_filter(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake1 = Fake(rm, id=1, param1="one", param2="a")
        fake2 = Fake(rm, id=1, param1="one", param2="b")
        fake3 = Fake(rm, id=1, param1="two", param2="c")
        searchable_list = SearchableList()
        searchable_list.append(fake1)
        searchable_list.append(fake2)
        searchable_list.append(fake3)
        self.assertEqual(len(searchable_list.filter(param1="one")), 2)
        self.assertEqual(len(searchable_list.filter(param1="notexists")), 0)
        self.assertEqual(len(searchable_list.filter(param1="one", param2="a")), 1)
        self.assertEqual(len(searchable_list.filter()), 3)

    def test_searchable_list_get(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake1 = Fake(rm, id=1, param1="one", param2="a")
        fake2 = Fake(rm, id=1, param1="one", param2="b")
        fake3 = Fake(rm, id=1, param1="two", param2="c")
        searchable_list = SearchableList()
        searchable_list.append(fake1)
        searchable_list.append(fake2)
        searchable_list.append(fake3)
        self.assertTrue(searchable_list.get(param1="one"))
        self.assertFalse(searchable_list.get(param1="notexists"), 0)
        self.assertTrue(searchable_list.get(param1="one", param2="a"), 1)
        self.assertTrue(searchable_list.get())

    @patch("taiga.requestmaker.RequestMaker.put")
    def test_call_model_base_update_2(self, mock_requestmaker_put):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two")
        fake.update()
        mock_requestmaker_put.assert_called_once_with(
            "/{endpoint}/{id}", endpoint="fakes", id=1, payload=fake.to_dict()
        )

    @patch("taiga.requestmaker.RequestMaker.put")
    def test_datetime_parsing(self, mock_requestmaker_put):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, created_date="2015-02-10T17:55:05+0000", modified_date="2015-02-10T17:55:05+0000")
        self.assertTrue(isinstance(fake.created_date, datetime.datetime))
        self.assertTrue(isinstance(fake.modified_date, datetime.datetime))

        fake = Fake(rm, id=1, created_date="2015-02-10T17:55:0", modified_date="2015-02-10T17:55:05+0000")
        self.assertFalse(isinstance(fake.created_date, datetime.datetime))
        self.assertTrue(isinstance(fake.modified_date, datetime.datetime))

    def test_repr(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        fake = Fake(rm, id=1, param1="one", param2="two", param3="three")
        rep = fake._rp()
        self.assertEqual(rep, "one")
        self.assertEqual(fake._rp(), str(fake))
        fake.repr_attribute = "notexisting"
        rep = fake._rp()
        self.assertEqual(rep, "{}({})".format(fake.__class__.__name__, fake.id))
