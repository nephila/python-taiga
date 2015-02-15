import json

class MockResponse():
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

    def json(self):
        return json.loads(self.text)

def create_mock_json(path):
    with open(path) as f:
        return f.read()