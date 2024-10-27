from flask import Flask, jsonify, request
import decorators
from core import logic

app = Flask(__name__)
app.error_handler_spec[None] = decorators.wrap_flask_errors()
app.add_url_rule('/healthcheck', 'healthcheck', lambda: ('', 200))

@app.route('/')
def index():
	return 'Running!'

@app.route('/next', methods=['POST'])
@decorators.handle_500
@decorators.allowed_domains()
@decorators.validate_json('NEXT')
def next():
	payload = request.get_json(force=True)
	response = logic.next_question(payload)
	return jsonify(response)

@app.route('/load', methods=['POST'])
@decorators.handle_500
@decorators.allowed_domains()
@decorators.validate_json('LOAD')
def load():
	payload = request.get_json(force=True)
	response = logic.load_interview(payload)
	return jsonify(response)

@app.route('/delete', methods=['POST'])
@decorators.handle_500
@decorators.allowed_domains()
def delete():
	payload = request.get_json(force=True)
	logic.delete_interview(payload)
	return jsonify({'success':True})