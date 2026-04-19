import json
import re


def clean_json_response(response):
    """
    Removes unwanted text around JSON
    """
    try:
        # Extract JSON part using regex
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            return json_match.group(0)
    except:
        pass

    return response


def parse_json(response):
    cleaned = clean_json_response(response)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON output",
            "raw_response": response
        }