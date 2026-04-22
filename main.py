print("🚀 main.py est bien exécuté")

import feedparser
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

SOURCES = {
    "Le Monde": "https://www.lemonde.fr/rss/une.xml",
    "Sud Ouest": "https://www.sudouest.fr/rss.xml",
    "Courrier International": "https://www.courrierinternational.com/feed/all/rss.xml"
}

EMOJIS = {
    "Le Monde": "🔵",
    "Sud Ouest": "🟠",
    "Courrier International": "🟢"
}

def fetch_articles():
    articles_by_source = {}
    limit = datetime.now(timezone.utc) - timedelta(hours=24)
    for source, url in SOURCES.items():
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries:
            if hasattr(entry, "published_parsed"):
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if published < limit:
                    continue
            resume = ""
            if hasattr(entry, "summary"):
                clean = re.sub(r"<[^>]+>", "", entry.summary)
                resume = clean.strip()[:200] + ("…" if len(clean) > 200 else "")
            articles.append({
                "title": entry.title,
                "link":  entry.link,
                "resume": resume,
                "date": entry.get("published", "")
            })
        articles_by_source[source] = articles
        print(f"✅ {source} : {len(articles)} articles")
    return articles_by_source

def render_article(a):
    resume_html = f'<div class="news-resume">{a["resume"]}</div>' if a.get("resume") else ""
    date_html   = f'<div class="news-date">{formater_date(a["date"])}</div>' if a.get("date") else ""
    return f'''
    <div class="news-item">
      <a class="news-titre" href="{a["link"]}" target="_blank" rel="noopener">{a["title"]}</a>
      {resume_html}
      {date_html}
    </div>'''

def render_articles(articles, source_id):
    html = ""
    visibles = articles[:5]
    cachees  = articles[5:]
    for a in visibles:
        html += render_article(a)
    if cachees:
        html += f'<div id="more-{source_id}" style="display:none">'
        for a in cachees:
            html += render_article(a)
        html += f'</div>'
        html += f'<button class="btn-more" onclick="afficherPlus(\'{source_id}\')">▼ Afficher plus ({len(cachees)})</button>'
    return html

def formater_date(date_str):
    try:
        from email.utils import parsedate_to_datetime
        d = parsedate_to_datetime(date_str)
        return d.strftime("%d %b, %H:%M")
    except:
        return ""

def generate_html(articles_by_source):
    generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")

    sections = ""
    for source, articles in articles_by_source.items():
        source_id = source.lower().replace(" ", "_")
        emoji = EMOJIS.get(source, "📰")
        sections += f'''
        <div class="card">
          <h2>{emoji} {source}</h2>
          <div class="news-list" id="{source_id}">
            {render_articles(articles, source_id)}
          </div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>News & Actus</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', 'Segoe UI', Arial, sans-serif; background: #0f1117; color: #e8eaf0; min-height: 100vh; transition: background 0.3s, color 0.3s; }}
    body.light {{ background: #f0f2f7; color: #1a1d2e; }}
    header {{ display: flex; justify-content: space-between; align-items: center; padding: 14px 24px; background: #1a1d2e; border-bottom: 1px solid #2a2d3e; position: sticky; top: 0; z-index: 100; flex-wrap: wrap; gap: 10px; }}
    body.light header {{ background: #ffffff; border-color: #dde2ee; }}
    .logo {{ font-size: 1.2rem; font-weight: 700; color: #3d8ef8; }}
    .header-right {{ display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }}
    #lastUpdate {{ font-size: 0.78rem; color: #8892a4; }}
    #toggleMode {{ background: #22263a; color: #e8eaf0; border: 1px solid #2a2d3e; padding: 7px 14px; border-radius: 20px; cursor: pointer; font-size: 0.82rem; transition: all 0.2s; }}
    body.light #toggleMode {{ background: #e8eaf0; color: #1a1d2e; border-color: #dde2ee; }}
    #toggleMode:hover {{ background: #3d8ef8; color: #fff; }}
    main {{ max-width: 1400px; margin: 0 auto; padding: 24px 16px; display: flex; flex-direction: column; gap: 24px; }}
    .news-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
    .card {{ background: #1a1d2e; border: 1px solid #2a2d3e; border-radius: 14px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.4); }}
    body.light .card {{ background: #ffffff; border-color: #dde2ee; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
    .card h2 {{ font-size: 1rem; font-weight: 600; color: #8892a4; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid #2a2d3e; }}
    body.light .card h2 {{ border-color: #dde2ee; }}
    .news-list {{ display: flex; flex-direction: column; }}
    .news-item {{ padding: 12px 0; border-bottom: 1px solid #2a2d3e; display: flex; flex-direction: column; gap: 5px; }}
    body.light .news-item {{ border-color: #dde2ee; }}
    .news-item:first-child {{ padding-top: 0; }}
    .news-item:last-child {{ border-bottom: none; padding-bottom: 0; }}
    .news-titre {{ font-size: 0.88rem; color: #e8eaf0; line-height: 1.45; font-weight: 600; text-decoration: none; display: block; }}
    body.light .news-titre {{ color: #1a1d2e; }}
    .news-titre:hover {{ color: #3d8ef8; }}
    .news-resume {{ font-size: 0.80rem; color: #8892a4; line-height: 1.4; }}
    body.light .news-resume {{ color: #5a6478; }}
    .news-date {{ font-size: 0.70rem; color: #5a6478; }}
    .btn-more {{ margin-top: 12px; background: none; border: 1px solid #2a2d3e; color: #3d8ef8; padding: 6px 14px; border-radius: 20px; cursor: pointer; font-size: 0.8rem; width: 100%; transition: all 0.2s; }}
    body.light .btn-more {{ border-color: #dde2ee; }}
    .btn-more:hover {{ background: #3d8ef8; color: #fff; }}
    @media (max-width: 900px) {{ .news-grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body class="dark">
  <header>
    <span class="logo">📰 News & Actus</span>
    <div class="header-right">
      <span id="lastUpdate">Mise à jour : {generated_at}</span>
      <button id="toggleMode" onclick="toggleMode()">☀️ Mode clair</button>
    </div>
  </header>
  <main>
    <div class="news-grid">
      {sections}
    </div>
  </main>
  <script>
    function toggleMode() {{
      const body = document.body;
      const btn  = document.getElementById("toggleMode");
      if (body.classList.contains("dark")) {{
        body.classList.replace("dark", "light");
        btn.textContent = "🌙 Mode sombre";
      }} else {{
        body.classList.replace("light", "dark");
        btn.textContent = "☀️ Mode clair";
      }}
    }}
    function afficherPlus(sourceId) {{
      const more = document.getElementById("more-" + sourceId);
      const btn  = more.nextElementSibling;
      if (more.style.display === "none") {{
        more.style.display = "block";
        btn.textContent = "▲ Afficher moins";
      }} else {{
        more.style.display = "none";
        btn.textContent = "▼ Afficher plus (" + more.querySelectorAll(".news-item").length + ")";
      }}
    }}
  </script>
</body>
</html>'''

    output_path = Path("index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Fichier index.html écrit")

if __name__ == "__main__":
    articles = fetch_articles()
    generate_html(articles)
