import unittest
from validator import validate_dats
import json
import os

EXAMPLES = os.path.dirname(os.path.realpath(__file__)) + '/examples/'

class JsonschemaTest(unittest.TestCase):
    valid =  os.path.join(EXAMPLES, 'valid_dats.json')
    invalid = os.path.join(EXAMPLES, 'invalid_dats.json')

    def test_validate_dats(self):
        with open(self.valid) as vjson:
            valid_obj = json.load(vjson)
            valid_validation = validate_dats(valid_obj)
        with open(self.invalid) as invjson:
            invalid_obj = json.load(invjson)
            invalid_validation = validate_dats(invalid_obj)
        self.assertEqual(valid_validation, True)
        self.assertEqual(invalid_validation, False)

if __name__ == '__main__':
    unittest.main()
