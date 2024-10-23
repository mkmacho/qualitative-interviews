INTERVIEW = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "User message object",
    "description": "User's interview response/request",
    "properties": {
        "message": {"type": "string"},
        "topics": {"type":"object"},            # or string?
        "topicsLength": {"type": "array"},      # or string?
        "firstQuestion": {"type": "string"},
        "promptTopic": {"type":"string"},       # set default in code?
        "promptHistory": {"type":"string"},
        "promptFinish": {"type":"object"},      # why different?
        "promptProbing": {"type":"string"},
        "modelNameShort": {"type":"string"},    
        "modelNameLong": {"type":"string"},     
        "temperatureTopic": {"type":"number", "minimum":0.0, "maximum":1.0},
        "temperatureHistory": {"type":"number", "minimum":0.0, "maximum":1.0},
        "temperatureFinish": {"type":"number", "minimum":0.0, "maximum":1.0},
        "temperatureProbing": {"type":"number", "minimum":0.0, "maximum":1.0},
        "userID": {"type":"number"},
        "surveyID": {"type":"number"},
        "questionID": {"type":"number"},
        "versionID": {"type":"number"},
    },
    "required": [
        "message","firstQuestion",
        "topics","topicsLength",
        "promptTopic","promptHistory","promptFinish","promptProbing",
        "userID","surveyID","questionID","versionID"
    ],
    "type": "object"
}

    