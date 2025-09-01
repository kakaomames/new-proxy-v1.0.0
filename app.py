import subprocess
import json
import os
from flask import Flask, request, jsonify, render_template_string
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# jsonではバックスラッシュを使用する記号などはバックスラッシュをそのままにしたい
print(json.dumps({"message": "プロキシ機能とホームページを統合しました。", "user": "カカオマメ"}))

# YouTubeの特定のパスをリスト化
YOUTUBE_PATHS = ["watch", "channel", "c", "@", "search", "live", "playlist", "tag", "shorts"]

# 動画埋め込み用の設定URL
CONFIG_URL = 'https://raw.githubusercontent.com/siawaseok3/wakame/master/video_config.json'
EMBED_BASE_URL = 'https://www.youtubeeducation.com/embed/'
VIDEO_CONFIG = None

# video_config.jsonの内容を読み込む関数
def load_video_config():
    global VIDEO_CONFIG
    try:
        # curlコマンドでjsonファイルを取得
        result = subprocess.run(["curl", "-s", CONFIG_URL], capture_output=True, text=True, check=True)
        VIDEO_CONFIG = json.loads(result.stdout)
        print("動画設定ファイルを読み込みました。")
    except Exception as e:
        print(f"動画設定ファイルの読み込みに失敗しました: {e}")
        VIDEO_CONFIG = {"params": ""}

# アプリケーション起動時に設定を読み込む
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
        .textbox {
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
            <input type="text" class="textbox" placeholder="ここに何か入力してください...">
        </div>
    </main>
    <footer>
        <p>&copy; 2025  pokemoguプロジェクト</p>
    </footer>
</body>
</html>
"""

# --- ルートの定義 ---
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/home')
def home():
    return render_template_string(HOME_HTML)

---
@app.route('/<path:path>', methods=['GET', 'POST'])
def proxy_request(path):
    query_string = request.query_string.decode('utf-8')
    target_url = None

    url_param = request.args.get('url')
    if url_param:
        target_url = url_param
    else:
        path_segments = path.split('/')
        if path_segments[0] in YOUTUBE_PATHS:
            youtube_base_url = "https://www.youtube.com"
            target_url = f"{youtube_base_url}/{path}"
            if query_string:
                target_url += f"?{query_string}"
        else:
            if path.startswith(("http://", "https://", "www.", "m.")):
                if not path.startswith(("http://", "https://")):
                    path = "https://" + path
                target_url = path
                if query_string:
                    target_url += f"?{query_string}"
            else:
                return jsonify({"error": "無効なURLまたはパスです。"}), 400

    data = request.get_data()
    curl_command = ["curl", "-s", "-L", "--max-time", "30", "-X", request.method, target_url]
    
    if data:
        curl_command.extend(["-d", data.decode('utf-8')])

    try:
        result = subprocess.run(
            curl_command,
            capture_output=True,
            text=True,
            check=True
        )
        content = result.stdout
        
        content_type = 'text/html' if 'text/html' in result.stderr else ''
        
        if 'text/html' in content_type:
            soup = BeautifulSoup(content, 'html.parser')

            for video_tag in soup.find_all('video'):
                source_tag = video_tag.find('source')
                if source_tag and source_tag.get('src'):
                    video_url = source_tag['src']
                    video_id = urlparse(video_url).path.split('/')[-1]
                    final_params_string = VIDEO_CONFIG["params"] if VIDEO_CONFIG else ""
                    iframe_html = f'<iframe width="560" height="315" src="{EMBED_BASE_URL}{video_id}{final_params_string}" frameborder="0" allowfullscreen></iframe>'
                    video_tag.replace_with(BeautifulSoup(iframe_html, 'html.parser'))

            tags_to_rewrite = {'a': 'href', 'link': 'href', 'script': 'src', 'img': 'src', 'source': 'src'}
            for tag, attr in tags_to_rewrite.items():
                for element in soup.find_all(tag):
                    link = element.get(attr)
                    if link:
                        absolute_link = urljoin(target_url, link)
                        element[attr] = f"./?url={absolute_link}"
            
            for style_tag in soup.find_all('style'):
                if style_tag.string:
                    style_tag.string = style_tag.string.replace('url(', f'url(./?url=')
            
            content = str(soup)
            
        return content, 200, {'Content-Type': content_type if content_type else 'text/plain'}
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Curlコマンドの実行に失敗しました: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
