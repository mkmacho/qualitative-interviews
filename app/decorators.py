from werkzeug.exceptions import default_exceptions
from functools import wraps
from flask import make_response, jsonify, request
import time
import traceback as tb
import schema_validators
from log import Logger
from core.parameters import WHITELISTED_DOMAINS

logger = Logger()

def wrap_flask_errors():
	""" Wrap flask app-level errors as standardized JSON responses. """
	return {
		error_code: {
			error: lambda ex: make_response(jsonify({
				"error_code": getattr(ex, "error_code", error_code),
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
	def decorator(f):
		@wraps(f)
		def decorated(*args, **kwargs):
			domain = request.headers.get("origin", "")
			if not domain in WHITELISTED_DOMAINS:
				return make_response(
					jsonify({
						"message":"Invalid domain: origin '{0}' is not allowed. " \
						"Allowed domains are {1}".format(domain, WHITELISTED_DOMAINS),
						"http_code":401
					}), 401
				)
			return f(*args, **kwargs)
		return decorated
	return decorator

def validate_json(endpoint):
	""" Validate incoming request using JSON Schema. """
	def decorator(f):
		@wraps(f)
		def decorated(*args, **kwargs):
			try:
				data = request.get_json(force=True, silent=True) or {}
				schema = '{0}_{1}'.format(endpoint, request.method)
				schema_validators.validate(data, schema)
			except Exception as e:
				return make_response(
					jsonify({
						"message":str(e).split("\n")[0],
						"http_code":400,
						"meta":{'str':str(e),'type':type(e).__name__,'tb':tb.format_exc()}
					}),400
				)
			return f(*args, **kwargs)
		return decorated
	return decorator

def response_log(resp, status, start, key="info", resp_type="RequestSuccessful"):
	logger.log(key="critical", message={
		"payload":request.get_json(force=True, silent=True) or {},
		"url":request.url,
		"duration":time.time() - start,
		"response":resp,
		"http_code":status,
		"type":resp_type
	})

def handle_500(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		start_time = time.time()
		try:
			response = f(*args, **kwargs)
			response_log(response.json, response.status_code, start_time)
		except Exception as e:
			http_code = getattr(e, "http_code", None) or getattr(e, "code", 500)
			message = str(e) or getattr(e, "message", "Service failed")
			meta = {"type":type(e).__name__,"tb":tb.format_exc(),"str":message}
			response_log(meta, http_code, start_time, key="error", resp_type=meta["type"])
			response = make_response(
				jsonify({
					"message":message, 
					"http_code":http_code, 
					"meta":meta
				}), http_code
			)
		return response
	return decorated
