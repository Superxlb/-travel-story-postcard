"""Run with: python -m unittest discover -s tests -v (no extra dependencies)."""
import base64
import hashlib
import importlib.util
import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("renderer", ROOT / "scripts" / "render_postcard.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.tags, self.attributes, self.text = [], [], []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.append((tag, dict(attrs)))

    def handle_data(self, text):
        self.text.append(text)


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.data = json.loads((ROOT / "demo" / "example-content.json").read_text(encoding="utf-8"))
        self.source = ROOT / "demo" / "sample.jpg"
        self.original_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def render(self, image=True, **kwargs):
        data_file = self.path / "content.json"
        data_file.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        output = self.path / "我的成品.html"
        renderer.render(data_file, output, self.source if image else None, **kwargs)
        return output, Document(output.read_text(encoding="utf-8"))

    def test_embedded_image_preserves_source_and_has_no_external_resources(self):
        output, doc = self.render()
        images = [a for tag, a in doc.attributes if tag == "img"]
        self.assertEqual(len(images), 1)
        uri = images[0]["src"]
        self.assertTrue(uri.startswith("data:image/jpeg;base64,"))
        self.assertEqual(base64.b64decode(uri.split(",", 1)[1]), self.source.read_bytes())
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.original_hash)
        self.assertNotIn("script", doc.tags)
        self.assertNotIn("link", doc.tags)
        for _, attrs in doc.attributes:
            for key in ("src", "href"):
                self.assertFalse(attrs.get(key, "").startswith(("http:", "https:", "//", "file:")))
        self.assertNotIn("{{", output.read_text(encoding="utf-8"))
        self.assertNotIn("地点：", "".join(doc.text))
        self.assertNotIn("日期：", "".join(doc.text))
        self.assertNotIn("署名：", "".join(doc.text))

    def test_user_markup_is_displayed_as_text_not_executed(self):
        payload = '<script>alert("x")</script><img src=x onerror="alert(1)"> & {{TITLE}}'
        for key in ("title", "caption", "recipient", "story", "wish", "photo_alt", "signature", "credit"):
            self.data[key] = payload
        _, doc = self.render()
        self.assertNotIn("script", doc.tags)
        self.assertEqual(doc.tags.count("img"), 1)
        self.assertIn(payload, "".join(doc.text))
        self.assertFalse(any(key.startswith("on") for _, attrs in doc.attributes for key in attrs))
        self.assertEqual(next(attrs["alt"] for tag, attrs in doc.attributes if tag == "img"), payload)

    def test_relative_image_is_portable_copy(self):
        output, doc = self.render(image_mode="relative")
        src = next(attrs["src"] for tag, attrs in doc.attributes if tag == "img")
        copied = output.parent / unquote(src)
        self.assertEqual(copied.read_bytes(), self.source.read_bytes())
        self.assertNotEqual(copied.resolve(), self.source.resolve())

    def test_description_only_never_fakes_a_photo(self):
        _, doc = self.render(image=False, description_only=True)
        self.assertNotIn("img", doc.tags)
        self.assertIn("未附照片", "".join(doc.text))

    def test_refuses_overwrite_and_invalid_data(self):
        output, _ = self.render()
        before = output.read_bytes()
        with self.assertRaises(ValueError):
            renderer.render(self.path / "content.json", output, self.source)
        self.assertEqual(output.read_bytes(), before)
        self.data["story"] = ["wrong type"]
        data_file = self.path / "invalid.json"
        data_file.write_text(json.dumps(self.data), encoding="utf-8")
        with self.assertRaises(ValueError):
            renderer.render(data_file, self.path / "invalid.html", self.source)
        self.assertFalse((self.path / "invalid.html").exists())

    def test_svg_or_missing_image_is_rejected(self):
        with self.assertRaises(ValueError):
            renderer.image_kind(b'<svg onload="alert(1)"></svg>')
        data_file = self.path / "content.json"
        data_file.write_text(json.dumps(self.data), encoding="utf-8")
        with self.assertRaises(ValueError):
            renderer.render(data_file, self.path / "missing.html")


if __name__ == "__main__":
    unittest.main()
