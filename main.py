print("🚀 main.py est bien exécuté")

import feedparser
import urllib.request
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

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

# ============================================================
# COLLECTE DES ARTICLES
# ============================================================
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
                import re
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

# ============================================================
# RÉSUMÉ IA VIA GEMINI
# ============================================================
def generate_ai_summary(articles_by_source):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("⚠️ Clé Gemini manquante, résumé de secours")
        return generer_resume_secours(articles_by_source)

    titres = []
    for articles in articles_by_source.values():
        for article in articles[:8]:
            titres.append(article["title"])

    if not titres:
        return "Aucun article disponible pour générer un résumé."

    prompt = (
        "Tu es un assistant journalistique francophone. "
        "Voici les titres des principaux articles du jour issus de trois journaux "
        "(Le Monde, Sud Ouest, Courrier International). "
        "Rédige un résumé global de l'actualité du moment en 3-4 phrases, "
        "en français, de manière neutre et factuelle. "
        "Ne cite pas les journaux, synthétise simplement les grandes tendances.\n\n"
        "Titres :\n" + "\n".join(titres)
    )

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 300}
    }).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            texte = data["candidates"][0]["content"]["parts"][0]["text"]
            print("✅ Résumé Gemini généré")
            return texte
    except Exception as e:
        print(f"⚠️ Erreur Gemini : {e}")
        return generer_resume_secours(articles_by_source)

def generer_resume_secours(articles_by_source):
    import re
    from collections import Counter
    STOP_WORDS = {
        "le", "la", "les", "de", "des", "du", "un", "une", "et", "en", "à",
        "pour", "dans", "sur", "au", "aux", "par", "avec", "ce", "ces",
        "est", "sont", "plus", "moins", "que", "qui", "dont", "entre",
        "direct", "images", "année", "nouvelle", "leurs", "être", "après"
    }
    words = []
    for articles in articles_by_source.values():
        for article in articles:
            title = article["title"].lower()
            title = re.sub(r"[^\w\s]", "", title)
            for word in title.split():
                if len(word) > 3 and word.isalpha() and word not in STOP_WORDS:
                    words.append(word)
    if not words:
        return "L'actualité du jour est relativement calme, sans thème dominant identifiable."
    counter = Counter(words)
    themes = ", ".join(w for w, _ in counter.most_common(5))
    return (
        f"L'actualité des dernières 24 heures est marquée par plusieurs thèmes, "
        f"notamment : {themes}. "
        "Ces sujets reflètent les tensions internationales et les débats du moment."
    )

# ============================================================
# GÉNÉRATION HTML
# ============================================================
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

def render_article(a):
    resume_html = f'<div class="news-resume">{a["resume"]}</div>' if a.get("resume") else ""
    date_html   = f'<div class="news-date">{formater_date(a["date"])}</div>' if a.get("date") else ""
    return f'''
    <div class="news-item">
      <a class="news-titre" href="{a["link"]}" target="_blank" rel="noopener">{a["title"]}</a>
      {resume_html}
      {date_html}
    </div>'''

def formater_date(date_str):
    try:
        from email.utils import parsedate_to_datetime
        d = parsedate_to_datetime(date_str)
        return d.strftime("%d %b, %H:%M")
    except:
        return ""

def generate_html(articles_by_source, summary):
    print("🧠 generate_html() appelée")
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
    .card {{ background: #1a1d2e; border: 1px solid #2a2d3e; border-radius: 14px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.4); }}
    body.light .card {{ background: #ffffff; border-color: #dde2ee; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
    .card h2 {{ font-size: 1rem; font-weight: 600; color: #8892a4; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid #2a2d3e; }}
    body.light .card h2 {{ border-color: #dde2ee; }}
    .resume-ia {{ font-size: 0.95rem; line-height: 1.7; color: #e8eaf0; }}
    body.light .resume-ia {{ color: #1a1d2e; }}
    .ia-badge {{ display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 10px; border-radius: 20px; margin-bottom: 12px; }}
    .news-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
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
    <div class="card">
      <h2>🤖 Résumé de l'actualité</h2>
      <div class="ia-badge">✨ Généré par IA</div>
      <div class="resume-ia">{summary}</div>
    </div>
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

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    articles = fetch_articles()
    summary  = generate_ai_summary(articles)
    generate_html(articles, summary)
