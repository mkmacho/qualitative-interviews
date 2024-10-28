from app import app
import unittest
import json

SAMPLE_HEADERS = {
    "origin":"https://nhh.eu.qualtrics.com"
}

SAMPLE_FIRST_PAYLOAD = {
	"user_message":"I can't afford it and the stock market is rigged.",
	"first_question":"I am interested in learning more about why you currently do not own any stocks or stock mutual funds. Can you help me understand the main factors or reasons why you are not participating in the stock market?",
	"open_topics":[
		{
			"topic":"Explore the reasons behind the interviewee's choice to avoid the stock market.",
			"length":6
		},
		{
			"topic":"Delve into the perceived barriers or challenges preventing them from participating in the stock market.",
			"length":5
		},
		{
			"topic":"Explore a 'what if' scenario where the interviewee invest in the stock market. What would they do? What would it take to thrive? Probing questions should explore the hypothetical scenario.",
			"length":3
		},
		{
			"topic":"Prove for conditions or changes needed for the interviewee to consider investing in the stock market.",
			"length":2
		}
	],
	"closing_questions":[
		"As we conclude our discussion, are there any perspectives or information you feel we haven't addressed that you'd like to share?",
		"Reflecting on our conversation, what would you identify as the main reason you're not participating in the stock market?"
	],
	"session_id":"TEST_SESSION_ID"
}

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

	def test_interview(self):
		with app.test_client() as client:
			response = client.post('/next', 
				headers=SAMPLE_HEADERS,
				data=json.dumps(SAMPLE_FIRST_PAYLOAD), 
				content_type='application/json'
			)
		self.assertEqual(response.status_code, 200, f"Received response:\n{response.text}")
		body = json.loads(response.data.decode('utf8')) if isinstance(response.data, bytes) else json.loads(response.data)
		self.assertIsInstance(body, dict)
		self.assertIn('message', body)
		self.assertIsInstance(body['message'], str)
		print(f"Received response:\n{body['message']}")


if __name__ == '__main__':
	unittest.main()
