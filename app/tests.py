from app import app
import unittest
import json


class APITestCase(unittest.TestCase):

	def test_healthcheck(self):
		with app.test_client() as client:
			response = client.get('/healthcheck')
		self.assertEqual(response.status_code, 200)

	def test_running(self):
		with app.test_client() as client:
			response = client.get('/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data, bytes('Running!', 'utf-8'))

	def test_load(self):
		with app.test_client() as client:
			response = client.post('/load', 
				headers={"origin":"MY_TEST_DOMAIN"},
				data=json.dumps({
					"session_id": "STOCK_MARKET_TEST_SESSION",
				}), 
				content_type='application/json'
			)
		self.assertEqual(response.status_code, 200, f"Received response:\n{response.text}")
		body = json.loads(response.data.decode('utf8')) if isinstance(response.data, bytes) else json.loads(response.data)
		print(f"Received 'load' response: {body}")

	def test_interview(self):
		with app.test_client() as client:
			response = client.post('/next', 
				headers={"origin":"MY_TEST_DOMAIN"},
				data=json.dumps({
					"user_message": "I can't afford it and the stock market is rigged.",
					"session_id": "STOCK_MARKET_TEST_SESSION",
					"parameters_id": "STOCK_MARKET_PARTICIPATION"
				}), 
				content_type='application/json'
			)
		self.assertEqual(response.status_code, 200, f"Received response:\n{response.text}")
		body = json.loads(response.data.decode('utf8')) if isinstance(response.data, bytes) else json.loads(response.data)
		self.assertIsInstance(body, dict)
		self.assertIn('message', body)
		self.assertIsInstance(body['message'], str)
		print(f"Received response: {body['message']}")


if __name__ == '__main__':
	unittest.main()
