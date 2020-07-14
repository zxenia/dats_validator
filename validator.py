import jsonschema
import os
import json
import logging
import getopt
from sys import argv


logger = logging.getLogger(__name__)
# path to a top-level schema
SCHEMA_PATH = os.path.dirname(os.path.realpath(__file__)) + '/conp-dats/dataset_schema.json'


# set value to 0 if there is no controlled vocabulary list, set a value to a list if there is one.
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
        validate_recursively(json_obj)


def validate_json(json_obj):
    """ Checks if json object is valid according to CONP DATS json schema. """

    with open(SCHEMA_PATH) as s:
        json_schema = json.load(s)
    # first validate schema file
    v = jsonschema.Draft4Validator(json_schema)
    # now validate json file
    try:
        jsonschema.validate(json_obj, json_schema, format_checker=jsonschema.FormatChecker())
        logger.info('JSON schema validation passed.')
        return True
    except jsonschema.exceptions.ValidationError:
        errors = [e for e in v.iter_errors((json_obj))]
        logger.info(f"The file is not valid. Total errors: {len(errors)}")
        for i, error in enumerate(errors, 1):
            logger.error(f"{i} Validation error in {'.'.join(str(v) for v in error.path)}: {error.message}")
        logger.info('JSON schema validation failed.')
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
                error_message = f"Validation error: " \
                                f"extraProperties - category - {category} is not found."
                errors.append(error_message)
                #logger.error(error_message)

        # checks if values of required extraProperties are correct according to a controlled vocabulary
        if "CONP_status" in extra_prop_categories:
            for each_value in extra_prop_categories["CONP_status"]:
                if each_value not in REQUIRED_EXTRA_PROPERTIES["CONP_status"]:
                    error_message = f"Validation error: extraProperties - category - " \
                                    f"CONP_status - {each_value} is not allowed value for CONP_status. " \
                                    f"Allowed values are {REQUIRED_EXTRA_PROPERTIES['CONP_status']}."
                    errors.append(error_message)
                    #logger.error(error_message)

        if errors:
            logger.info(f"Total errors for dataset {dataset['title']}: {len(errors)}.")
            for i, er in enumerate(errors, 1):
                logger.error(f"{i} {er}")
            return False
        else:
            #logger.info(f"Required extra properties validation for dataset {dataset['title']} has passed.")
            return True

    # extraProperties is only required property which is not required on dataset_schema level,
    # if it's not present an Exception is raised
    except KeyError as e:
        raise Exception(f"{e} is required."
                        f"The following extraProperties categories are required: "
                        f"{[k for k in REQUIRED_EXTRA_PROPERTIES.keys()]}")


def validate_recursively(obj):
    """ Checks all datasets recursively for required extraProperties. """

    validate_extra_properties(obj)
    if "hasPart" in obj:
        for child_dataset in obj["hasPart"]:
            validate_recursively(child_dataset)


def help():
    return logger.info('Usage: python validator.py --file=doc.json')


if __name__ == "__main__":
    main(argv[1:])
