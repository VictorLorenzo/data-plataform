import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file_template:
            return json.load(file_template)
    except FileNotFoundError as error:
         logger.error(f"File not found: {file_path}")
         raise error
    except json.JSONDecodeError as error:
        logger.error(f"Error JSON from file: {file_path}")
        raise error
    except IOError as error:
        logger.error(f"IOError with reading file {file_path}: {error}")
        raise error