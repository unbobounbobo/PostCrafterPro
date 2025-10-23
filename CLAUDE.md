# PostCrafterPro

**SNS投稿作成支援ツール** - Claude 4.5とPinecone RAGを活用した、業務レベルのSNS投稿クラフター

## 🎯 主な機能

- **Tinder方式UI**: 2つの投稿案を比較選択し、繰り返し改善
- **バッチ処理**: 複数の投稿を一括で自動生成（10件なら約5〜10分）
- **Pinecone RAG**: ミドリ安全サイト全体（65,098件）から商品情報を検索
- **過去投稿参照**: セマンティック検索で類似投稿を自動取得
- **Google Sheets連携**: 下書き・完成投稿を自動保存
- **Claude 4.5**: 最新AIによる高品質な投稿生成

## 📋 必要な環境

- Python 3.11+
- Google Sheetsアクセス権限
- 以下のAPIキー:
  - Anthropic (Claude)
  - Pinecone
  - Google Sheets API
  - Firecrawl (オプション)

## 🚀 セットアップ

### 1. プロジェクトのクローン

```bash
cd D:\Claude-code
# プロジェクトは既に PostCrafterPro フォルダに展開されています
```

### 2. 仮想環境の作成

```bash
cd PostCrafterPro
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、APIキーを設定:

```bash
cp .env.example .env
```

`.env` を編集して以下を設定:
- `ANTHROPIC_API_KEY`: Claude APIキー
- `PINECONE_API_KEY`: Pinecone APIキー
- `GOOGLE_SHEETS_DRAFT_ID`: 下書きシートID（初回起動時に作成）
- `GOOGLE_SHEETS_PUBLISHED_ID`: 完成シートID（初回起動時に作成）
- `FIRECRAWL_API_KEY`: Firecrawl APIキー（オプション）

### 5. Google Sheets認証設定

Google Cloud Consoleで認証情報（OAuth 2.0）を取得し、プロジェクトルートに配置:
- `credentials.json` または `service_account.json`

### 6. アプリケーションの起動

```bash
python run.py
```

ブラウザで http://127.0.0.1:5000 にアクセス

## 📊 Google Sheets構成

### 自動作成スクリプト

初回セットアップ時に、以下のスクリプトを実行してシートを作成できます:

```bash
python setup_sheets.py
```

このスクリプトは以下を作成します:

### 1. 下書きシート (`SNS投稿_下書き`)

生成中・改善中の投稿を保存。各ラウンドの履歴を記録。

**主なカラム:**
- 作成日時
- 投稿日
- URL
- 決定事項
- 記念日
- 補足
- R1_案A、R1_案B、R1_選択、R1_改善リクエスト
- R2_案A、R2_案B、R2_選択、R2_改善リクエスト
- R3_案A、R3_案B、R3_選択、R3_改善リクエスト
- 最終投稿
- 最終文字数
- 文字数チェック
- ラウンド数
- Pinecone結果数
- 類似投稿数

### 2. 完成シート (`SNS投稿_完成版`)

最終確定した投稿のみ保存。

**主なカラム:**
- 作成日時
- 投稿日
- URL
- 決定事項
- 記念日
- 補足
- 最終投稿
- 文字数
- 文字数チェック
- ラウンド数
- Pinecone結果数
- 類似投稿数

### 3. アナリティクスシート (既存)

過去データ参照用（RAG対象）

**シートID:** `1Y7tNRSQ9es_cx2rDm9dF_bF_Gj5cgft8-_jD_d2zcbw`

## 🔑 Google Sheets API設定詳細

### サービスアカウント方式（推奨）

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
3. Google Sheets APIを有効化
4. サービスアカウントを作成
5. JSONキーをダウンロードし、プロジェクトルートに `service_account.json` として保存
6. サービスアカウントのメールアドレス（`xxx@xxx.iam.gserviceaccount.com`）を、
   各Google Sheetsの共有設定で「編集者」として追加

### OAuth 2.0方式

1. Google Cloud Consoleで OAuth 2.0 クライアントIDを作成
2. `credentials.json` をダウンロード
3. 初回起動時にブラウザで認証

## 🎨 使い方

### 基本フロー（1件ずつ作成）

1. **入力フォーム**: 投稿日、URL、決定事項などを入力
2. **情報取得**: Pineconeから商品情報、過去投稿から類似投稿を自動検索
3. **初回生成**: Claude 4.5が2案を生成
4. **Tinder選択**: 気に入った方を選択
5. **改善（任意）**: 改善リクエストを入力して次ラウンドへ
6. **繰り返し**: 満足するまで選択→改善を繰り返し
7. **確定**: 最終投稿をGoogle Sheetsに保存

### バッチ処理（複数まとめて作成）

複数の投稿を一括で自動生成できます。

**アクセス**: http://127.0.0.1:5000/batch

**使い方**:
1. Google Sheets下書きに投稿データを準備（投稿日、URL、決定事項）
2. バッチ処理画面で設定（開始行、終了行、オプション）
3. データ読み込み → 確認 → 処理開始
4. 結果を確認してCSVエクスポートまたは自動保存

**処理時間**: 10件で約5〜10分

**詳細**: [バッチ処理使い方ガイド](docs/BATCH_USAGE.md)

## 🔧 技術スタック

- **Backend**: Flask 3.0
- **AI**: Claude 4.5 (Sonnet)
- **RAG**: Pinecone (Serverless)
- **Database**: Google Sheets
- **Frontend**: Alpine.js + Tailwind CSS
- **Deployment**: PythonAnywhere対応

## 📁 プロジェクト構造

```
PostCrafterPro/
├── app/
│   ├── __init__.py          # Flaskアプリ初期化
│   ├── services/            # ビジネスロジック
│   ├── routes/              # APIルーティング
│   └── utils/               # ユーティリティ
├── static/                  # CSS/JS
├── templates/               # HTMLテンプレート
├── config.py                # 設定管理
├── run.py                   # 開発サーバー
└── wsgi.py                  # 本番サーバー
```

## 🌐 PythonAnywhereへのデプロイ

### 準備

1. PythonAnywhereアカウントを作成
2. Bash コンソールでプロジェクトをクローン
3. 仮想環境を作成し、依存関係をインストール
4. `.env` ファイルと認証ファイルを配置
5. Web タブで WSGI 設定

### WSGI設定例

```python
import sys
import os

