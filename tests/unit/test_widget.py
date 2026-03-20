"""Unit tests for the embeddable chat widget (RA-20)."""
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

STATIC_DIR = Path(__file__).parent.parent.parent / "static"
WIDGET_JS = STATIC_DIR / "widget.js"
TEST_HTML = STATIC_DIR / "test.html"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def widget_js_content():
    return WIDGET_JS.read_text()


@pytest.fixture(scope="module")
def test_html_soup():
    return BeautifulSoup(TEST_HTML.read_text(), "html.parser")


# ---------------------------------------------------------------------------
# widget.js — structure & required features
# ---------------------------------------------------------------------------

def test_widget_js_exists():
    assert WIDGET_JS.exists(), "static/widget.js must exist"


def test_widget_has_session_storage(widget_js_content):
    assert "sessionStorage" in widget_js_content, "widget must use sessionStorage for session ID"


def test_widget_has_tenant_id_config(widget_js_content):
    assert "data-tenant-id" in widget_js_content, "widget must read data-tenant-id attribute"


def test_widget_has_restaurant_name_config(widget_js_content):
    assert "data-restaurant-name" in widget_js_content


def test_widget_has_theme_color_config(widget_js_content):
    assert "data-theme-color" in widget_js_content


def test_widget_posts_to_api_chat(widget_js_content):
    assert "/api/chat" in widget_js_content, "widget must POST to /api/chat"


def test_widget_sends_tenant_header(widget_js_content):
    assert "X-Tenant-ID" in widget_js_content, "widget must send X-Tenant-ID header"


def test_widget_has_floating_button(widget_js_content):
    assert "ra-widget-btn" in widget_js_content


def test_widget_has_message_panel(widget_js_content):
    assert "ra-widget-panel" in widget_js_content


def test_widget_has_close_button(widget_js_content):
    assert "ra-widget-close" in widget_js_content


def test_widget_has_input_and_send(widget_js_content):
    assert "ra-widget-input" in widget_js_content
    assert "ra-widget-send" in widget_js_content


def test_widget_is_iife(widget_js_content):
    """Widget must be wrapped in IIFE to avoid polluting global scope."""
    assert "(function" in widget_js_content or "(() =>" in widget_js_content


def test_widget_has_responsive_styles(widget_js_content):
    assert "@media" in widget_js_content, "widget must have responsive CSS media queries"


def test_widget_has_escape_key_close(widget_js_content):
    assert "Escape" in widget_js_content, "widget must close on Escape key"


def test_widget_has_enter_key_send(widget_js_content):
    assert "Enter" in widget_js_content, "widget must send on Enter key"


def test_widget_uses_session_id_in_request(widget_js_content):
    assert "session_id" in widget_js_content, "widget must include session_id in API request"


# ---------------------------------------------------------------------------
# test.html — demo page structure
# ---------------------------------------------------------------------------

def test_test_html_exists():
    assert TEST_HTML.exists(), "static/test.html must exist"


def test_test_html_embeds_widget_script(test_html_soup):
    scripts = test_html_soup.find_all("script", src=True)
    widget_scripts = [s for s in scripts if "widget.js" in s.get("src", "")]
    assert widget_scripts, "test.html must embed widget.js via <script src>"


def test_test_html_has_tenant_id(test_html_soup):
    scripts = test_html_soup.find_all("script", attrs={"data-tenant-id": True})
    assert scripts, "test.html widget script must have data-tenant-id attribute"


def test_test_html_has_restaurant_name(test_html_soup):
    scripts = test_html_soup.find_all("script", attrs={"data-restaurant-name": True})
    assert scripts, "test.html widget script must have data-restaurant-name attribute"


def test_test_html_has_theme_color(test_html_soup):
    scripts = test_html_soup.find_all("script", attrs={"data-theme-color": True})
    assert scripts, "test.html widget script must have data-theme-color attribute"


def test_test_html_valid_structure(test_html_soup):
    assert test_html_soup.find("html") is not None
    assert test_html_soup.find("head") is not None
    assert test_html_soup.find("body") is not None


# ---------------------------------------------------------------------------
# api/main.py — StaticFiles mount
# ---------------------------------------------------------------------------

def test_api_main_mounts_static_files():
    main_py = Path(__file__).parent.parent.parent / "api" / "main.py"
    content = main_py.read_text()
    assert "StaticFiles" in content, "api/main.py must mount StaticFiles"
    assert '"/static"' in content or "'/static'" in content
