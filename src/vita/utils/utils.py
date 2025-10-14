import re
import hashlib
import json
import subprocess
from typing import Dict, Union
from datetime import datetime, timedelta
from pathlib import Path

from deepdiff import DeepDiff
from dotenv import load_dotenv
from loguru import logger
from thefuzz import fuzz, process
from json_repair import repair_json

from vita.config import DEFAULT_LANGUAGE

global_time = None

res = load_dotenv()
if not res:
    logger.warning("No .env file found")

SOURCE_DIR = Path(__file__).parents[3]
DATA_DIR = SOURCE_DIR / "data"
DOMAIN_DIR = DATA_DIR / "vita" / "domains"

def get_task_file_path(domain: str, language: str = None) -> Path:
    """Return corresponding task file path based on language parameter"""
    if language is None:
        language = DEFAULT_LANGUAGE
    
    if language == "english":
        return DOMAIN_DIR / domain / "tasks_en.json"
    else:
        return DOMAIN_DIR / domain / "tasks.json"

# Task file path definitions
DELIVERY_TASK_SET_PATH = get_task_file_path("delivery")
INSTORE_TASK_SET_PATH = get_task_file_path("instore")
CROSS_TASK_SET_PATH = get_task_file_path("cross_domain")
OTA_TASK_SET_PATH = get_task_file_path("ota")


def get_hash(obj: Union[dict, str]) -> str:
    """
    Generate a unique hash for dict.
    Returns a hex string representation of the hash.
    """
    if isinstance(obj, dict):
        hash_string = json.dumps(obj, sort_keys=True, default=str, ensure_ascii=False)
    else:
        hash_string = obj
    return hashlib.sha256(hash_string.encode()).hexdigest()


def show_dict_diff(dict1: dict, dict2: dict) -> str:
    """
    Show the difference between two dictionaries.
    """
    diff = DeepDiff(dict1, dict2)
    return diff


def get_now(format: str = "%Y%m%d_%H%M%S") -> str:
    """
    Returns the current date and time in the format YYYYMMDD_HHMMSS.
    """
    global global_time
    if global_time is not None:
        return global_time
    now = datetime.now()
    return format_time(now, format=format)


def str_to_datetime(time: str) -> datetime:
    return datetime.strptime(time, "%Y-%m-%d %H:%M:%S")

def get_weekday(date: str, language: str = None) -> str:
    """Get weekday in the specified language"""
    if language is None:
        language = DEFAULT_LANGUAGE
    
    if language == "english":
        weekday_dict = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        weekday = str_to_datetime(date).weekday()
        return weekday_dict[weekday]
    else:
        weekday_dict = {0: '一', 1: '二', 2: '三',  3: '四',  4: '五',  5: '六',  6: '日'}
        weekday = str_to_datetime(date).weekday()
        return f"星期{weekday_dict[weekday]}"

def format_time(time: datetime, format: str = "%Y%m%d_%H%M%S") -> str:
    """
    Format the time in the format YYYYMMDD_HHMMSS.
    """
    return time.strftime(format)


def check_time_format(time: str, format="%Y-%m-%d %H:%M:%S") -> bool:
    try:
        datetime.strptime(time, format)
        return True
    except ValueError:
        return False


def check_date_format(date: str) -> bool:
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_date_between(start_date: str, end_date: str) -> list[str]:
    """
    Get Date List between start_date and end_date. (include start_date and end_date)
    """
    date_list = []
    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
    while start_datetime < end_datetime:
        date_list.append(start_datetime.strftime("%Y-%m-%d"))
        start_datetime += timedelta(days=1)
    return date_list


def get_commit_hash() -> str:
    """
    Get the commit hash of the current directory.
    """
    try:
        commit_hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], text=True)
            .strip()
            .split("\n")[0]
        )
    except Exception as e:
        logger.error(f"Failed to get git hash: {e}")
        commit_hash = "unknown"
    return commit_hash


def edit_distance_score(s1: str, s2: str):
    """Calculate the edit distance between two strings."""
    dp = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
    for i in range(len(s1) + 1):
        dp[i][0] = i
    for j in range(len(s2) + 1):
        dp[0][j] = j
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1
    return 1 - dp[len(s1)][len(s2)] / max(len(s1), len(s2))


def rerank(keywords: str, docs: Dict[str, str], with_score: bool = False):
    candidates = [doc for doc in docs.values()]
    doc_dict_reverse = {val: key for key, val in docs.items()}
    docs_sorted = process.extract(keywords, candidates, limit=None, scorer=fuzz.partial_ratio)
    if with_score:
        id_doc_sorted = [(doc_dict_reverse[doc], doc, score) for doc, score in docs_sorted]
    else:
        id_doc_sorted = [(doc_dict_reverse[doc], doc) for doc, _ in docs_sorted]
    return id_doc_sorted


def fuzzy_match(x: str, y: str) -> bool:
    if fuzz.partial_ratio(x, y) >= 40:
        return True
    else:
        return False


def fuzzy_ratio_match(x: str, y: str) -> bool:
    if fuzz.ratio(x, y) >= 20:
        return True
    else:
        return False


def json_check(json_str: str) -> bool:
    try:
        json.loads(json_str)
        return True
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Format error: {e}")
        return False


def extract_json_fields(json_str):
    """Simple function to extract JSON fields"""
    rubrics_pattern = r'"rubrics":\s*"(.*?)"(?=,|\s*})'
    reasoning_pattern = r'"reasoning":\s*"(.*?)"(?=,|\s*})'
    meet_expectation_pattern = r'"meetExpectation":\s*(true|false)'

    rubrics_list = re.findall(rubrics_pattern, json_str, re.DOTALL)
    reasoning_list = re.findall(reasoning_pattern, json_str, re.DOTALL)
    meet_expectation_list = re.findall(meet_expectation_pattern, json_str)

    results = []
    max_length = max(len(rubrics_list), len(reasoning_list), len(meet_expectation_list))

    for i in range(max_length):
        obj_result = {}
        if i < len(rubrics_list):
            obj_result['rubrics'] = rubrics_list[i]
        if i < len(reasoning_list):
            obj_result['reasoning'] = reasoning_list[i]
        if i < len(meet_expectation_list):
            obj_result['meetExpectation'] = meet_expectation_list[i] == 'true'

        results.append(obj_result)

    return results


def evaluator_extracter(content: str) -> list[dict]:
    """
    Extract the result from the content.
    """
    good_json_string = repair_json(content)
    result_data = json.loads(good_json_string)
    return result_data