# プロジェクトパスを追加
project_home = '/home/yourusername/PostCrafterPro'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 環境変数読み込み
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# アプリケーション読み込み
from wsgi import app as application
```

## 📚 API エンドポイント

### POST `/api/init`

コンテキストの初期化（Pinecone + 類似投稿検索）

**Request:**
```json
{
  "date": "2025-01-15",
  "url": "https://ec.midori-anzen.com/shop/...",
  "decided": "防災の日にヘルメットをPRする",
  "anniversary": "防災の日",
  "remarks": "補足事項"
}
```

**Response:**
```json
{
  "pinecone_results": [...],
  "similar_posts": [...]
}
```

### POST `/api/generate`

初回投稿生成（2案）

**Request:**
```json
{
  "date": "2025-01-15",
  "url": "https://ec.midori-anzen.com/shop/...",
  "decided": "防災の日にヘルメットをPRする",
  "anniversary": "防災の日",
  "remarks": "補足事項",
  "pinecone_results": [...],
  "similar_posts": [...]
}
```

**Response:**
```json
{
  "post_a": {
    "text": "投稿テキスト",
    "character_count": 123,
    "is_valid": true,
    "thinking": "..."
  },
  "post_b": { ... },
  "metadata": { ... }
}
```

### POST `/api/refine`

投稿の改善（選択した投稿から2つの改善案を生成）

**Request:**
```json
{
  "selected_post": "選択された投稿テキスト",
  "refinement_request": "もっとカジュアルに（オプション）",
  "round": 2
}
```

**Response:**
```json
{
  "post_a": { ... },
  "post_b": { ... },
  "metadata": { ... }
}
```

### POST `/api/publish`

最終投稿の保存（Google Sheetsへ保存）

**Request:**
```json
{
  "date": "2025-01-15",
  "url": "https://ec.midori-anzen.com/shop/...",
  "decided": "防災の日にヘルメットをPRする",
  "final_post": {
    "text": "最終投稿テキスト",
    "character_count": 123,
    "is_valid": true
  },
  "history": [ ... ],
  "pinecone_results": [ ... ],
  "similar_posts": [ ... ]
}
```

**Response:**
```json
{
  "success": true,
  "draft_row": 2,
  "published_row": 5
}
```

## 🔧 トラブルシューティング

### エラー: "ANTHROPIC_API_KEY not found"

`.env` ファイルにAPIキーが正しく設定されているか確認してください。

```bash
# .env ファイルを確認
cat .env

# 正しい形式:
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
```

### エラー: "Google Sheets API credentials not found"

1. `service_account.json` または `credentials.json` がプロジェクトルートに配置されているか確認
2. Google Cloud ConsoleでGoogle Sheets APIが有効化されているか確認
3. サービスアカウントがシートに共有されているか確認

### エラー: "Pinecone index not found"

1. `.env` ファイルの `PINECONE_INDEX_NAME` が正しいか確認
2. Pineconeダッシュボードでインデックスが存在するか確認
3. Pinecone APIキーが正しいか確認

### 投稿が生成されない

1. Claude APIのクォータを確認
2. ネットワーク接続を確認
3. ログを確認: `app/routes/api.py` のエラーメッセージ

### 文字数チェックが機能しない

tweet_length_checkerツールが正しく設定されているか確認してください。Claude APIが自動的に文字数をチェックします。

## 🚧 今後の予定

- [x] バッチ処理機能（1ヶ月分まとめて処理）✅ 実装完了
- [ ] 投稿履歴の可視化ダッシュボード
- [ ] Firecrawl統合の強化
- [ ] 画像生成機能の追加
- [ ] 予約投稿機能

## 📝 ライセンス

Private Use Only

## 🤝 サポート

問題が発生した場合は、プロジェクトメンテナーに連絡してください。

## 🙏 謝辞

このプロジェクトは以下の技術を使用しています:

- [Anthropic Claude](https://www.anthropic.com/) - AI生成エンジン
- [Pinecone](https://www.pinecone.io/) - ベクトルデータベース
- [Flask](https://flask.palletsprojects.com/) - Webフレームワーク
- [Alpine.js](https://alpinejs.dev/) - リアクティブUI
- [Tailwind CSS](https://tailwindcss.com/) - CSSフレームワーク
