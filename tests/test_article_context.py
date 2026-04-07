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

    @patch("src.kor_companies.article_context.fetch_url")
    def test_build_article_context_trims_nikkei_related_and_sponsored_blocks(self, mock_fetch_url):
        html = """
        <html>
          <head>
            <meta
              property="og:description"
              content="Samsung SDI faces scrutiny in Hungary as environmental and safety concerns intensify."
            />
          </head>
          <body>
            <article>
              <p>
                Samsung SDI is facing four criminal investigations in Hungary over environmental
                and safety violations ahead of the election campaign.
                Read next Tech Korean battery makers target robots as EV demand cools.
                Sponsored Content This content was commissioned by Nikkei Global Business Bureau.
              </p>
              <p>
                The controversy has become a political burden for Prime Minister Viktor Orban as
                his opponents promise tighter oversight of battery plants. © Reuters Jens Kastner
              </p>
            </article>
          </body>
        </html>
        """
        mock_fetch_url.return_value = FetchResponse(
            url="https://asia.nikkei.com/business/automobiles/electric-vehicles/samsung-sdi-s-hungary-woes-cloud-pm-orban-s-reelection-bid",
            body=html.encode("utf-8"),
            content_type="text/html",
        )

        context = build_article_context(
            "https://asia.nikkei.com/business/automobiles/electric-vehicles/samsung-sdi-s-hungary-woes-cloud-pm-orban-s-reelection-bid",
            aliases=["Samsung SDI"],
        )

        summary_text = " ".join(context.summary_sentences)
        self.assertIn("Samsung SDI is facing four criminal investigations in Hungary", summary_text)
        self.assertIn("The controversy has become a political burden", summary_text)
        self.assertNotIn("Read next", summary_text)
        self.assertNotIn("Sponsored Content", summary_text)
        self.assertNotIn("© Reuters", summary_text)

    @patch("src.kor_companies.article_context.fetch_url")
    def test_build_article_context_falls_back_to_meta_for_nikkei_headline_blob(self, mock_fetch_url):
        html = """
        <html>
          <head>
            <meta
              name="description"
              content="HAMBURG, Germany -- The four criminal investigations into South Korean EV battery maker Samsung SDI in Hungary for alleged environmental and safety vi"
            />
            <meta
              property="og:description"
              content="Sector's key proponent faces challenger Magyar who promises tighter scrutiny."
            />
            <meta name="date" content="2026-03-26T09:41:18.000+09:00" />
            <script type="application/ld+json">
              {"@context":"https://schema.org","@type":"NewsArticle","alternativeHeadline":"Sector's key proponent faces challenger Magyar who promises tighter scrutiny.","datePublished":"2026-03-26T00:41:18.000Z"}
            </script>
          </head>
          <body>
            <article>
              <p>
                Electric vehicles Samsung SDI's Hungary woes cloud PM Orban's reelection bid
                Sector's key proponent faces challenger Magyar who promises tighter scrutiny
                Hungarian Prime Minister Viktor Orban, left, who has formed close ties with U
              </p>
            </article>
          </body>
        </html>
        """
        mock_fetch_url.return_value = FetchResponse(
            url="https://asia.nikkei.com/business/automobiles/electric-vehicles/samsung-sdi-s-hungary-woes-cloud-pm-orban-s-reelection-bid",
            body=html.encode("utf-8"),
            content_type="text/html",
        )

        context = build_article_context(
            "https://asia.nikkei.com/business/automobiles/electric-vehicles/samsung-sdi-s-hungary-woes-cloud-pm-orban-s-reelection-bid",
            aliases=["Samsung SDI"],
        )

        self.assertTrue(context.low_confidence)
        self.assertEqual(context.summary_sentences, [])
        self.assertIn("Sector's key proponent faces challenger Magyar", context.meta_description)

    @patch("src.kor_companies.article_context.fetch_url")
    def test_build_article_context_reads_text_from_structured_meta_object(self, mock_fetch_url):
        html = """
        <html>
          <head>
            <script type="application/ld+json">
              {
                "@context": "https://schema.org",
                "@type": "NewsArticle",
                "description": {
                  "@type": "WebContent",
                  "text": "SK hynix warns that AI memory demand remains strong despite broader chip market caution."
                }
              }
            </script>
          </head>
          <body>
            <header>Latest news Subscribe My account</header>
            <nav>Technology Business Markets Opinion</nav>
          </body>
        </html>
        """
        mock_fetch_url.return_value = FetchResponse(
            url="https://example.com/sk-hynix-ai-memory-demand",
            body=html.encode("utf-8"),
            content_type="text/html",
        )

        context = build_article_context(
            "https://example.com/sk-hynix-ai-memory-demand",
            aliases=["SK hynix"],
        )

        self.assertTrue(context.low_confidence)
        self.assertEqual(context.summary_sentences, [])
        self.assertEqual(
            context.meta_description,
            "SK hynix warns that AI memory demand remains strong despite broader chip market caution.",
        )


if __name__ == "__main__":
    unittest.main()
