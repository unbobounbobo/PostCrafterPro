# 次回セッション クイックスタートガイド

**このファイルを読めば、次回セッションをすぐに開始できます**

---

## 🚀 1分で状況把握

### 現在の状態
- ✅ バックエンド実装 **完了**（55%完了）
- ⏳ フロントエンド実装 **未着手**（残り45%）

### 完成しているもの
1. Claude 4.5 API統合
2. Pinecone RAG（65,098件のミドリ安全データ検索）
3. Google Sheets連携（3シート管理）
4. セマンティック検索（過去投稿）
5. 統合RAGサービス

### これから作るもの
1. **UI（Tinder方式）** ← 次回のメイン作業
2. APIエンドポイント統合
3. テスト & デバッグ

---

## 📋 次回セッション開始時のコマンド

```bash
# 1. プロジェクトに移動
cd D:\Claude-code\PostCrafterPro

# 2. 仮想環境を有効化（未作成の場合は先に作成）
# 仮想環境作成（初回のみ）
python -m venv venv

# Windows
venv\Scripts\activate

# 3. 依存関係インストール（初回のみ）
pip install -r requirements.txt

# 4. .env ファイルを作成（初回のみ）
# .env.example をコピーして編集
copy .env.example .env

# 5. Google Sheetsセットアップ（初回のみ）
# ※ service_account.json を配置してから実行
python setup_sheets.py

# 6. アプリ起動テスト（後で実施）
python run.py
```

---

## ⚙️ 環境変数チェックリスト

`.env` ファイルに以下が設定されているか確認：

```bash
# 必須
✅ ANTHROPIC_API_KEY=sk-ant-...
✅ PINECONE_API_KEY=...
✅ GOOGLE_SHEETS_ANALYTICS_ID=1Y7tNRSQ9es_cx2rDm9dF_bF_Gj5cgft8-_jD_d2zcbw

# セットアップ後に追加
⏳ GOOGLE_SHEETS_DRAFT_ID=（setup_sheets.py実行後に取得）
⏳ GOOGLE_SHEETS_PUBLISHED_ID=（setup_sheets.py実行後に取得）

# オプション
□ FIRECRAWL_API_KEY=...
```

---

## 🎯 次回セッションの作業内容

### フェーズ6: UI実装（90分）

#### 作成するファイル一覧
```
templates/
  ├── base.html           ← ベーステンプレート
  ├── index.html          ← メイン画面
  └── components/
      ├── input_form.html       ← 入力フォーム
      ├── tinder_view.html      ← Tinder方式UI
      ├── refinement.html       ← 改善リクエスト
      ├── pinecone_results.html ← Pinecone検索結果
      └── similar_posts.html    ← 類似投稿表示

static/
  ├── js/
  │   └── app.js          ← Alpine.jsメインアプリ
  └── css/
      └── app.css         ← カスタムスタイル
```

#### UI要件のおさらい
1. **入力フォーム**: 日付、URL、決定事項、記念日、補足
2. **Tinder方式**: 2案を並べて表示 → 選択
3. **繰り返し**: 選択 → 改善リクエスト → 次ラウンド
4. **最終確定**: Google Sheetsに保存

---

## 💻 実装サンプル（参考）

### Alpine.js コンポーネントの基本構造

```javascript
function postCreator() {
  return {
    // State
    form: {
      date: '',
      url: '',
      decided: '',
      anniversary: '',
      remarks: ''
    },
    pineconeResults: [],
    similarPosts: [],
    round: 0,
    postA: null,
    postB: null,
    selectedSide: null,
    refinementRequest: '',
    history: [],
    loading: false,

    // Methods
    async init() {
      // 初期化処理
    },

    async fetchContext() {
      // Pinecone + 類似投稿検索
      const response = await fetch('/api/init', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          url: this.form.url,
          decided: this.form.decided
        })
      });
      const data = await response.json();
      this.pineconeResults = data.pinecone_results;
      this.similarPosts = data.similar_posts;
    },

    async generatePosts() {
      this.loading = true;
      // APIコール
      this.loading = false;
    },

    selectPost(side) {
      this.selectedSide = side;
    },

    async nextRound() {
      // 次のラウンドへ
    },

    async finalize() {
      // 完成投稿をGoogle Sheetsに保存
    }
  }
}
```

---

## 🔍 動作確認の手順

### ステップ1: サービスの動作確認

```python
# Pythonインタラクティブシェルで確認
python

>>> from app.services.rag_service import RAGService
>>> rag = RAGService()
# ✅ が3つ表示されればOK

>>> from app.services.claude_service import ClaudeService
>>> claude = ClaudeService()
# ✅ が表示されればOK
```

### ステップ2: Flaskアプリの起動

```bash
python run.py
# http://127.0.0.1:5000 にアクセス
```

---

## 📝 よくある問題と解決法

### 問題1: `ANTHROPIC_API_KEY not found`
**解決**: `.env` ファイルを作成し、APIキーを設定

### 問題2: `PINECONE_API_KEY not found`
**解決**: `.env` ファイルにPinecone APIキーを追加

### 問題3: `Spreadsheet not found`
**解決**: `setup_sheets.py` を実行してシートを作成

### 問題4: `ModuleNotFoundError`
**解決**: `pip install -r requirements.txt` を実行

---

## 🎨 UI設計のポイント

### Tinder方式UIの実装イメージ

```
┌──────────────────────────────────────┐
│        PostCrafterPro                │
├──────────────────────────────────────┤
│ [入力フォーム]                         │
│ 日付: [2025/01/22]                   │
│ URL:  [https://...]                  │
│ 決定: [防災の日にヘルメットPR]         │
├──────────────────────────────────────┤
│ [Pinecone検索結果]                    │
│ ・フラットメットキッズ                 │
│ ・防災ヘルメット一覧                   │
├──────────────────────────────────────┤
│ [Tinder選択]                          │
│ ┌───────────┬───────────┐            │
│ │ 案A      │ 案B      │            │
│ │ 今日は... │ 防災の... │            │
│ │ [選択]   │ [選択]   │            │
│ └───────────┴───────────┘            │
├──────────────────────────────────────┤
│ [改善リクエスト]                       │
│ もっとカジュアルに [次へ] [確定]      │
└──────────────────────────────────────┘
```

---

## ✅ チェックリスト（次回開始前）

- [ ] `.env` ファイル作成済み
- [ ] Google認証ファイル配置済み（`service_account.json`）
- [ ] `pip install -r requirements.txt` 実行済み
- [ ] `python setup_sheets.py` 実行済み
- [ ] `.env` にシートID追加済み
- [ ] サービスの動作確認済み

---

**準備ができたら、「UI実装を開始してください」と伝えてください！**
