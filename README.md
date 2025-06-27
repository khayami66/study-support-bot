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

### 4. Google Sheets APIの設定

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. Google Sheets APIを有効化
4. サービスアカウントを作成
5. サービスアカウントキーをダウンロード（`credentials.json`として保存）
6. Googleスプレッドシートを作成し、サービスアカウントに編集権限を付与
7. スプレッドシートIDを取得（URLの`/d/`と`/edit`の間の文字列）

### 5. アプリケーションの起動

```bash
python main.py
```

## 使用方法

### LINEでの操作

- `#宿題` - 宿題完了で1pt付与
- `#スタスタ` - スタスタで運動で3pt付与
- `#ポイント` - 現在の合計ポイントを確認
- `#履歴` - 最近の行動履歴を確認
- `#ヘルプ` - ヘルプを表示

### スプレッドシートの構造

| 日時 | 行動 | ポイント | 合計ポイント |
|------|------|----------|--------------|
| 2024-01-01 10:00:00 | 宿題を完了 | 1 | 1 |
| 2024-01-01 15:00:00 | スタスタで運動 | 3 | 4 |

## ファイル構成

```
study_support/
├── main.py              # Flaskメインアプリケーション
├── sheets_handler.py    # Googleスプレッドシート操作
├── point_system.py      # ポイントシステム管理
├── requirements.txt     # Python依存関係
├── env_example.txt      # 環境変数テンプレート
└── README.md           # このファイル
```

## 拡張機能

### 新しいポイントルールの追加

`point_system.py`で新しいルールを追加できます：

```python
point_system.add_point_rule(
    keyword='#読書',
    points=2,
    message='読書できたね！{points}pt追加したよ📚',
    description='読書を完了'
)
```

### ユーザー管理の追加

将来的にユーザーごとのポイント管理やごほうびシステムを追加できます。

## トラブルシューティング

### よくある問題

1. **LINE Webhookエラー**
   - チャネルアクセストークンとチャネルシークレットが正しく設定されているか確認
   - Webhook URLが正しく設定されているか確認

2. **Google Sheets接続エラー**
   - `credentials.json`ファイルが正しい場所にあるか確認
   - サービスアカウントにスプレッドシートの編集権限があるか確認
   - スプレッドシートIDが正しいか確認

3. **環境変数エラー**
   - `.env`ファイルが正しく作成されているか確認
   - 全ての必要な環境変数が設定されているか確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。 