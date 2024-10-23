from flask import Flask, jsonify, request
import decorators
from core.logic import next_question

app = Flask(__name__)
app.error_handler_spec[None] = decorators.wrap_flask_errors()
app.add_url_rule('/healthcheck', 'healthcheck', lambda: ('', 200))

@app.route('/')
def index():
	return 'Running!'

@app.route('/interview', methods=['POST'])
@decorators.handle_500
@decorators.allowed_domains()
@decorators.validate_json('INTERVIEW')
def interview():
	payload = request.get_json(force=True)
	return jsonify({"message":next_question(payload)})

