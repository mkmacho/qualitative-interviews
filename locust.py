from locust import HttpUser, task, between
from random import randint, choice
from time import sleep
from json.decoder import JSONDecodeError

sample_messages = [
	"I dont like stocks",
	"The game is rigged",
	"Stop the itnerview",
	"Not enough money to lose. Why would I? And why do you want to know anyway?",
	"No one gets ahead",
	"I am sleepy",
	"Do you?",
	"We've already tried that before",
	"THere's no point, we'd just lose money",
	"I do own a few actually"
]

class Quickstart(HttpUser):
	wait_time = between(0, 2)

	@task
	def test_interview(self):
		session_id = str(randint(1,100))
		
		# Load session
		r = self.client.get(f"/load/{session_id}")
		if r.status_code != 200 or not isinstance(r.json(), dict): 
			print(f"ERROR {r.status_code}: /load/{session_id} returned: {r.text}")
			return

		# Start session if not already started
		if not r.json():
			r = self.client.get(f"/STOCK_MARKET/{session_id}")
			if r.status_code != 200:
				print(f"ERROR {r.status_code}: /STOCK_MARKET/{session_id} returned: {r.text}")
				return
			sleep(1)

		# Continue session
		r = self.client.post("/next", json={
			"session_id": session_id,
			"user_message": choice(sample_messages)
		})
		if r.status_code != 200:
			print(f"ERROR {r.status_code}: /next/{session_id} returned: {r.text}")
			return 
		try:
			message = r.json()['message']
			assert message
		except JSONDecodeError:
			print(f"ERROR {r.status_code}: /next/{session_id} returned empty: {r.text}")
			return 

		if 'unusual input' in message or 'interview is over' in message:
			# Delete session
			r = self.client.get(f"/delete/{session_id}")
			if r.status_code != 200:
				print(f"ERROR {r.status_code}: /delete/{session_id} returned: {r.text}")

