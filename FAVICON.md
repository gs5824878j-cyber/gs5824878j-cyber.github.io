# favicon運用

共通ブランドはホスト直下の /ai-blog/favicon.ico、/ai-blog/favicon-32x32.png、/ai-blog/favicon-192x192.png、/ai-blog/apple-touch-icon.png。全サービスで同じものを参照します。

HTMLを追加したら `python3 scripts/favicon.py .` を実行してheadへ設定してください。新規GitHub Pages制作物にもこのスクリプトをコピーして実行します。data URIのfaviconは追加しません。公開後は全icon URLのHTTP 200を確認します。

別ホストではそのサービスのアイコンを同じパスへ配置します。
