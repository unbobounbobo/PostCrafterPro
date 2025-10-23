# PostCrafterPro

**SNS投稿作成支援ツール** - Claude 4.5とPinecone RAGを活用した、業務レベルのSNS投稿クラフター

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![Claude](https://img.shields.io/badge/Claude-4.5%20Sonnet-purple)
![Pinecone](https://img.shields.io/badge/Pinecone-RAG-orange)
![License](https://img.shields.io/badge/License-Private-red)

</div>

## 🎯 主な機能

- **🔄 Tinder方式UI**: 2つの投稿案を比較選択し、繰り返し改善
- **🔍 Pinecone RAG**: ミドリ安全サイト全体（65,098件）から商品情報を検索
- **📊 過去投稿参照**: セマンティック検索で類似投稿を自動取得
- **📝 Google Sheets連携**: 下書き・完成投稿を自動保存
- **🤖 Claude 4.5**: Extended Thinkingによる高品質な投稿生成
- **📦 バッチ処理**: 複数投稿の一括生成機能
- **📅 Flatpickrカレンダー**: 日本語対応・月曜始まり
- **⚙️ プロンプトカスタマイズ**: システム・ユーザープロンプトの細かい調整が可能

## 📸 スクリーンショット

### メイン画面
投稿情報を入力し、AIが2つの案を生成します。

### Tinder方式選択
左右の投稿案を比較し、気に入った方を選択できます。

### バッチ処理
Google Sheetsから複数の投稿を一括で生成・保存できます。

## 🚀 セットアップ

### 必要な環境

- **Python 3.11以上**
- **Google Sheetsアクセス権限**
- 以下のAPIキー:
  - Anthropic Claude API
  - Pinecone API
  - Google Sheets API
  - Firecrawl API（オプション）

### 1. リポジトリのクローン

```bash
git clone https://github.com/unbobounbobo/PostCrafterPro.git
cd PostCrafterPro
```

### 2. 仮想環境の作成

```bash
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

`.env.example` をコピーして `.env` を作成:

```bash
cp .env.example .env
```

`.env` を編集して以下を設定:

```env
# Claude API
ANTHROPIC_API_KEY=your-claude-api-key-here

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_INDEX_NAME=your-index-name

# Google Sheets
GOOGLE_SHEETS_DRAFT_ID=your-draft-sheet-id
GOOGLE_SHEETS_PUBLISHED_ID=your-published-sheet-id

# Optional: Firecrawl
FIRECRAWL_API_KEY=your-firecrawl-api-key-here
```

### 5. Google Sheets認証設定

Google Cloud Consoleで認証情報を取得し、プロジェクトルートに配置:

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. Google Sheets APIを有効化
3. サービスアカウントを作成
4. JSONキーをダウンロード
5. プロジェクトルートに `service_account.json` として保存
6. サービスアカウントのメールアドレスをGoogle Sheetsに共有

### 6. Google Sheetsの初期化

```bash
python setup_sheets.py
```

このスクリプトは以下のシートを作成します:
- `SNS投稿_下書き`: 生成中・改善中の投稿を保存
- `SNS投稿_完成版`: 最終確定した投稿を保存

### 7. アプリケーションの起動

```bash
python run.py
```

ブラウザで http://127.0.0.1:5000 にアクセス

## 📖 使い方

### 基本フロー

1. **投稿情報入力**: 投稿日、商品URL、決定事項などを入力
2. **情報取得**: Pineconeから商品情報、過去投稿から類似投稿を自動検索
3. **初回生成**: Claude 4.5が2つの投稿案（A/B）を生成
4. **Tinder選択**: 左右の案を比較し、気に入った方を選択
5. **改善（任意）**: 改善リクエストを入力して次ラウンドへ
6. **繰り返し**: 満足するまで選択→改善を繰り返し（最大3ラウンド）
7. **確定**: 最終投稿をGoogle Sheetsに保存

### バッチ処理

詳細は [docs/BATCH_USAGE.md](docs/BATCH_USAGE.md) を参照してください。

1. `/batch` にアクセス
2. データソース（Google Sheets）を選択
3. 処理範囲（行番号）を指定
4. オプション設定（自動保存、エラースキップ、待機時間）
5. データを読み込み
6. バッチ処理を開始
7. 結果をCSVエクスポート

## 🔧 技術スタック

### Backend
- **Flask 3.0**: Webフレームワーク
- **Python 3.11+**: プログラミング言語

### AI & RAG
- **Claude 4.5 Sonnet**: Extended Thinking対応の最新AIモデル
- **Pinecone**: ベクトルデータベース（Serverless）
- **OpenAI Embeddings**: text-embedding-3-small

### Frontend
- **Alpine.js**: リアクティブUIフレームワーク（軽量）
- **Tailwind CSS**: ユーティリティファーストCSSフレームワーク
- **Flatpickr**: 日本語対応カレンダー（月曜始まり）

### Database
- **Google Sheets**: データ保存・管理

### Deployment
- **PythonAnywhere**: 本番環境対応

## 📁 プロジェクト構造

```
PostCrafterPro/
├── app/
│   ├── __init__.py              # Flaskアプリ初期化
│   ├── routes/                  # APIルーティング
│   │   ├── api.py              # メインAPI
│   │   ├── batch_api.py        # バッチ処理API
│   │   ├── main.py             # ページルート
│   │   └── settings.py         # 設定API
│   ├── services/                # ビジネスロジック
│   │   ├── claude_service.py   # Claude API連携
│   │   ├── pinecone_service.py # Pinecone RAG
│   │   ├── sheets_service.py   # Google Sheets
│   │   ├── rag_service.py      # RAG統合
│   │   └── prompt_service.py   # プロンプト管理
│   └── utils/                   # ユーティリティ
├── templates/                   # HTMLテンプレート
│   ├── base.html               # 共通レイアウト
│   ├── index.html              # メイン画面
│   ├── batch.html              # バッチ処理画面
│   ├── settings.html           # 設定画面
│   └── components/             # UIコンポーネント
├── static/
│   └── js/
│       └── app.js              # Alpine.jsアプリロジック
├── config/
│   └── prompts.json            # プロンプト設定
├── docs/
│   └── BATCH_USAGE.md          # バッチ処理マニュアル
├── config.py                    # 設定管理
├── run.py                       # 開発サーバー
├── wsgi.py                      # 本番サーバー
└── requirements.txt             # Python依存関係
```

## 📊 API エンドポイント

### `POST /api/init`
コンテキストの初期化（Pinecone + 類似投稿検索）

### `POST /api/generate`
初回投稿生成（2案: A/B）

### `POST /api/refine`
投稿の改善（選択した投稿から2つの改善案を生成）

### `POST /api/publish`
最終投稿の保存（Google Sheetsへ保存）

### `POST /api/batch/load`
バッチ処理用のデータ読み込み

### `POST /api/batch/process`
バッチ処理で1件の投稿を生成

### `POST /api/batch/export`
バッチ処理結果のCSVエクスポート

## 🎨 プロンプトカスタマイズ

`/settings` にアクセスして、以下のプロンプトをカスタマイズできます:

### 🚀 初回生成
- **システム: 調査段階用プロンプト**: URLクローリング・thinking実行時に使用
- **システム: 出力段階用プロンプト**: JSON形式で投稿案を出力する際に使用
- **ユーザー: 初回生成用プロンプト**: 投稿情報・コンテキスト・生成手順を指示

### ✨ 改善
- **システム: 改善用システムプロンプト**: 投稿改善時の役割定義
- **ユーザー: 改善用プロンプト**: 元の投稿と改善リクエストを受け取り、改善手順を指示

## 🔒 セキュリティ

以下のファイルは `.gitignore` に含まれており、リポジトリにコミットされません:

- `.env` - 環境変数（APIキーなど）
- `credentials.json` - Google OAuth認証情報
- `service_account.json` - Google サービスアカウントキー
- `.mcp.json` - MCPサーバー設定（APIキー含む）

**重要**: これらのファイルは絶対にGitHubにプッシュしないでください。

## 🚧 トラブルシューティング

### エラー: "ANTHROPIC_API_KEY not found"
`.env` ファイルにAPIキーが正しく設定されているか確認してください。

### エラー: "Google Sheets API credentials not found"
1. `service_account.json` がプロジェクトルートに配置されているか確認
2. Google Cloud ConsoleでGoogle Sheets APIが有効化されているか確認
3. サービスアカウントがシートに共有されているか確認

### 投稿が生成されない
1. Claude APIのクォータを確認
2. ネットワーク接続を確認
3. ログを確認: `app/routes/api.py` のエラーメッセージ

詳細は [docs/BATCH_USAGE.md](docs/BATCH_USAGE.md) のトラブルシューティングセクションを参照してください。

## 🌐 デプロイ

### PythonAnywhereへのデプロイ

詳細は `CLAUDE.md` を参照してください。

基本的な手順:
1. PythonAnywhereアカウントを作成
2. Bash コンソールでプロジェクトをクローン
3. 仮想環境を作成し、依存関係をインストール
4. `.env` と認証ファイルを配置
5. Web タブでWSGI設定を行う

## 📝 ライセンス

Private Use Only

## 🙏 謝辞

このプロジェクトは以下の技術を使用しています:

- [Anthropic Claude](https://www.anthropic.com/) - AI生成エンジン
- [Pinecone](https://www.pinecone.io/) - ベクトルデータベース
- [Flask](https://flask.palletsprojects.com/) - Webフレームワーク
- [Alpine.js](https://alpinejs.dev/) - リアクティブUIフレームワーク
- [Tailwind CSS](https://tailwindcss.com/) - CSSフレームワーク
- [Flatpickr](https://flatpickr.js.org/) - 日本語カレンダー

---

**開発**: PostCrafterPro Team
**最終更新**: 2025-10-23
