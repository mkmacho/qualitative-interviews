from flask import Flask, request
from flask import jsonify, render_template, make_response
import decorators
from core import logic

app = Flask(__name__)
app.error_handler_spec[None] = decorators.wrap_flask_errors()
app.add_url_rule('/healthcheck', 'healthcheck', lambda: ('', 200))

@app.route('/<interview_id>/<session_id>', methods=['GET'])
@decorators.handle_500
def index(interview_id:str, session_id:str):
	""" Landing (start) page for interview_id session_id. """
	response = logic.begin_interview_session(interview_id, session_id)
	return render_template('chat.html', data=response)

@app.route('/next', methods=['POST'])
@decorators.handle_500
@decorators.allowed_domains()
def next():
	""" Internally called to continue interview. """
	payload = request.get_json(force=True)
	response = logic.next_question(**payload)
	return jsonify(response)

@app.route('/load/<session_id>', methods=['GET'])
@decorators.handle_500
def load(session_id:str):
	""" Load remote database entry for interview session_id. """
	session = logic.load_interview_session(session_id)
	return jsonify(session)

@app.route('/delete/<session_id>', methods=['GET'])
@decorators.handle_500
def delete(session_id:str):
	""" Delete remote database entry for interview session_id. """
	logic.delete_interview_session(session_id)
	return make_response(f"Successfully deleted session '{session_id}'.")


if __name__ == "__main__":
	app.run(host="127.0.0.1", port=8000, debug=True)
