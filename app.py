import subprocess
import json
import os
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# jsonではバックスラッシュを使用する記号などはバックスラッシュをそのままにしたい
print(json.dumps({"message": "PythonでYouTube動画を埋め込むようにしました。", "user": "カカオマメ"}))

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

# ルートパスで返すHTMLコンテンツ
ROOT_HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>プロキシサイトへようこそ</title>
    <style>
        body {
            font-family: sans-serif;
            background-color: #f0f2f5;
            color: #333;
            text-align: center;
            padding-top: 50px;
        }
        .container {
            background-color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 600px;
            margin: auto;
        }
        h1 {
            color: #0056b3;
        }
        p {
            line-height: 1.6;
        }
        a {
            color: #007bff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>プロキシサイト</h1>
        <p>このサイトはプロキシとして機能します。</p>
        <p>
            URLの末尾にYouTubeのパス（例：/watch?v=...）や、
            他のサイトのURL（例：/https://www.example.com）を入力してアクセスしてください。
        </p>
        <p>
            <a href="/watch?v=dQw4w9WgXcQ">YouTubeのサンプルページへ</a>
        </p>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def serve_root_html():
    """ルートパスにアクセスした際に静的なHTMLを返す"""
    return ROOT_HTML_CONTENT, 200, {'Content-Type': 'text/html; charset=utf-8'}

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

            # 動画URLをiframeに変換
            for video_tag in soup.find_all('video'):
                source_tag = video_tag.find('source')
                if source_tag and source_tag.get('src'):
                    video_url = source_tag['src']
                    
                    video_id = urlparse(video_url).path.split('/')[-1]
                    
                    # 動画設定のparamsを追加
                    final_params_string = VIDEO_CONFIG["params"] if VIDEO_CONFIG else ""
                    
                    iframe_html = f'<iframe width="560" height="315" src="{EMBED_BASE_URL}{video_id}{final_params_string}" frameborder="0" allowfullscreen></iframe>'
                    
                    video_tag.replace_with(BeautifulSoup(iframe_html, 'html.parser'))

            # 他のリンク（a, style, script, link, img, source）を書き換え
            tags_to_rewrite = {'a': 'href', 'link': 'href', 'script': 'src', 'img': 'src', 'source': 'src'}
            for tag, attr in tags_to_rewrite.items():
                for element in soup.find_all(tag):
                    link = element.get(attr)
                    if link:
                        absolute_link = urljoin(target_url, link)
                        element[attr] = f"./?url={absolute_link}"
            
            # CSSの<style>タグ内のURLも書き換え
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
