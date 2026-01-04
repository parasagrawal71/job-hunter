import re
from typing import Tuple, List

def clean_string_value(value):
    if not isinstance(value, str):
        return value
    return value.replace('"', "").strip()

def normalize_str_into_words(words: List[str]) -> List[str]:
    normalized = []
    for word in words:
        parts = [part.strip().lower() for part in word.split(",")]
        normalized.extend(parts)
    return normalized

def contains_whole_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None

def match_words(text, words):
    if not text:
        return []
    text = text.lower()
    return [word for word in words if contains_whole_word(text, word)]
