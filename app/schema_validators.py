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
        "first_question": {
            "type": "string",
            "description": "Question that began interview"
        },
        "open_topics": {
            "type":"array",
            "description": "List of topics to cover in interview",
            "items": { "type": "object" }
        },           
        "closing_questions": {
            "type": "array",
            "description": "Final questions to close interview",
            "items": { "type": "string" }
        }
    },
    "required": [
        "session_id",
        "user_message"
    ],
    "type": "object"
}

LOAD = {
    "description": "Load endpoint request schema",
    "properties": {
        "session_id": {
            "type": ["number", "string"],
            "description": "Unique interview ID"
        },
        "get_summary": {
            "type": ["boolean"],
            "description": "Directive to summarize interview"
        }
    },
    "required": ["session_id"],
    "type": "object"
}   

API_SCHEMAS = {
    "NEXT_POST": NEXT,
    "LOAD_POST": LOAD
}