"""Tests for the vbpl HTML → legal plain-text converter."""

from scripts.html_to_legal_text import html_to_legal_text

# Minimal fixture mimicking the vbpl export: a table-of-contents block that
# lists articles 1..2, then the real body with bullet-prefixed headings.
_HTML_WITH_TOC = """
<html><body>
<p>·Chương I</p>
<p>·NHỮNG QUY ĐỊNH CHUNG</p>
<p>oĐiều 1. Phạm vi điều chỉnh</p>
<p>oĐiều 2. Đối tượng áp dụng</p>
<p>·Chương I</p>
<p>·NHỮNG QUY ĐỊNH CHUNG</p>
<p>oĐiều 1. Phạm vi điều chỉnh</p>
<p>1. Luật này quy định về sở hữu nhà ở.</p>
<p>oĐiều 2. Đối tượng áp dụng</p>
<p>1. Áp dụng với tổ chức, cá nhân.</p>
</body></html>
"""


class TestHtmlToLegalText:
    def test_strips_table_of_contents(self) -> None:
        result = html_to_legal_text(_HTML_WITH_TOC)
        # Article 1 heading must appear exactly once (ToC copy dropped).
        assert result.count("Điều 1. Phạm vi điều chỉnh") == 1
        assert result.count("Điều 2. Đối tượng áp dụng") == 1

    def test_keeps_body_content(self) -> None:
        result = html_to_legal_text(_HTML_WITH_TOC)
        assert "Luật này quy định về sở hữu nhà ở." in result
        assert "Áp dụng với tổ chức, cá nhân." in result

    def test_strips_bullet_prefixes(self) -> None:
        result = html_to_legal_text(_HTML_WITH_TOC)
        assert "oĐiều" not in result
        assert "·Chương" not in result

    def test_headings_on_own_lines(self) -> None:
        result = html_to_legal_text(_HTML_WITH_TOC)
        lines = result.split("\n")
        assert "Điều 1. Phạm vi điều chỉnh" in lines
        assert "Chương I" in lines

    def test_no_toc_single_run_preserved(self) -> None:
        html = (
            "<p>Điều 1. A</p><p>Nội dung 1.</p>"
            "<p>Điều 2. B</p><p>Nội dung 2.</p>"
        )
        result = html_to_legal_text(html)
        assert result.count("Điều 1. A") == 1
        assert result.count("Điều 2. B") == 1
        assert "Nội dung 1." in result
