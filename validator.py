import jsonschema
import os
import json
import logging
import getopt
from sys import argv


logger = logging.getLogger(__name__)
DATS_PATH = os.path.dirname(os.path.realpath(__file__)) + '/dats/dataset_schema.json'


def main(argv):
    FORMAT = '%(message)s'
    logging.basicConfig(format=FORMAT)
    logging.getLogger().setLevel(logging.INFO)
    opts, args = getopt.getopt(argv, "", ["json="])
    json_filename = ''

    for opt, arg in opts:
        if opt == '--json':
            json_filename = arg

    if json_filename == '':
        help()
        exit()

    with open(json_filename) as json_file:
        json_obj = json.load(json_file)
        validate_dats(json_obj)


def validate_dats(dats_json):
    with open(DATS_PATH) as s:
        json_schema = json.load(s)
    # first validate schema file
    v = jsonschema.Draft4Validator(json_schema)
    # now validate dats file
    try:
        jsonschema.validate(dats_json, json_schema, format_checker=jsonschema.FormatChecker())
        logger.info('DATS file is valid. Validation passed.')
        return True
    except jsonschema.exceptions.ValidationError:
        errors = [e for e in v.iter_errors((dats_json))]
        logger.info(f"DATS file is not valid. Total errors: {len(errors)}")
        for i, error in enumerate(errors, 1):
            logger.error(f"{i} Validation error in {'.'.join(str(v) for v in error.path)}: {error.message}")
        logger.info('Validation failed.')
        return False


def help():
    return logger.info('Usage: python validator.py --json=doc.json')


if __name__ == "__main__":
    main(argv[1:])
