"""Pure-logic helpers for the fleet-vs-frontier coding eval.

No network I/O in this module — see test_frontier_comparison_live.py for
the live orchestration that calls the fleet gateway and OpenRouter.
"""

from __future__ import annotations

PROMPTS: list[dict] = [
    {
        "id": "binary_search_off_by_one",
        "title": "Fix off-by-one bug in binary search",
        "task": (
            "This binary search has an off-by-one bug that makes it miss the "
            "last element of the array. Find and fix the bug. Return only the "
            "corrected Python code.\n\n"
            "```python\n"
            "def binary_search(arr, target):\n"
            "    lo, hi = 0, len(arr) - 1\n"
            "    while lo < hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            lo = mid + 1\n"
            "        else:\n"
            "            hi = mid - 1\n"
            "    return -1\n"
            "```"
        ),
    },
    {
        "id": "lru_cache",
        "title": "Implement an LRU cache",
        "task": (
            "Implement a Python class LRUCache(capacity: int) with O(1) get(key) "
            "and put(key, value) methods. get returns -1 if the key is missing. "
            "When capacity is exceeded, evict the least-recently-used entry. "
            "Return only the Python code."
        ),
    },
    {
        "id": "refactor_nested_ifs",
        "title": "Refactor nested ifs into early returns",
        "task": (
            "Refactor this function to use early returns instead of nested ifs, "
            "preserving its exact behavior. Return only the refactored Python code.\n\n"
            "```python\n"
            "def classify(age, has_license, has_car):\n"
            "    if age >= 18:\n"
            "        if has_license:\n"
            "            if has_car:\n"
            "                return 'can drive own car'\n"
            "            else:\n"
            "                return 'can drive, no car'\n"
            "        else:\n"
            "            return 'needs license'\n"
            "    else:\n"
            "        return 'too young'\n"
            "```"
        ),
    },
    {
        "id": "pytest_unit_tests",
        "title": "Write pytest unit tests with edge cases",
        "task": (
            "Write pytest unit tests (including edge cases like empty input and "
            "negative numbers) for this function. Return only the test code.\n\n"
            "```python\n"
            "def clamp(value, lo, hi):\n"
            "    return max(lo, min(value, hi))\n"
            "```"
        ),
    },
    {
        "id": "race_condition_fix",
        "title": "Diagnose and fix a race condition",
        "task": (
            "This counter class has a race condition when incremented from "
            "multiple threads. Diagnose the bug and return corrected Python "
            "code that is thread-safe.\n\n"
            "```python\n"
            "class Counter:\n"
            "    def __init__(self):\n"
            "        self.value = 0\n"
            "\n"
            "    def increment(self):\n"
            "        self.value = self.value + 1\n"
            "```"
        ),
    },
    {
        "id": "token_bucket_rate_limiter",
        "title": "Implement a token-bucket rate limiter",
        "task": (
            "Implement a Python class TokenBucket(rate: float, capacity: int) "
            "with a method allow() -> bool that returns True if a request is "
            "allowed under the token-bucket algorithm (refilling `rate` tokens "
            "per second, capped at `capacity`), False otherwise. Return only "
            "the Python code."
        ),
    },
    {
        "id": "n_plus_1_to_join",
        "title": "Rewrite N+1 query pattern into a JOIN",
        "task": (
            "This SQLAlchemy code has an N+1 query problem: it issues one query "
            "per author to fetch their books. Rewrite it to use a single query "
            "with a JOIN (or eager loading). Return only the corrected Python code.\n\n"
            "```python\n"
            "authors = session.query(Author).all()\n"
            "for author in authors:\n"
            "    books = session.query(Book).filter(Book.author_id == author.id).all()\n"
            "    print(author.name, [b.title for b in books])\n"
            "```"
        ),
    },
    {
        "id": "fastapi_endpoint",
        "title": "Implement a FastAPI endpoint with validation",
        "task": (
            "Implement a FastAPI POST endpoint `/users` that accepts JSON body "
            "{name: str, email: str, age: int}, validates that age >= 0 and "
            "email contains '@' (return HTTP 422 if invalid), and returns the "
            "created user with a generated integer id. Return only the Python code."
        ),
    },
]
