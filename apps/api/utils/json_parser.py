import json
from pathlib import Path
from typing import Any, Dict, Optional

import ijson
from utils.logger import get_logger

logger = get_logger(__name__)


def safe_load_json(file_path: str | Path) -> Optional[Dict[str, Any]]:
    """
    Safely load JSON data from a file, attempting to recover data even if the file is corrupted.
    Uses multiple strategies:
    1. Standard JSON parser
    2. ijson streaming parser
    3. Manual recovery of partial JSON
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    # Strategy 1: Try standard JSON parser first
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"Standard JSON parser failed: {e}")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return None

    # Strategy 2: Try ijson streaming parser
    try:
        with open(file_path, "rb") as f:
            parser = ijson.parse(f)
            result = {}
            current_key = None
            current_value = None

            for prefix, event, value in parser:
                if prefix == "item":
                    if current_key and current_value is not None:
                        result[current_key] = current_value
                    current_key = value
                    current_value = None
                elif prefix == "item.value":
                    current_value = value

            # Add the last key-value pair
            if current_key and current_value is not None:
                result[current_key] = current_value

            if result:
                logger.info(
                    f"Successfully recovered partial JSON data using ijson parser with {len(result)} fields: {result.keys()}"
                )
                return result
    except Exception as e:
        logger.warning(f"ijson parser failed: {e}")

    # Strategy 3: Manual recovery of partial JSON
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the last complete object
        result = {}
        current_pos = 0
        while True:
            try:
                # Try to find the next key-value pair
                key_start = content.find('"', current_pos)
                if key_start == -1:
                    break

                key_end = content.find('"', key_start + 1)
                if key_end == -1:
                    break

                value_start = content.find(":", key_end + 1)
                if value_start == -1:
                    break

                # Try to parse the value
                value_str = content[value_start + 1 :].strip()
                if value_str.startswith('"'):
                    # String value
                    value_end = value_str.find('"', 1)
                    if value_end == -1:
                        break
                    value = value_str[1:value_end]
                elif value_str.startswith("{"):
                    # Object value
                    brace_count = 1
                    value_end = 1
                    while brace_count > 0 and value_end < len(value_str):
                        if value_str[value_end] == "{":
                            brace_count += 1
                        elif value_str[value_end] == "}":
                            brace_count -= 1
                        value_end += 1
                    if brace_count > 0:
                        break
                    try:
                        value = json.loads(value_str[:value_end])
                    except json.JSONDecodeError:
                        break
                elif value_str.startswith("["):
                    # Array value
                    bracket_count = 1
                    value_end = 1
                    while bracket_count > 0 and value_end < len(value_str):
                        if value_str[value_end] == "[":
                            bracket_count += 1
                        elif value_str[value_end] == "]":
                            bracket_count -= 1
                        value_end += 1
                    if bracket_count > 0:
                        break
                    try:
                        value = json.loads(value_str[:value_end])
                    except json.JSONDecodeError:
                        break
                else:
                    # Try to parse as number or boolean
                    value_end = value_str.find(",")
                    if value_end == -1:
                        value_end = value_str.find("}")
                    if value_end == -1:
                        break
                    try:
                        value = json.loads(value_str[:value_end])
                    except json.JSONDecodeError:
                        break

                key = content[key_start + 1 : key_end]
                result[key] = value
                current_pos = value_start + value_end + 1

            except Exception:
                break

        if result:
            logger.info(
                f"Successfully recovered partial JSON data using manual recovery with {len(result)} fields: {result.keys()}"
            )
            return result

    except Exception as e:
        logger.error(f"Manual recovery failed: {e}")

    return None
