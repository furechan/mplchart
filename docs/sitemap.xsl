<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:sm="http://www.sitemaps.org/schemas/sitemap/0.9">
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html>
      <head>
        <title>Sitemap - mplchart</title>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <style>
          :root {
            color-scheme: light dark;
            --bg: #ffffff;
            --fg: #1f2933;
            --muted: #6b7a8c;
            --accent: #546e7a;
            --border: #e0e5ea;
            --row-hover: #f4f6f8;
          }
          @media (prefers-color-scheme: dark) {
            :root {
              --bg: #1e2129;
              --fg: #e3e6eb;
              --muted: #9aa5b1;
              --accent: #90a4ae;
              --border: #343a46;
              --row-hover: #262b35;
            }
          }
          body {
            margin: 0;
            background: var(--bg);
            color: var(--fg);
            font: 15px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          }
          main {
            max-width: 48rem;
            margin: 0 auto;
            padding: 2.5rem 1.25rem;
          }
          h1 {
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0 0 0.25rem;
          }
          p.note {
            color: var(--muted);
            margin: 0 0 1.5rem;
            font-size: 0.85rem;
          }
          table {
            width: 100%;
            border-collapse: collapse;
          }
          th {
            text-align: left;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--muted);
            padding: 0.5rem 0.75rem;
            border-bottom: 2px solid var(--border);
          }
          td {
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid var(--border);
            word-break: break-all;
          }
          tr:hover td {
            background: var(--row-hover);
          }
          td.lastmod {
            white-space: nowrap;
            color: var(--muted);
            font-size: 0.85rem;
          }
          a {
            color: var(--accent);
            text-decoration: none;
          }
          a:hover {
            text-decoration: underline;
          }
        </style>
      </head>
      <body>
        <main>
          <h1>Sitemap</h1>
          <p class="note">
            This XML sitemap lists <xsl:value-of select="count(sm:urlset/sm:url)"/> pages of the
            <a href="https://furechan.github.io/mplchart/">mplchart</a> documentation.
            It is meant for search engines; this page is a styled view for humans.
          </p>
          <table>
            <thead>
              <tr>
                <th>URL</th>
                <th>Last modified</th>
              </tr>
            </thead>
            <tbody>
              <xsl:for-each select="sm:urlset/sm:url">
                <tr>
                  <td>
                    <a href="{sm:loc}"><xsl:value-of select="sm:loc"/></a>
                  </td>
                  <td class="lastmod">
                    <xsl:value-of select="sm:lastmod"/>
                  </td>
                </tr>
              </xsl:for-each>
            </tbody>
          </table>
        </main>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
