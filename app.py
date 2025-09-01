import subprocess
import json
import os
from flask import Flask, request, jsonify, render_template_string, redirect
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote

app = Flask(__name__)

# jsonではバックスラッシュを使用する記号などはバックスラッシュをそのままにしたい
print(json.dumps({"message": "デバッグログを追加して、どこまで実行されるか確認します。", "user": "カカオマメ"}))

# プロキシのベースURL (例: https://[あなたのドメイン].vercel.app)
def get_proxy_base_url():
    host = request.headers.get('Host')
    protocol = request.headers.get('X-Forwarded-Proto', 'http')
    return f"{protocol}://{host}"

# YouTubeの特定のパスをリスト化
YOUTUBE_PATHS = ["watch", "channel", "c", "@", "search", "live", "playlist", "tag", "shorts"]

# 動画埋め込み用の設定URL
CONFIG_URL = 'https://raw.githubusercontent.com/siawaseok3/wakame/master/video_config.json'
EMBED_BASE_URL = 'https://www.youtubeeducation.com/embed/'
VIDEO_CONFIG = None
print(f"GITHUBのリンク:{CONFIG_URL},YOUTUBEの埋め込みリンク{EMBED_BASE_URL},Noneか？={VIDEO_CONFIG}")

# video_config.jsonの内容を読み込む関数
def load_video_config():
    global VIDEO_CONFIG
    try:
        result = subprocess.run(["curl", "-s", CONFIG_URL], capture_output=True, text=True, check=True)
        VIDEO_CONFIG = json.loads(result.stdout)
        print("✅ 動画設定ファイル読み込みに成功しました。")
    except Exception as e:
        print(f"❌ 動画設定ファイルの読み込みに失敗しました: {e}")
        VIDEO_CONFIG = {"params": ""}

load_video_config()

# --- ホームページ関連のHTML ---
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ホームページ - pokemoguプロジェクト</title>
    <link rel="apple-touch-icon" sizes="180x180" href="https://kakaomames.github.io/Minecraft-flask-app/static/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="https://kakaomames.github.io/Minecraft-flask-app/static/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="https://kakaomames.github.io/Minecraft-flask-app/static/favicon-16x16.png">
    <link rel="manifest" href="https://kakaomames.github.io/Minecraft-flask-app/static/site.webmanifest">
    <link rel="stylesheet" href="https://kakaomames.github.io/Minecraft-flask-app/static/style.css">
</head>
<body>
    <header>
        <h1>HOME🏠</h1>
        <nav>
            <ul>
                <li><a href="/home">ホーム</a></li>
            </ul>
        </nav>
    </header>
    <main>
    </main>
    <footer>
        <p>&copy; 2025  pokemoguプロジェクト</p>
    </footer>
</body>
</html>
"""

HOME_HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ホーム - pokemoguプロジェクト</title>
    <link rel="apple-touch-icon" sizes="180x180" href="https://kakaomames.github.io/Minecraft-flask-app/static/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="https://kakaomames.github.io/Minecraft-flask-app/static/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="https://kakaomames.github.io/Minecraft-flask-app/static/favicon-16x16.png">
    <link rel="manifest" href="https://kakaomames.github.io/Minecraft-flask-app/static/site.webmanifest">
    <link rel="stylesheet" href="https://kakaomames.github.io/Minecraft-flask-app/static/style.css">
    <style>
        .textbox-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 50vh;
        }
        .search-box {
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            width: 80%;
            max-width: 400px;
        }
    </style>
</head>
<body>
    <header>
        <h1>HOME🏠</h1>
        <nav>
            <ul>
                <li><a href="/">トップページ</a></li>
            </ul>
        </nav>
    </header>
    <main>
        <div class="textbox-container">
            <form action="/search" method="get">
                <input type="text" name="q" class="search-box" placeholder="URLまたは検索テキストを入力...">
                <button type="submit" style="display:none;">検索</button>
            </form>
        </div>
    </main>
    <footer>
        <p>&copy; 2025  pokemoguプロジェクト</p>
    </footer>
</body>
</html>
"""

def is_url(text):
    text = text.lower()
    return text.startswith(("http://", "https://", "www.", "m."))

# --- ルートの定義 ---
@app.route('/')
def index():
    print("➡️ ルートページへのリクエストを受信しました。")
    return render_template_string(INDEX_HTML)

@app.route('/home')
def home():
    print("➡️ ホームページへのリクエストを受信しました。")
    return render_template_string(HOME_HTML)

