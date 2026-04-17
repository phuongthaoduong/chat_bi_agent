import re

# Patterns that strongly indicate non-data questions.
# Each pattern is compiled once at import time for speed.
_IRRELEVANT_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(tell|say)\s+(me\s+)?(a\s+)?(joke|story|riddle|fun fact)",
        r"\bwrite\s+(me\s+)?(a\s+)?(poem|essay|letter|email|code|script|song|story)",
        r"\b(what('?s| is)\s+the\s+weather|forecast)\b",
        r"\bwho\s+is\s+the\s+(president|prime minister|king|queen|ceo)\b",
        r"\btranslat(e|ion)\b",
        r"\b(how\s+(do|can|to)\s+(i|you|we)\s+(cook|bake|make food|fix|repair|install|draw|paint|play))\b",
        r"\b(play|sing|dance|draw)\s+(a\s+)?(game|song|music|picture)\b",
        r"\bmeaning\s+of\s+life\b",
        r"\b(recipe|cooking|baking)\s+(for|instructions)\b",
        r"\b(help\s+me\s+)?(write|draft|compose)\s+(an?\s+)?(essay|blog|article|resume|cv|cover letter)\b",
        r"\b(what|who)\s+(is|are|was|were)\s+[A-Z][a-z]+\s+[A-Z]",
        r"\bwrite\s+(me\s+)?(python|javascript|java|html|css|sql|code)\b",
    ]
]

# If the question matches ANY of these data-related patterns, it's NOT irrelevant
_DATA_SAFEGUARD_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(data|dataset|column|row|table|chart|graph|plot|trend|sales|revenue|profit|cost|price|inventory|order|customer|product|category|region|average|total|sum|count|max|min|mean|median|percentage|proportion|share|distribution|correlation|comparison|rank|top|bottom|group\s+by|filter|sort\s+by|aggregate|breakdown)\b",
    ]
]


def is_obviously_irrelevant(question: str) -> bool:
    """Fast heuristic check. Returns True only for clearly off-topic questions."""
    for pattern in _DATA_SAFEGUARD_PATTERNS:
        if pattern.search(question):
            return False

    for pattern in _IRRELEVANT_PATTERNS:
        if pattern.search(question):
            return True

    return False
