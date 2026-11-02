import hashlib
import json

_cache = {}

def make_cache_key(symptoms: list, category: str) -> str:
    key_str = f"{sorted(symptoms)}_{category}"
    return hashlib.md5(key_str.encode()).hexdigest()

def get_cached_question(symptoms: list, category: str):
    key = make_cache_key(symptoms, category)
    return _cache.get(key)

def set_cached_question(symptoms: list, category: str, question: str):
    key = make_cache_key(symptoms, category)
    _cache[key] = question
