import unittest
from unittest.mock import patch

from taiga.models import Webhook, Webhooks
from taiga.requestmaker import RequestMaker


class TestWebhooks(unittest.TestCase):
    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_webhook(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = Webhook(rm)
        Webhooks(rm).create(1, "Webhook-Name", "Webhook-Url", "Webhook-Key")
        mock_new_resource.assert_called_with(
            payload={"project": 1, "name": "Webhook-Name", "url": "Webhook-Url", "key": "Webhook-Key"}
        )
