import jsonschema
import requests

import os
import json
import logging
import getopt
from sys import argv


logger = logging.getLogger(__name__)
# path to a top-level schema
SCHEMA_PATH = os.path.dirname(os.path.realpath(__file__)) + '/conp-dats/dataset_schema.json'


# set value to 0 if there is no controlled vocabulary list, set value to a list if there is one.
REQUIRED_EXTRA_PROPERTIES = {
    "files": 0,
    "subjects": 0,
    "CONP_status": ["CONP", "Canadian", "external"]
}


def main(argv):
    FORMAT = '%(message)s'
    logging.basicConfig(format=FORMAT)
    logging.getLogger().setLevel(logging.INFO)
    opts, args = getopt.getopt(argv, "", ["file="])
    json_filename = ''

    for opt, arg in opts:
        if opt == '--file':
            json_filename = arg

    if json_filename == '':
        help()
        exit()

    with open(json_filename) as json_file:
        json_obj = json.load(json_file)
        validate_json(json_obj)
        validate_non_schema_required(json_obj)


def validate_json(json_obj):
    """ Checks if json object is valid according to CONP DATS json schema. """

    with open(SCHEMA_PATH) as s:
        json_schema = json.load(s)
    # first validate schema file
    v = jsonschema.Draft4Validator(json_schema, format_checker=jsonschema.FormatChecker())
    # now validate json file
    try:
        jsonschema.validate(json_obj, json_schema, format_checker=jsonschema.FormatChecker())
        logger.info("JSON schema validation passed.")
        return True
    except jsonschema.exceptions.ValidationError:
        errors = [e for e in v.iter_errors((json_obj))]
        logger.info(f"The file is not valid. Total json schema errors: {len(errors)}")
        for i, error in enumerate(errors, 1):
            logger.error(f"{i} Validation error in {'.'.join(str(v) for v in error.path)}: {error.message}")
        logger.info("JSON schema validation failed.")
        return False


def validate_extra_properties(dataset):
    """ Checks if required extraProperties are present in a dataset."""

    try:
        errors = []
        extra_prop_categories = {prop["category"]: [value["value"] for value in prop["values"]]
                                 for prop in dataset["extraProperties"] if "extraProperties" in dataset}
        # first checks if required extraProperties categories are present
        for category in REQUIRED_EXTRA_PROPERTIES:
            if category not in extra_prop_categories:
                error_message = f"Validation error in {dataset['title']}: " \
                                f"extraProperties.category.{category} is required but not found."
                errors.append(error_message)

        # checks if values of required extraProperties are correct according to a controlled vocabulary
        if "CONP_status" in extra_prop_categories:
            for each_value in extra_prop_categories["CONP_status"]:
                if each_value not in REQUIRED_EXTRA_PROPERTIES["CONP_status"]:
                    error_message = f"Validation error in {dataset['title']}: extraProperties.category." \
                                    f"CONP_status - {each_value} is not allowed value for CONP_status. " \
                                    f"Allowed values are {REQUIRED_EXTRA_PROPERTIES['CONP_status']}."
                    errors.append(error_message)
        # checks if 'derivedFrom' values refer to existing datasets accessible online
        if "derivedFrom" in extra_prop_categories:
            for value in extra_prop_categories["derivedFrom"]:
                if not dataset_exists(value):
                    error_message = f"The 'derivedFrom' dataset {value} is not found."
                    errors.append(error_message)

        if errors:
            return False, errors
        else:
            return True, errors

    # extraProperties is only required property which is not required on dataset_schema level,
    # if it's not present an Exception is raised
    except KeyError as e:
        raise Exception(f"{e} is required."
                        f"The following extra properties categories are required: "
                        f"{[k for k in REQUIRED_EXTRA_PROPERTIES.keys()]}")


def validate_recursively(obj, errors):
    """ Checks all datasets recursively for required extraProperties. """

    val, errors_list = validate_extra_properties(obj)
    errors.extend(errors_list)
    if "hasPart" in obj:
        for each in obj["hasPart"]:
            validate_recursively(each, errors)


def validate_non_schema_required(json_obj):
    """ Checks if json object has all required extra properties beyond json schema. Prints error report. """

    errors = []
    validate_recursively(json_obj, errors)
    if errors:
        logger.info(f"Total required extra properties errors: {len(errors)}")
        for i, er in enumerate(errors, 1):
            logger.error(f"{i} {er}")
        return False
    else:
        logger.info(f"Required extra properties validation passed.")
        return True


# cache responses to avoid redundant calls
cache = dict()


def dataset_exists(derived_from_url):
    """ Caches response values in cache dict. """

    if derived_from_url not in cache:
        cache[derived_from_url] = get_response_status(derived_from_url)
    return cache[derived_from_url]


def get_response_status(derived_from_url):
    """ Get a response status code for derivedFrom value. Returns True if status code is 200."""

    try:
        r = requests.get(derived_from_url)
        r.raise_for_status()
        if r.status_code == 200:
            return True

    except requests.exceptions.HTTPError as e:
        return False


def help():
    return logger.info("Usage: python validator.py --file=doc.json")


if __name__ == "__main__":
    main(argv[1:])
