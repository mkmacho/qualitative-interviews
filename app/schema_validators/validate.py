from jsonschema import validate as json_validate
from .api_schemas import *

VALIDATORS = {
    'INTERVIEW_POST': INTERVIEW,
}

def validate(data, schema):
    if VALIDATORS[schema]: json_validate(data, VALIDATORS[schema])