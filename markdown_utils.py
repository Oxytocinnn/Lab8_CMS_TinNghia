import bleach
import markdown as md

POST_ALLOWED_TAGS = [
    "p", "br", "strong", "em", "b", "i", "a", "ul", "ol", "li",
    "blockquote", "code", "pre", "h1", "h2", "h3", "img", "table", "thead", "tbody", "tr", "th", "td"
]
POST_ALLOWED_ATTRS = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "class"]
}

COMMENT_ALLOWED_TAGS = ["p", "br", "strong", "em", "b", "i", "a", "code"]
COMMENT_ALLOWED_ATTRS = {"a": ["href", "title", "rel"]}


def render_markdown(raw_md, allowed_tags=None, allowed_attrs=None):
    tags = allowed_tags if allowed_tags is not None else POST_ALLOWED_TAGS
    attrs = allowed_attrs if allowed_attrs is not None else POST_ALLOWED_ATTRS

    html = md.markdown(raw_md or "", extensions=["fenced_code", "tables"])
    clean_html = bleach.clean(html, tags=tags, attributes=attrs, strip=True)
    return clean_html
