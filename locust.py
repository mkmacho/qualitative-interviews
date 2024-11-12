from locust import HttpUser, task, constant
import random
import os

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

class QuickstartUser(HttpUser):
	wait_time = constant(0)
	host = "http://0.0.0.0:8000"
	# session_ids = [i for i in range(1,201)]

	# @task(10) # Call 10x as often
	# def test_start(self):
	# 	# Start interview
	# 	self.client.get(f"/STOCK_MARKET/{random.choice(self.session_ids)}")

	# @task
	# def test_load(self):
	# 	# Load interview history for random session
	# 	self.client.get(f"/load/{random.choice(self.session_ids)}")

	# @task(5) # Call 5x as often
	# def test_interview(self):
	# 	# Gather next interview question
	# 	self.client.post("/next", 
	# 		headers={'origin':self.host}, 
	# 		json={
	# 			"session_id" : random.choice(self.session_ids),
	# 			"user_message" : random.choice(sample_messages)
	# 		}
	# 	)
		
	# @task
	# def test_delete(self):
	# 	# Delete interview for random session
	# 	self.client.get(f"/delete/{random.choice(self.session_ids)}")

	@task
	def test_interview(self):
		# Gather next interview question
		# session_id = os.urandom(15).hex()
		session_id = random.randint(1,200)
		#self.client.get(f"/STOCK_MARKET/{session_id}")
		self.client.post("/next", 
			headers={'origin':self.host}, 
			json={
				"session_id": session_id,
				"user_message": random.choice(sample_messages)
			}
		)
