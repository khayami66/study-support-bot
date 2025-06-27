# LINE Point System

LINEメッセージに応じてポイントを付与し、Googleスプレッドシートに記録するFlaskアプリケーションです。

## 機能

- LINEメッセージのキーワードに応じたポイント付与
- Googleスプレッドシートへの自動記録
- 合計ポイントの確認
- 行動履歴の確認
- 拡張可能なポイントルールシステム

## 現在のポイントルール

- `#宿題` → 1pt（宿題を完了）
- `#スタスタ` → 3pt（スタスタで運動）
- `#ごみ捨て` → 5pt（ごみ捨てを完了）

## セットアップ手順

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`env_example.txt`を参考に、`.env`ファイルを作成してください：

```bash
# LINE Messaging API設定
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
LINE_CHANNEL_SECRET=your_line_channel_secret_here

# Google Sheets API設定
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
SPREADSHEET_ID=your_spreadsheet_id_here
WORKSHEET_NAME=ポイント記録

# アプリケーション設定
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```

### 3. LINE Messaging APIの設定

1. [LINE Developers Console](https://developers.line.biz/)にアクセス
2. 新しいプロバイダーとチャネルを作成
3. Messaging APIチャネルを作成
4. チャネルアクセストークンとチャネルシークレットを取得
5. Webhook URLを設定（例：`https://your-domain.com/callback`）

### 4. Google Sheets APIの設定（詳細手順）

#### 4.1 Google Cloud Consoleでの設定

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）
3. 左側のメニューから「APIとサービス」→「ライブラリ」を選択
4. 「Google Sheets API」を検索して有効化
5. 「APIとサービス」→「認証情報」を選択

#### 4.2 サービスアカウントの作成

1. 「認証情報を作成」→「サービスアカウント」を選択
2. サービスアカウント名を入力（例：`line-point-system`）
3. 「キーを作成」→「JSON」を選択
4. ダウンロードしたファイルを`credentials.json`として保存

#### 4.3 Googleスプレッドシートの設定

1. [Google Sheets](https://sheets.google.com/)で新しいスプレッドシートを作成
2. スプレッドシートのURLからIDを取得：
   - URL例：`https://docs.google.com/spreadsheets/d/1ABC123DEF456/edit`
   - ID：`1ABC123DEF456`
3. スプレッドシートを開き、「共有」ボタンをクリック
4. `credentials.json`内の`client_email`の値をコピー
5. そのメールアドレスを追加し、「編集者」権限を付与

### 5. アプリケーションの起動

```bash
python main.py
```

起動時に設定状況が詳細に表示されます。エラーがある場合は、表示される指示に従って設定を修正してください。

## 使用方法

### LINEでの操作

- `#宿題` - 宿題完了で1pt付与
- `#スタスタ` - スタスタで運動で3pt付与
- `#ごみ捨て` - ごみ捨てで5pt付与
- `#ポイント` - 現在の合計ポイントを確認
- `#履歴` - 最近の行動履歴を確認
- `#ヘルプ` - ヘルプを表示

### スプレッドシートの構造

| ユーザーID | 日時 | 行動 | ポイント | 合計ポイント |
|------------|------|------|----------|--------------|
| U1234567890 | 2024-01-01 10:00:00 | 宿題を完了 | 1 | 1 |
| U1234567890 | 2024-01-01 15:00:00 | スタスタで運動 | 3 | 4 |

## 管理エンドポイント

アプリケーション起動後、以下のエンドポイントで設定状況を確認できます：

- `http://localhost:5000/` - メインページ
- `http://localhost:5000/health` - ヘルスチェック
- `http://localhost:5000/config` - 設定状況の詳細確認

## ファイル構成

```
study_support/
├── main.py              # Flaskメインアプリケーション
├── sheets_handler.py    # Googleスプレッドシート操作
├── point_system.py      # ポイントシステム管理
├── config.py           # 設定管理
├── requirements.txt     # Python依存関係
├── env_example.txt      # 環境変数テンプレート
└── README.md           # このファイル
```

## 拡張機能

### 新しいポイントルールの追加

`config.py`の`DEFAULT_POINT_RULES`に新しいルールを追加できます：

```python
'#読書': {
    'points': 2,
    'message': '読書できたね！{points}pt追加したよ📚',
    'description': '読書を完了'
}
```

### ユーザー管理の追加

将来的にユーザーごとのポイント管理やごほうびシステムを追加できます。

## トラブルシューティング

### よくある問題と解決方法

#### 1. スプレッドシート設定エラー

**症状**: 「スプレッドシートの設定が完了していません」というメッセージが表示される

**解決方法**:
1. `credentials.json`ファイルが正しい場所にあるか確認
2. スプレッドシートIDが正しく設定されているか確認
3. サービスアカウントにスプレッドシートの編集権限があるか確認
4. `/config`エンドポイントで詳細なエラー情報を確認

#### 2. LINE Webhookエラー

**症状**: LINEからのメッセージが受信されない

**解決方法**:
1. チャネルアクセストークンとチャネルシークレットが正しく設定されているか確認
2. Webhook URLが正しく設定されているか確認
3. LINE DevelopersコンソールでWebhookの利用を有効化

#### 3. 環境変数エラー

**症状**: アプリケーション起動時に設定エラーが表示される

**解決方法**:
1. `.env`ファイルが正しく作成されているか確認
2. 全ての必要な環境変数が設定されているか確認
3. デフォルト値（`your_xxx_here`）が実際の値に変更されているか確認

#### 4. Google Sheets API接続エラー

**症状**: スプレッドシートへの接続テストが失敗する

**解決方法**:
1. Google Cloud ConsoleでGoogle Sheets APIが有効化されているか確認
2. サービスアカウントキーが正しくダウンロードされているか確認
3. スプレッドシートにサービスアカウントの編集権限が付与されているか確認

### デバッグ方法

1. アプリケーション起動時のログを確認
2. `/config`エンドポイントで設定状況を確認
3. `/health`エンドポイントでアプリケーションの状態を確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。 