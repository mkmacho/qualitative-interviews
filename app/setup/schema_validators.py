NEXT = {
    "description": "Next endpoint request schema",
    "properties": {
        "session_id": {
            "type": ["number", "string"],
            "description": "Unique interview ID"
        },
        "user_message": {
            "type": "string",
            "description": "Interviewee response"
        },
        "parameters_id": {
            "type": ["number", "string"],
            "description": "Index for interview parameter set"
        },
    },
    "required": [
        "session_id",
        "user_message",
        "parameters_id"
    ],
    "type": "object"
}

SESSION = {
    "properties": {
        "session_id": {
            "type": ["number", "string"],
            "description": "Unique interview ID"
        }
    },
    "required": ["session_id"],
    "type": "object"
}   

API_SCHEMAS = {
    "NEXT_POST": NEXT,
    "INTERVIEW_POST": SESSION
}