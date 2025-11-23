import feedparser
import datetime
import os
import re

# 🔥 監視対象リスト (技術者向け)
RSS_URLS = [
    # 1. 公式ブログ (新モデル発表など)
    "https://www.anthropic.com/index.xml",
    
    # 2. Python SDK Releases (ライブラリの変更点)
    "https://github.com/anthropics/anthropic-sdk-python/releases.atom",
    
    # 3. Cookbook Commits (新しいサンプルコードの追加)
    "https://github.com/anthropics/anthropic-cookbook/commits/main.atom"
]

def clean_html(raw_html):
    """HTMLタグを除去してテキストだけにする"""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

# 保存設定
today = datetime.date.today()
os.makedirs("data", exist_ok=True)
filename = f"data/{today}.txt"

print(f"Fetching data for {today}...")

with open(filename, "w", encoding="utf-8") as f:
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            site_title = feed.feed.get('title', 'No Title')
            
            f.write(f"\n{'='*40}\n")
            f.write(f"📡 Source: {site_title}\n")
            f.write(f"{'='*40}\n\n")
            
            # 最新10件のみ取得（多すぎるとトークン圧迫するため）
            for entry in feed.entries[:10]:
                # 日付取得 (AtomとRSSで場所が違うため調整)
                date_str = entry.get('updated', '') or entry.get('published', '')
                date_str = date_str[:10] # YYYY-MM-DDだけ取る
                
                title = entry.get('title', 'No Title')
                link = entry.get('link', '')
                
                # 内容の取得（GitHubのFeedはcontentに入る）
                content = ''
                if 'content' in entry:
                    content = entry.content[0].value
                elif 'summary' in entry:
                    content = entry.summary
                
                # HTML除去して整形
                text_content = clean_html(content)[:600] # 長すぎる場合はカット
                
                f.write(f"📌 [{date_str}] {title}\n")
                f.write(f"🔗 {link}\n")
                f.write(f"📝 Detail: {text_content}\n")
                f.write("-" * 20 + "\n")
                
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            f.write(f"Error reading {url}\n")

print(f"Saved to {filename}")
