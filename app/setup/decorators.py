from werkzeug.exceptions import default_exceptions
from functools import wraps
from flask import make_response, jsonify, request
import time
import traceback as tb
from jsonschema import validate 
from setup.schema_validators import API_SCHEMAS
from setup.log import Logger
from parameters import WHITELISTED_DOMAINS

# Specialized logging logger
logger = Logger()

def wrap_flask_errors():
	""" Wrap flask app-level errors as standardized JSON responses. """
	return {
		error_code: {
			error: lambda ex: make_response(jsonify({
				"http_code": getattr(ex, "http_code", 405 if "Method" in str(ex) else 400),
				"meta": {
					"type": type(ex).__name__,
					"error": str(ex) or "",
					"tb": tb.format_exc() if not ("NoneType" in tb.format_exc()) else ""
				},
				"message": str(ex) or getattr(ex, "description", ""),
			}), 
			getattr(ex, "http_code", error_code)
		)} for error_code, error in default_exceptions.items()
	}

def allowed_domains():
	""" Only allow pre-defined domains to access. """
	def decorator(f):
		@wraps(f)
		def decorated(*args, **kwargs):
			domain = request.headers.get("origin", "")
			if not domain in WHITELISTED_DOMAINS:
				return make_response(
					jsonify({
						"message":"Invalid domain: origin '{0}' is not allowed.",
						"http_code":401
					}), 401
				)
			return f(*args, **kwargs)
		return decorated
	return decorator

def validate_json(endpoint:str="INTERVIEW"):
	""" Validate incoming request using JSON Schema. """
	def decorator(f):
		@wraps(f)
		def decorated(*args, **kwargs):
			try:
				payload = request.get_json(force=True, silent=True) or {}
				endpoint_schema = '{0}_{1}'.format(endpoint, request.method)
				validate(payload, API_SCHEMAS[endpoint_schema])
			except Exception as e:
				return make_response(
					jsonify({
						"message":str(e).split("\n")[0],
						'type':type(e).__name__,
						'tb':tb.format_exc()
					}), 400
				)
			return f(*args, **kwargs)
		return decorated
	return decorator

def response_log(response, status, start_time, key="info"):
	""" Log outgoing response. Useful for debugging/monitoring. """
	logger.log(key=key, message={
		"payload":request.get_json(force=True, silent=True) or {},
		"url":request.url,
		"duration":time.time() - start_time,
		"response":response,
		"http_code":status,
		"type":response["type"] if (isinstance(response, dict) and 
			response.get("tb")) else "RequestSuccessful"
	})

def handle_500(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		start_time = time.time()
		try:
			response = f(*args, **kwargs)
			response_log(
				getattr(response, 'json') if request.endpoint == 'next' else request.endpoint, 
				getattr(response, 'status_code', 200), 
				start_time
			)
		except Exception as e:
			http_code = getattr(e, "http_code", None) or getattr(e, "code", 500)
			message = str(e) or getattr(e, "message", "Service failed")
			meta = {"type":type(e).__name__,"tb":tb.format_exc(),"str":message}
			response_log(meta, http_code, start_time, key="error")
			response = make_response(jsonify(meta), http_code)
		return response
	return decorated
