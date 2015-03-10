# -*- coding: utf-8 -*-

from taiga.requestmaker import RequestMaker
from taiga.models.base import InstanceResource, ListResource, SearchableList
import unittest
from mock import patch
import datetime


class Fake(InstanceResource):

    endpoint = 'fakes'

    allowed_params = ['param1', 'param2']

    repr_attribute = 'param1'

    def my_method(self):
        response = self.requester.get('/users/{id}/starred', id=self.id)
        return projects.Projects.parse(response.json(), self.requester)


class Fakes(ListResource):

    instance = Fake


class TestModelBase(unittest.TestCase):

    def test_encoding(self):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        param2 = {
            'list' : [u'Caf\xe9 project', 'Andrea'],
            'dict' : {
                'el1' : 'Andrea',
                'el2' : u'Caf\xe9 project'
            }
        }
        fake = Fake(rm, id=1, param1=u'Caf\xe9 project', param2=param2)
        self.assertEqual(fake.param1, 'Café project')
        self.assertEqual(fake.param2['list'][0], 'Café project')
        self.assertEqual(fake.param2['dict']['el2'], 'Café project')

    @patch('taiga.requestmaker.RequestMaker.put')
    def test_call_model_base_update(self, mock_requestmaker_put):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fake = Fake(rm, id=1, param1='one', param2='two')
        fake.update()
        mock_requestmaker_put.assert_called_once_with('/{endpoint}/{id}', endpoint='fakes',
            id=1, payload=fake.to_dict())

    @patch('taiga.requestmaker.RequestMaker.delete')
    def test_call_model_base_delete(self, mock_requestmaker_delete):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fake = Fake(rm, id=1, param1='one', param2='two')
        fake.delete()
        mock_requestmaker_delete.assert_called_once_with('/{endpoint}/{id}', endpoint='fakes', id=1)

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_call_model_base_get_element(self, mock_requestmaker_get):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fakes = Fakes(rm)
        fakes.get(1)
        mock_requestmaker_get.assert_called_once_with('/{endpoint}/{id}', endpoint='fakes', id=1)

    @patch('taiga.requestmaker.RequestMaker.delete')
    def test_call_model_base_delete_element(self, mock_requestmaker_delete):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fake = Fake(rm, id=1, param1='one', param2='two')
        fake.delete()
        mock_requestmaker_delete.assert_called_once_with('/{endpoint}/{id}', endpoint='fakes', id=1)

    @patch('taiga.requestmaker.RequestMaker.delete')
    def test_call_model_base_delete_element_from_list(self, mock_requestmaker_delete):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fakes = Fakes(rm)
        fakes.delete(1)
        mock_requestmaker_delete.assert_called_once_with('/{endpoint}/{id}', endpoint='fakes', id=1)

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_call_model_base_list_elements(self, mock_requestmaker_get):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fakes = Fakes(rm)
        fakes.list()
        mock_requestmaker_get.assert_called_with('fakes',  query={})
        fakes.list(project_id=1)
        mock_requestmaker_get.assert_called_with('fakes', query={'project_id':1})

    def test_to_dict_method(self):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fake = Fake(rm, id=1, param1='one', param2='two', param3='three')
        expected_dict = {'param1':'one', 'param2':'two'}
        self.assertEqual(len(fake.to_dict()), 2)
        self.assertEqual(fake.to_dict(), expected_dict)

    def test_searchable_list_filter(self):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fake1 = Fake(rm, id=1, param1='one', param2='a')
        fake2 = Fake(rm, id=1, param1='one', param2='b')
        fake3 = Fake(rm, id=1, param1='two', param2='c')
        searchable_list = SearchableList()
        searchable_list.append(fake1)
        searchable_list.append(fake2)
        searchable_list.append(fake3)
        self.assertEqual(len(searchable_list.filter(param1='one')), 2)
        self.assertEqual(len(searchable_list.filter(param1='notexists')), 0)
        self.assertEqual(len(searchable_list.filter(param1='one', param2='a')), 1)
        self.assertEqual(len(searchable_list.filter()), 3)

    def test_searchable_list_get(self):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fake1 = Fake(rm, id=1, param1='one', param2='a')
        fake2 = Fake(rm, id=1, param1='one', param2='b')
        fake3 = Fake(rm, id=1, param1='two', param2='c')
        searchable_list = SearchableList()
        searchable_list.append(fake1)
        searchable_list.append(fake2)
        searchable_list.append(fake3)
        self.assertTrue(searchable_list.get(param1='one'))
        self.assertFalse(searchable_list.get(param1='notexists'), 0)
        self.assertTrue(searchable_list.get(param1='one', param2='a'), 1)
        self.assertTrue(searchable_list.get())

    @patch('taiga.requestmaker.RequestMaker.put')
    def test_call_model_base_update(self, mock_requestmaker_put):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fake = Fake(rm, id=1, param1='one', param2='two')
        fake.update()
        mock_requestmaker_put.assert_called_once_with('/{endpoint}/{id}', endpoint='fakes',
            id=1, payload=fake.to_dict())

    @patch('taiga.requestmaker.RequestMaker.put')
    def test_datetime_parsing(self, mock_requestmaker_put):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fake = Fake(
            rm, id=1,
            created_date='2015-02-10T17:55:05+0000',
            modified_date='2015-02-10T17:55:05+0000'
        )
        self.assertTrue(isinstance(fake.created_date, datetime.datetime))
        self.assertTrue(isinstance(fake.modified_date, datetime.datetime))

        fake = Fake(
            rm, id=1,
            created_date='2015-02-10T17:55:0',
            modified_date='2015-02-10T17:55:05+0000'
        )
        self.assertFalse(isinstance(fake.created_date, datetime.datetime))
        self.assertTrue(isinstance(fake.modified_date, datetime.datetime))

    def test_repr(self):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        fake = Fake(rm, id=1, param1='one', param2='two', param3='three')
        rep = fake._rp()
        self.assertEqual(rep, 'one')
        self.assertEqual(fake._rp(), str(fake))
        fake.repr_attribute = 'notexisting'
        rep = fake._rp()
        self.assertEqual(rep, '{0}({1})'.format(fake.__class__.__name__, fake.id))
