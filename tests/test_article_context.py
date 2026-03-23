import unittest
from unittest.mock import patch

from src.kor_companies.article_context import build_article_context
from src.kor_companies.fetcher import FetchResponse


class ArticleContextTests(unittest.TestCase):
    @patch("src.kor_companies.article_context.fetch_url")
    def test_build_article_context_filters_site_chrome(self, mock_fetch_url):
        html = """
        <html>
          <head>
            <meta
              name="description"
              content="A U.S. court ordered Krafton to reinstate executives at Unknown Worlds."
            />
          </head>
          <body>
            <header>Digital Subscriber Print Edition Latest news My Account Log out</header>
            <nav>
              Politics World Business Markets Technology Sports Opinion Travel Food Style
              Culture Facebook LinkedIn Reddit Bluesky Threads Email Print Bookmark Link copied
            </nav>
            <article>
              <h1>U.S. court rules against Korean game company over AI-led acquisition plan</h1>
              <p>
                Krafton followed ChatGPT advice during a $250 million dispute with the leadership
                of Unknown Worlds Entertainment, the studio behind Subnautica.
              </p>
              <p>
                A Delaware judge ordered Krafton to reinstate the studio executives, finding they
                had been removed unfairly as part of the acquisition process.
              </p>
              <p>
                The ruling could complicate Krafton's integration of the U.S. game developer and
                reshape how it handles the dispute.
              </p>
            </article>
            <footer>Subscribe for full access</footer>
          </body>
        </html>
        """
        mock_fetch_url.return_value = FetchResponse(
            url="https://www.japantimes.co.jp/business/2026/03/17/krafton-ai-ruling/",
            body=html.encode("utf-8"),
            content_type="text/html",
        )

        context = build_article_context(
            "https://www.japantimes.co.jp/business/2026/03/17/krafton-ai-ruling/",
            aliases=["Krafton"],
        )

        summary_text = " ".join(context.summary_sentences)
        self.assertFalse(context.low_confidence)
        self.assertIn("Krafton followed ChatGPT advice", summary_text)
        self.assertIn("A Delaware judge ordered Krafton to reinstate", summary_text)
        self.assertNotIn("Digital Subscriber", summary_text)
        self.assertNotIn("LinkedIn", summary_text)
        self.assertNotIn("Politics World Business", summary_text)

    @patch("src.kor_companies.article_context.fetch_url")
    def test_build_article_context_marks_meta_only_context_as_low_confidence(self, mock_fetch_url):
        html = """
        <html>
          <head>
            <meta name="description" content="Krafton dispute heads to Delaware court." />
          </head>
          <body>
            <header>Digital Subscriber Print Edition Latest news</header>
            <nav>Facebook LinkedIn Reddit Bluesky Threads Email Print Bookmark Link copied</nav>
          </body>
        </html>
        """
        mock_fetch_url.return_value = FetchResponse(
            url="https://www.japantimes.co.jp/business/2026/03/17/krafton-ai-ruling/",
            body=html.encode("utf-8"),
            content_type="text/html",
        )

        context = build_article_context(
            "https://www.japantimes.co.jp/business/2026/03/17/krafton-ai-ruling/",
            aliases=["Krafton"],
        )

        self.assertTrue(context.low_confidence)
        self.assertEqual(context.summary_sentences, [])
        self.assertEqual(context.meta_description, "Krafton dispute heads to Delaware court.")

    @patch("src.kor_companies.article_context.fetch_url")
    def test_build_article_context_uses_og_description_and_filters_nikkei_bio(self, mock_fetch_url):
        html = """
        <html>
          <head>
            <meta
              property="og:description"
              content="As BTS returns to the stage, HYBE faces pressure to improve governance and overseas expansion discipline."
            />
          </head>
          <body>
            <article>
              <p>
                Hae-Ryoun Kang is a Seoul-based filmmaker and journalist. She is also the host of
                the eight-part podcast Mission K-Pop produced by USG Audio and Novel.
              </p>
              <p>
                Read next Media &amp; Entertainment BTS comeback show comes to Netflix as an
                exclusive 'Dynamite' performance.
              </p>
            </article>
          </body>
        </html>
        """
        mock_fetch_url.return_value = FetchResponse(
            url="https://asia.nikkei.com/opinion/bts-back-to-showbiz-group-s-agency-hybe-demands-closer-scrutiny",
            body=html.encode("utf-8"),
            content_type="text/html",
        )

        context = build_article_context(
            "https://asia.nikkei.com/opinion/bts-back-to-showbiz-group-s-agency-hybe-demands-closer-scrutiny",
            aliases=["HYBE"],
        )

        self.assertTrue(context.low_confidence)
        self.assertEqual(context.summary_sentences, [])
        self.assertEqual(
            context.meta_description,
            "As BTS returns to the stage, HYBE faces pressure to improve governance and overseas expansion discipline.",
        )


if __name__ == "__main__":
    unittest.main()
