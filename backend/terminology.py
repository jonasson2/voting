"""Presentation-only terminology, shared with the web frontend.

Only pass application-owned labels to label(); names and election data are opaque.
The context is confined to a report call, including concurrent web requests.
"""
from contextvars import ContextVar
from functools import wraps
import json
from pathlib import Path
import re

CATALOG = json.loads((Path(__file__).resolve().parent.parent /
                      "vue-frontend/src/terminology.json").read_text(encoding="utf-8"))
_preferences = ContextVar("report_terminology", default={})


def normalize_terminology(preferences=None):
    preferences = preferences or {}
    if not isinstance(preferences, dict):
        raise ValueError("Terminology preferences must be an object")
    result = {}
    for concept, definition in CATALOG.items():
        choice = preferences.get(concept, definition["default"])
        if not isinstance(choice, str) or choice not in definition["choices"]:
            raise ValueError(f"Unknown {concept} terminology: {choice}")
        result[concept] = choice
    return result


def term(concept, preferences=None, *, plural=False, capitalized=False):
    selected = normalize_terminology(_preferences.get() if preferences is None else preferences)
    choice = CATALOG[concept]["choices"][selected[concept]]
    text = choice["plural" if plural else "singular"]
    return text[0].upper() + text[1:] if capitalized else text


def label(text):
    if not isinstance(text, str):
        return text
    for concept, definition in CATALOG.items():
        original = definition["choices"][definition["default"]]
        forms = sorted(original, key=lambda form: len(original[form]), reverse=True)
        alternatives = [re.escape(original[form]).replace(r"\ ", r"[\s-]+") for form in forms]

        def replace(match):
            article, space, value = match.groups()
            form = next(form for form in forms
                        if original[form] == re.sub(r"[\s-]+", " ", value.lower()))
            choice = CATALOG[concept]["choices"][normalize_terminology(_preferences.get())[concept]]
            result = choice[form]
            if " " in original[form] and "-" in value:
                result = result.replace(" ", "-")
            if value[0].isupper():
                result = result[0].upper() + result[1:]
            noun = result.upper() if value.isupper() else result
            if not article:
                return noun
            next_article = "an" if noun[0].lower() in "aeiou" else "a"
            if article.isupper() and value.isupper():
                next_article = next_article.upper()
            elif article[0].isupper():
                next_article = next_article.capitalize()
            return next_article + space + noun

        text = re.sub(r"\b(?:(a|an)(\s+))?(" + "|".join(alternatives) + r")(?!\w)",
                      replace, text, flags=re.IGNORECASE)
    return text


def report_terminology(function):
    """Accept an optional terminology keyword without persisting it in results."""
    @wraps(function)
    def write(*args, terminology=None, **kwargs):
        token = _preferences.set(normalize_terminology(terminology))
        try:
            return function(*args, **kwargs)
        finally:
            _preferences.reset(token)
    return write


def label_table(table):
    """Copy web report labels; preserve keys, system names, and numeric entries."""
    result = dict(table)
    for key in ("group_titles", "block_headers", "footnotes", "group_messages"):
        if key in result:
            result[key] = {key: label(value) for key, value in result[key].items()}
    if "initial_title" in result:
        result["initial_title"] = label(result["initial_title"])
    for group in result.get("group_ids", []):
        if not isinstance(result.get(group), list):
            continue
        rows = []
        for row in result[group]:
            formatted = dict(row)
            if "tooltip" in row:
                formatted["tooltip"] = label(row["tooltip"])
            if "rowtitle" in row and not row.get("measure", "").startswith("cmp_"):
                formatted["rowtitle"] = label(row["rowtitle"])
            rows.append(formatted)
        result[group] = rows
    return result


def add_terminology_option(parser):
    for concept, definition in CATALOG.items():
        parser.add_argument("--" + concept.replace("_", "-") + "-term",
                            choices=tuple(definition["choices"]),
                            default=definition["default"], metavar="TERM",
                            help="Report terminology: " + ", ".join(definition["choices"]))


def terminology_from_args(args):
    return {concept: getattr(args, concept + "_term") for concept in CATALOG}
