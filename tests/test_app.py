import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from flask import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock google.auth.default so it doesn't look for real credentials
with patch('google.auth.default', return_value=(MagicMock(), "test-project-id")):
    # Create a mock Vision client that returns a label for "Mountain"
    mock_vision_client_instance = MagicMock()
    mock_label = MagicMock(description="Mountain")
    mock_vision_client_instance.label_detection.return_value.label_annotations = [mock_label]

    with patch('google.cloud.vision.ImageAnnotatorClient', return_value=mock_vision_client_instance):
        from backend.app import app

class TestAppEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_root_redirect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/index.html', response.location)

    @patch('requests.get')
    def test_get_places_no_region(self, mock_requests):
        response = self.client.get('/places')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "Region is required"})

    @patch('requests.get')
    def test_get_places_with_region(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "name": "Nature Park",
                    "formatted_address": "123 Green St",
                    "photos": [{"photo_reference": "abc123"}]
                },
                {
                    "name": "Forest Reserve",
                    "formatted_address": "456 Leafy Rd"
                }
            ]
        }
        mock_requests.return_value = mock_response

        response = self.client.get('/places?region=Oregon')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], "Nature Park")
        self.assertEqual(data[0]['location'], "123 Green St")
        self.assertEqual(data[0]['photo_reference'], "abc123")
        self.assertEqual(data[1]['name'], "Forest Reserve")
        self.assertEqual(data[1]['location'], "456 Leafy Rd")
        self.assertIsNone(data[1]['photo_reference'])

    def test_get_photo_missing_reference(self):
        response = self.client.get('/photo')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "Missing photo_reference"})

    @patch('requests.get')
    def test_get_photo_success(self, mock_requests):
        mock_response = MagicMock()
        mock_response.content = b'fake_image_data'
        mock_response.headers = {"Content-Type": "image/jpeg"}
        mock_response.raise_for_status = MagicMock()
        mock_requests.return_value = mock_response

        response = self.client.get('/photo?photo_reference=abc123')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'fake_image_data')
        self.assertEqual(response.content_type, "image/jpeg")

    def test_analyze_photo_missing_reference(self):
        response = self.client.post('/analyze', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "Missing photo_reference"})


if __name__ == '__main__':
    unittest.main()