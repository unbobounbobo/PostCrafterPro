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

## 🔬 仕組み・アーキテクチャ

PostCrafterProがどのように動作するか、データフローを詳しく解説します。

### 📊 全体フロー

```
┌─────────────────────────────────────────────────┐
│ 【Step 1】ユーザー入力                           │
│  ① date (投稿日) - 必須                         │
│  ② url (商品URL) - オプション                   │
│  ③ decided (決定事項) - 必須                    │
│  ④ anniversary (記念日) - オプション            │
│  ⑤ remarks (補足) - オプション                  │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 【Step 2】コンテキスト取得（/api/init）          │
│  RAGService.get_comprehensive_context()         │
│                                                 │
│  ❶ Pinecone検索（商品情報）                     │
│     ├─ URL → 商品ページ検索（最大5件）          │
│     └─ decided → キーワード検索（最大3件）      │
│                                                 │
│  ❷ 過去投稿の類似検索                           │
│     ├─ decided → セマンティック検索（最大5件）  │
│     └─ anniversary → 記念日関連検索（最大3件）  │
│                                                 │
│  ❸ X Analytics分析                              │
│     └─ decided → パフォーマンス統計・推奨事項   │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 【Step 3】Claude 4.5による投稿生成               │
│  ClaudeService.create_sns_post_with_context()   │
│                                                 │
│  第1段階: 調査・思考（Extended Thinking）       │
│    - URLクローリング（提供された場合）          │
│    - コンテキスト分析                           │
│    - 戦略立案                                   │
│    - tweet_length_checkerで文字数確認           │
│                                                 │
│  第2段階: JSON出力                              │
│    - 投稿案A（アプローチ1）                     │
│    - 投稿案B（アプローチ2）                     │
│    - 文字数チェック済み                         │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 【Step 4】ユーザー選択 & 改善（オプション）      │
│  最大3ラウンドまで繰り返し改善可能              │
└─────────────────────────────────────────────────┘
```

### 📝 入力変数の使われ方

| 変数 | 必須 | 検索に使用 | 重要度 | 使用場所 |
|-----|------|-----------|--------|---------|
| **decided** | ✅ | ✅✅✅ | ⭐⭐⭐⭐⭐ | Pinecone検索、過去投稿検索、Analytics分析、プロンプト |
| **date** | ✅ | ❌ | ⭐⭐⭐ | プロンプト、Sheet保存 |
| **url** | ❌ | ✅✅ | ⭐⭐⭐⭐ | Pinecone検索（URL検索）、Claudeクローリング |
| **anniversary** | ❌ | ✅ | ⭐⭐ | 過去投稿検索（記念日関連） |
| **remarks** | ❌ | ❌ | ⭐ | プロンプトの補足指示のみ |

### 🗄️ データソースの活用

#### 1. **Pinecone（商品情報データベース）**

**データ量:** 65,098件のミドリ安全商品情報

**検索方法:**
- **URL検索**: 商品URLから直接検索（最大5件）
- **キーワード検索**: `decided`から抽出したキーワードで検索（最大3件）

**Claudeへの提供:**
```
【Pinecone検索結果（商品情報）】
1. フラットメットキッズ
   - 特徴: 折りたたみ式防災ヘルメット
   - 価格: ¥3,980
   - 詳細: ランドセルに収納可能...
```

#### 2. **過去投稿（セマンティック検索）**

**データソース:** Google Sheets「SNS投稿_完成版」

**検索方法:**
- **decided検索**: 意味的に類似した過去投稿を検索（最大5件）
- **anniversary検索**: 記念日関連の過去投稿を追加検索（最大3件）

**技術:** OpenAI Embeddings (text-embedding-3-small)

**Claudeへの提供:**
```
【過去の類似投稿】
1. 今日は防災の日🚨 もしもの時に備える...
2. 大切なお子さまを守る防災ヘルメット...
```

#### 3. **X Analytics（パフォーマンス分析）**

**データソース:**
- tweetシート: 投稿別パフォーマンス
- dayシート: 日次統計

**分析内容:**
- 最近30日のトレンド（インプレッション、エンゲージメント）
- Top50の高パフォーマンス投稿の特徴
- 平均文字数、URL使用率、ハッシュタグ使用率
- テーマ別の高パフォーマンス投稿例

**Claudeへの提供:**
```
【過去のX投稿パフォーマンス分析】

《最近30日のトレンド》
- 1日あたり平均インプレッション: 15,234
- 平均エンゲージメント率: 3.00%

《高パフォーマンス投稿の特徴》
- 平均文字数: 85文字
- URL含有率: 60%

《推奨事項》
- 高エンゲージメント投稿の平均文字数は85文字です。
```

### 🤖 Claude 4.5の処理プロセス

#### 初回生成（/api/generate）

**第1段階: 調査・思考**
- **システムプロンプト**: ミドリ安全の広報担当者として役割定義
- **ツール使用**:
  - `web_search`: URLのクローリング（提供された場合）
  - `tweet_length_checker`: 文字数の正確なカウント
- **Extended Thinking**: 6,554トークンの思考バジェット
- **max_tokens**: 16,000

**第2段階: JSON出力**
- **システムプロンプト**: 2案生成の指示
- **出力形式**: 構造化JSON（post_a, post_b）
- **max_tokens**: 10,000

#### 改善（/api/refine）

**処理:**
- 選択された投稿をベースに2つの改善案を生成
- 改善リクエスト（ユーザーの指示）を反映
- `tweet_length_checker`で文字数確認
- **max_tokens**: 8,000

**会話ループ:** 最大5ターン

### 📊 コスト・パフォーマンス

#### トークン使用量（推定）

| 処理 | Input tokens | Output tokens | コスト（概算） |
|------|-------------|--------------|--------------|
| 初回生成 | ~8,000 | ~2,000 | $0.23 |
| 改善1回 | ~1,500 | ~500 | $0.015 |
| 改善2回 | ~1,500 | ~500 | $0.015 |
| **合計（3ラウンド）** | ~11,000 | ~3,000 | **$0.26** |

#### 処理時間

| 処理 | 時間 |
|------|------|
| コンテキスト取得 | 5〜10秒 |
| 初回生成 | 30〜60秒 |
| 改善（1回） | 20〜40秒 |
| **1投稿の合計** | **55〜110秒** |

### 🔄 バッチ処理の仕組み

**特徴:**
- 自動的に投稿案Aを選択（手動選択不要）
- 3秒の待機時間でAPI制限を回避
- エラースキップで処理継続
- リアルタイム進捗表示

**処理フロー:**
```
投稿1 → コンテキスト取得 → 生成 → 保存 → 完了
  ↓ (3秒待機)
投稿2 → コンテキスト取得 → 生成 → 保存 → 完了
  ↓ (3秒待機)
...
```

**10件の処理時間:** 約5〜10分

### 🔐 データフローのセキュリティ

- **API通信**: 全てHTTPS
- **認証情報**: `.gitignore`で除外
- **Google Sheets**: サービスアカウント認証
- **Pinecone**: Serverless（自動スケーリング）

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
