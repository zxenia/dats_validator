# Simple dats validator

Usage: <pre>python validator.py --json=doc.json</pre>

Test valid and invalid examples: <pre>python tests.py</pre>

To validate against custom DATS schemas:

- add  directory (e.g. submodule) containing all custom DATS schemas
- in validator.py set SCHEMA_PATH to the top-level (main) schema file
