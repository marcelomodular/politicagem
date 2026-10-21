import unittest

from security_utils import is_safe_embed_url


class SafeEmbedUrlTestCase(unittest.TestCase):
    def test_accepts_https_urls(self):
        self.assertTrue(is_safe_embed_url('https://apublica.org/noticia/'))
        self.assertTrue(is_safe_embed_url('http://example.com/x?y=1'))

    def test_rejects_javascript_scheme(self):
        self.assertFalse(is_safe_embed_url('javascript:alert(1)'))
        self.assertFalse(is_safe_embed_url('JavaScript:alert(1)'))
        self.assertFalse(is_safe_embed_url('  javascript:alert(1)'))

    def test_rejects_data_and_vbscript_scheme(self):
        self.assertFalse(is_safe_embed_url('data:text/html,<script>alert(1)</script>'))
        self.assertFalse(is_safe_embed_url('vbscript:msgbox(1)'))

    def test_rejects_credentials(self):
        self.assertFalse(is_safe_embed_url('https://user:pass@example.com/'))

    def test_rejects_empty_and_hostless(self):
        self.assertFalse(is_safe_embed_url(''))
        self.assertFalse(is_safe_embed_url('https:///path'))

    def test_allows_unicode_and_query_params(self):
        self.assertTrue(is_safe_embed_url('https://example.com/цена?a=1&b=2#top'))


if __name__ == '__main__':
    unittest.main()
