#!/usr/bin/env python3
"""Offline postcard renderer. Python 3.8+, standard library only."""
import argparse
import base64
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
TOKEN = re.compile(r"\{\{([A-Z_]+)\}\}")


def escape(value):
    # Encode braces too: literal user {{text}} must not look like template residue.
    return html.escape(value, quote=True).replace("{", "&#123;").replace("}", "&#125;")


def image_kind(data):
    if data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9"):
        return "image/jpeg", ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif", ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", ".webp"
    raise ValueError("Unsupported image: use an actual JPEG, PNG, GIF, or WebP file.")


def render(data_path, output, image_path=None, image_mode="embed", description_only=False):
    data_path, output = Path(data_path).resolve(), Path(output).resolve()
    template_path = ROOT / "assets" / "postcard-template.html"
    if output.suffix.lower() != ".html":
        raise ValueError("Output must use .html.")
    if output.exists():
        raise ValueError("Output already exists; choose a new filename.")
    data = json.loads(data_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Data must be a JSON object.")
    required = ("title", "caption", "recipient", "story", "wish", "photo_alt")
    optional = ("location", "date", "signature", "credit")
    for key in required + optional:
        value = data.get(key, "")
        if not isinstance(value, str) or (key in required and not value.strip()):
            raise ValueError("Expected text field: " + key)
    if bool(image_path) == bool(description_only):
        raise ValueError("Choose either --image or --description-only.")
    image_bytes, copied_image = None, None
    if image_path:
        source = Path(image_path).resolve()
        if output in (source, data_path, template_path.resolve()):
            raise ValueError("Never overwrite source files.")
        image_bytes = source.read_bytes()
        mime, suffix = image_kind(image_bytes)
        if image_mode == "relative":
            copied_image = output.with_name(output.stem + "-photo" + suffix)
            if copied_image.exists() or copied_image == source:
                raise ValueError("Companion image already exists; choose a new output name.")
            src = quote(copied_image.name)
        else:
            src = "data:" + mime + ";base64," + base64.b64encode(image_bytes).decode("ascii")
        photo = '<img src="' + escape(src) + '" alt="' + escape(data["photo_alt"]) + '">'
    else:
        photo = '<div class="missing">未附照片 · 根据画面描述创作<br>' + escape(data["photo_alt"]) + '</div>'
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", data["story"]) if p.strip()]
    values = {
        "TITLE": escape(data["title"]), "CAPTION": escape(data["caption"]),
        "RECIPIENT": escape(data["recipient"]), "WISH": escape(data["wish"]),
        "PHOTO_HTML": photo,
        "STORY_HTML": "\n".join("<p>" + escape(p).replace("\n", "<br>") + "</p>" for p in paragraphs),
        "META_HTML": "<br>".join(label + "：" + escape(data[key]) for key, label in
                                  (("location", "地点"), ("date", "日期"), ("signature", "署名")) if data.get(key)),
        "CREDIT": escape(data.get("credit", "")),
    }
    template = template_path.read_text(encoding="utf-8")
    if set(TOKEN.findall(template)) != set(values):
        raise ValueError("Template tokens do not match renderer fields.")
    result = TOKEN.sub(lambda match: values[match.group(1)], template)
    if "{{" in result or "}}" in result:
        raise ValueError("Unresolved template marker.")
    output.parent.mkdir(parents=True, exist_ok=True)
    if copied_image:
        with copied_image.open("xb") as stream:
            stream.write(image_bytes)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(result)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="UTF-8 JSON")
    parser.add_argument("--output", required=True, help="New HTML filename")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", help="Local JPEG/PNG/GIF/WebP")
    group.add_argument("--description-only", action="store_true")
    parser.add_argument("--image-mode", choices=("embed", "relative"), default="embed")
    args = parser.parse_args()
    try:
        result = render(args.data, args.output, args.image, args.image_mode, args.description_only)
    except (OSError, ValueError) as error:
        print("Cannot render: " + str(error), file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
