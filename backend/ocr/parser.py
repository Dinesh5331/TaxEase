import json
import re

PAN_RE = re.compile(r"(?<![A-Z0-9])([A-Z]{5}[0-9]{4}[A-Z])(?![A-Z0-9])", re.IGNORECASE)


def _mask(pan):
    return f"{pan[:2].upper()}{'*' * 6}{pan[-2:].upper()}"


def mask_pans(text):
    """Replace every PAN with its masked form. Run on document text before it goes to an LLM."""
    return PAN_RE.sub(lambda m: _mask(m.group(1)), text)


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