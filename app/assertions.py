import os.path
import json
from jsonschema import validate, draft7_format_checker
from jsonschema.exceptions import ValidationError as JsonValidationError

def assert_valid_schema(data, schema_type):
    # checks whether the given data matches the schema

    #TODO: get these from redis or similar - only get from disk first time

    if schema_type == 'urls':
        schema = _load_json_schema('schemas/urls.json')

    if schema_type == 'uuid':
        schema = _load_json_schema('schemas/uuid.json')

    return validate(data, schema, format_checker=draft7_format_checker)


def _load_json_schema(filename):
    # loads the given schema file
    filepath = os.path.join(os.path.dirname(__file__), filename)

    with open(filepath) as schema_file:
        return json.loads(schema_file.read())