@app.route('/search', methods=['GET'])
def handle_search():
    print("➡️ 検索リクエストを受信しました。")
    query = request.args.get('q')
    if not query:
        print("⚠️ クエリパラメータ'q'が空です。ホームにリダイレクトします。")
        return redirect('/home')
    
    if is_url(query):
        print(f"🔗 入力をURLと判断しました: {query}")
        return redirect(f'/?url={quote(query, safe="")}')
    else:
        print(f"🔎 入力を検索テキストと判断しました: {query}")
        google_search_url = f"https://www.google.com/search?q={quote(query, safe='')}"
        print(f"➡️ Google検索URLを構築しました: {google_search_url}")
        return redirect(f"/?url={quote(google_search_url, safe='')}")

@app.route('/<path:path>', methods=['GET', 'POST'])
def proxy_request(path):
    print(f"➡️ プロキシリクエストを受信しました。パス: {path}")
    query_string = request.query_string.decode('utf-8')
    target_url = None

    url_param = request.args.get('url')
    if url_param:
        target_url = url_param
        print(f"🎯 URLパラメータからターゲットURLを取得: {target_url}")
    else:
        path_segments = path.split('/')
        if path_segments[0] in YOUTUBE_PATHS:
            youtube_base_url = "https://www.youtube.com"
            target_url = f"{youtube_base_url}/{path}"
            if query_string:
                target_url += f"?{query_string}"
            print(f"🎯 YouTubeパスからターゲットURLを構築: {target_url}")
            print(f"{youtube_base_url}/{path}")
        else:
            if path.startswith(("http://", "https://", "www.", "m.")):
                if not path.startswith(("http://", "https://")):
                    path = "https://" + path
                target_url = path
                if query_string:
                    target_url += f"?{query_string}"
                print(f"🎯 有効なURLパスからターゲットURLを構築: {target_url}")
            else:
                print(f"🚫 無効なURLまたはパスです: {path}")
                return jsonify({"error": "無効なURLまたはパスです。"}), 400

    data = request.get_data()
    curl_command = ["curl", "-s", "-L", "--max-time", "30", "-X", request.method, target_url]
    
    if data:
        curl_command.extend(["-d", data.decode('utf-8')])
    
    print(f"🚀 curlコマンド実行中... コマンド: {curl_command}")

    try:
        result = subprocess.run(
            curl_command,
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ curlコマンド実行成功。")
        print(f"--- curl標準出力開始（長さ：{len(result.stdout)}） ---")
        print(result.stdout[:500]) # 先頭500文字のみ表示
        print("--- curl標準出力終了 ---")
        print(f"--- curl標準エラー出力開始 ---")
        print(result.stderr)
        print("--- curl標準エラー出力終了 ---")
        
        content = result.stdout
        
        content_type = 'text/html' if 'text/html' in result.stderr else ''
        print(f"📝 取得したコンテンツタイプ: {content_type}")

        if 'text/html' in content_type:
            print("🔍 HTML解析開始...")
            soup = BeautifulSoup(content, 'html.parser')
            
            proxy_base_url = get_proxy_base_url()
            print(f"🔗 プロキシベースURL: {proxy_base_url}")

            for video_tag in soup.find_all('video'):
                source_tag = video_tag.find('source')
                if source_tag and source_tag.get('src'):
                    video_url = source_tag['src']
                    video_id = urlparse(video_url).path.split('/')[-1]
                    final_params_string = VIDEO_CONFIG["params"] if VIDEO_CONFIG else ""
                    iframe_html = f'<iframe width="560" height="315" src="{EMBED_BASE_URL}{video_id}{final_params_string}" frameborder="0" allowfullscreen></iframe>'
                    video_tag.replace_with(BeautifulSoup(iframe_html, 'html.parser'))
                    print(f"✅ 動画タグをiframeに変換しました。")

            tags_to_rewrite = {'a': 'href', 'link': 'href', 'script': 'src', 'img': 'src', 'source': 'src'}
            for tag, attr in tags_to_rewrite.items():
                for element in soup.find_all(tag):
                    link = element.get(attr)
                    if link:
                        absolute_link = urljoin(target_url, link)
                        if 'google' in absolute_link or 'gstatic' in absolute_link:
                            element[attr] = f"{proxy_base_url}/?url={quote(absolute_link, safe='')}"
                        else:
                            element[attr] = f"./?url={quote(absolute_link, safe='')}"
            print("✅ リンク書き換え完了。")
            
            for style_tag in soup.find_all('style'):
                if style_tag.string:
                    style_tag.string = style_tag.string.replace('url(', f'url(./?url=')
            print("✅ CSSのURL書き換え完了。")
            
            content = str(soup)
            
        return content, 200, {'Content-Type': content_type if content_type else 'text/plain'}
    
    except subprocess.CalledProcessError as e:
        print("❌ curlコマンド実行中にエラーが発生しました。")
        print(f"エラー詳細: {e.stderr}")
        return jsonify({"error": f"Curlコマンドの実行に失敗しました: {e.stderr}"}), 500
    except Exception as e:
        print(f"❌ 予期せぬエラーが発生しました: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
