"""
Project Trinetra - HTML Sanitizer.

Strips dangerous content from user-supplied HTML before parsing.
Uses bleach to remove scripts, event handlers, and unsafe URIs
while preserving table-structure tags needed by the chart parser.
"""

from __future__ import annotations

import re

import bleach


# Tags we need to keep for chart table parsing
ALLOWED_TAGS: list[str] = [
    "table", "thead", "tbody", "tfoot", "tr", "th", "td",
    "caption", "colgroup", "col",
    "div", "span", "p", "br", "b", "strong", "i", "em",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "a", "font",
]

# Attributes we keep (only safe, presentational ones)
ALLOWED_ATTRIBUTES: dict[str, list[str]] = {
    "*": ["class", "id", "style"],
    "a": ["href", "title"],
    "td": ["colspan", "rowspan", "class"],
    "th": ["colspan", "rowspan", "class"],
    "col": ["span"],
    "font": ["color", "size"],
}

# Regex to strip event-handler attributes that bleach might miss
_EVENT_HANDLER_RE = re.compile(
    r"""\s+on\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]*)""",
    re.IGNORECASE,
)

# Regex to remove javascript: URLs anywhere in attribute values
_JS_URL_RE = re.compile(
    r"""javascript\s*:""",
    re.IGNORECASE,
)


def sanitize_html(raw_html: str) -> str:
    """
    Sanitize raw HTML input for safe chart parsing.

    Steps:
    1. Strip <script> and <style> blocks entirely (content + tags).
    2. Remove on* event-handler attributes.
    3. Remove javascript: URLs.
    4. Run bleach.clean to whitelist only safe tags and attributes.

    Returns:
        Cleaned HTML string safe for parsing.
    """
    if not raw_html:
        return ""

    # 1. Remove <script>...</script> and <style>...</style> blocks
    text = re.sub(r"<script[^>]*>.*?</script>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Strip event handlers (onclick, onload, onerror, etc.)
    text = _EVENT_HANDLER_RE.sub("", text)

    # 3. Remove javascript: pseudo-protocol from any remaining attribute
    text = _JS_URL_RE.sub("", text)

    # 4. Bleach final pass – only allow safe tags/attributes
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
        strip_comments=True,
    )

    return cleaned


def strip_all_html(text: str) -> str:
    """Remove ALL HTML tags and return plain text."""
    if not text:
        return ""
    return bleach.clean(text, tags=[], strip=True).strip()
