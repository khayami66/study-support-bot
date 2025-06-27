import os
import logging
import random
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from sheets_handler import SheetsHandler
from point_system import PointSystem
from config import Config

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flaskアプリの初期化
app = Flask(__name__)
app.secret_key = Config.FLASK_SECRET_KEY

# LINE Bot設定
line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)

# ポイントシステムとスプレッドシートハンドラーの初期化
point_system = PointSystem()
sheets_handler = None

def initialize_sheets_handler():
    """スプレッドシートハンドラーを初期化"""
    global sheets_handler
    try:
        # 設定の確認
        if not Config.SPREADSHEET_ID or Config.SPREADSHEET_ID == 'your_spreadsheet_id_here':
            logger.error("SPREADSHEET_IDが設定されていません。環境変数を確認してください。")
            return False
        
        if not os.path.exists(Config.GOOGLE_SHEETS_CREDENTIALS_FILE):
            logger.error(f"Google API認証情報ファイルが見つかりません: {Config.GOOGLE_SHEETS_CREDENTIALS_FILE}")
            return False
        
        logger.info(f"スプレッドシート設定:")
        logger.info(f"  - スプレッドシートID: {Config.SPREADSHEET_ID}")
        logger.info(f"  - ワークシート名: {Config.WORKSHEET_NAME}")
        logger.info(f"  - 認証情報ファイル: {Config.GOOGLE_SHEETS_CREDENTIALS_FILE}")
        
        # スプレッドシートハンドラーの作成
        sheets_handler = SheetsHandler(
            Config.GOOGLE_SHEETS_CREDENTIALS_FILE, 
            Config.SPREADSHEET_ID, 
            Config.WORKSHEET_NAME
        )
        
        # スプレッドシートの初期化
        if sheets_handler.initialize_sheet():
            logger.info("✅ スプレッドシートハンドラーの初期化が完了しました")
            
            # 接続テスト
            try:
                # テスト用のデータ取得（空の結果でもエラーにならない）
                test_range = f"{Config.WORKSHEET_NAME}!A1"
                sheets_handler.service.spreadsheets().values().get(
                    spreadsheetId=Config.SPREADSHEET_ID,
                    range=test_range
                ).execute()
                logger.info("✅ スプレッドシートへの接続テストが成功しました")
                return True
            except Exception as e:
                logger.error(f"❌ スプレッドシートへの接続テストに失敗: {e}")
                return False
        else:
            logger.error("❌ スプレッドシートの初期化に失敗しました")
            return False
            
    except Exception as e:
        logger.error(f"❌ スプレッドシートハンドラーの初期化エラー: {e}")
        return False

@app.route("/callback", methods=['POST'])
def callback():
    """LINE Webhookのコールバックエンドポイント"""
    # リクエストヘッダーからX-Line-Signatureを取得
    signature = request.headers['X-Line-Signature']

    # リクエストボディを取得
    body = request.get_data(as_text=True)
    logger.info("Request body: " + body)

    try:
        # 署名を検証し、問題なければhandleに定義されている関数を呼び出す
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """テキストメッセージの処理"""
    try:
        user_id = event.source.user_id
        message_text = event.message.text
        
        logger.info(f"受信メッセージ: {message_text} (ユーザー: {user_id})")
        
        # ヘルプコマンドの処理
        if message_text.lower() in ['#help', '#ヘルプ', 'help', 'ヘルプ']:
            help_message = point_system.get_help_message()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_message))
            return
        
        # ポイント確認コマンドの処理
        if message_text.lower() in ['#ポイント', '#point', 'ポイント', 'point']:
            if sheets_handler:
                total_points = sheets_handler.get_total_points(user_id)
                response_message = f"現在の合計ポイント: {total_points}pt 🎯"
            else:
                response_message = "スプレッドシートに接続できません😅\n設定を確認してください。"
            
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))
            return
        
        # 履歴確認コマンドの処理
        if message_text.lower() in ['#履歴', '#history', '履歴', 'history']:
            if sheets_handler:
                history = sheets_handler.get_user_history(user_id, limit=Config.DEFAULT_HISTORY_LIMIT)
                if history:
                    history_lines = ["📋 最近の行動履歴："]
                    for record in history:
                        history_lines.append(f"• {record['action']} (+{record['points']}pt) - {record['timestamp']}")
                    response_message = "\n".join(history_lines)
                else:
                    response_message = "まだ行動履歴がありません😊"
            else:
                response_message = "スプレッドシートに接続できません😅\n設定を確認してください。"
            
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))
            return
        
        # ポイントルールの解析
        matches = point_system.parse_message(message_text)
        
        if not matches:
            # ポイント対象の行動が見つからない場合
            response_message = "ポイント対象の行動が見つからなかったよ😅\n\n" + point_system.get_help_message()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))
            return
        
        # スプレッドシートハンドラーが初期化されていない場合
        if not sheets_handler:
            response_message = "申し訳ありません。スプレッドシートの設定が完了していません😅\n\n設定を確認してください。"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))
            return
        
        # 各マッチしたルールに対してポイントを記録
        total_points_earned = 0
        recorded_actions = []
        
        for keyword, points, _ in matches:
            action_description = point_system.get_point_rule(keyword)['description']
            
            # スプレッドシートに記録
            if sheets_handler.record_action(user_id, action_description, points):
                total_points_earned += points
                recorded_actions.append(f"{action_description} (+{points}pt)")
            else:
                logger.error(f"行動記録に失敗: {action_description}")
        
        # 現在の合計ポイントを取得
        current_total = sheets_handler.get_total_points(user_id)
        
        # 返信メッセージの生成
        if total_points_earned > 0:
            if len(recorded_actions) == 1:
                response_message = f"{recorded_actions[0]} がんばったね！✨（合計：{current_total}pt）"
            else:
                actions_text = "、".join(recorded_actions)
                response_message = f"{actions_text} たくさんがんばったね！🎉（合計：{current_total}pt）"
        else:
            response_message = "ポイントの記録に失敗しました😅"
        
        # LINEに返信
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))
        
        # 100ptごと達成をチェック（前回の合計ポイントと比較）
        previous_total = current_total - total_points_earned
        prev_celebrate = previous_total // 100
        curr_celebrate = current_total // 100
        if curr_celebrate > prev_celebrate and curr_celebrate >= 1:
            celebrate_pt = curr_celebrate * 100
            if celebrate_pt in Config.CELEBRATION_MESSAGES:
                celebration_message = random.choice(Config.CELEBRATION_MESSAGES[celebrate_pt])
            else:
                # 500pt以降は500ptのメッセージを使い回す
                celebration_message = random.choice(Config.CELEBRATION_MESSAGES[500])
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text=celebration_message))
                logger.info(f"{celebrate_pt}pt達成お祝いメッセージを送信: {user_id}")
            except Exception as e:
                logger.error(f"お祝いメッセージ送信エラー: {e}")
        
    except Exception as e:
        logger.error(f"メッセージ処理エラー: {e}")
        try:
            error_message = "申し訳ありません。エラーが発生しました😅"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error_message))
        except:
            pass

@app.route("/health", methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "message": "LINE Point System is running"}

@app.route("/config", methods=['GET'])
def config_status():
    """設定状況を確認するエンドポイント"""
    validation = Config.validate_config()
    summary = Config.get_config_summary()
    
    # スプレッドシートの接続状況を詳細に確認
    sheets_status = {
        "connected": sheets_handler is not None,
        "credentials_file_exists": os.path.exists(Config.GOOGLE_SHEETS_CREDENTIALS_FILE),
        "spreadsheet_id_configured": bool(Config.SPREADSHEET_ID and Config.SPREADSHEET_ID != 'your_spreadsheet_id_here'),
        "worksheet_name": Config.WORKSHEET_NAME
    }
    
    if sheets_handler:
        try:
            # 接続テスト
            test_range = f"{Config.WORKSHEET_NAME}!A1"
            sheets_handler.service.spreadsheets().values().get(
                spreadsheetId=Config.SPREADSHEET_ID,
                range=test_range
            ).execute()
            sheets_status["connection_test"] = "success"
        except Exception as e:
            sheets_status["connection_test"] = f"failed: {str(e)}"
    else:
        sheets_status["connection_test"] = "not_initialized"
    
    return jsonify({
        "validation": validation,
        "summary": summary,
        "sheets_status": sheets_status,
        "sheets_connected": sheets_handler is not None
    })

@app.route("/", methods=['GET'])
def index():
    """ルートエンドポイント"""
    return """
    <h1>LINE Point System</h1>
    <p>LINEメッセージに応じてポイントを付与し、Googleスプレッドシートに記録するシステムです。</p>
    <h2>使用方法</h2>
    <ul>
        <li><code>#宿題</code> - 宿題完了で1pt</li>
        <li><code>#スタスタ</code> - スタスタ完了で3pt</li>
        <li><code>#ポイント</code> - 現在の合計ポイントを確認</li>
        <li><code>#履歴</code> - 最近の行動履歴を確認</li>
        <li><code>#ヘルプ</code> - ヘルプを表示</li>
    </ul>
    <h2>管理エンドポイント</h2>
    <ul>
        <li><a href="/health">/health</a> - ヘルスチェック</li>
        <li><a href="/config">/config</a> - 設定状況確認</li>
    </ul>
    """

if __name__ == "__main__":
    print("=" * 60)
    print("LINE Point System 起動中...")
    print("=" * 60)
    
    # 設定の検証
    validation = Config.validate_config()
    if not validation['valid']:
        print("❌ 設定エラー:")
        for error in validation['errors']:
            print(f"  - {error}")
        print("\n⚠️  一部の機能が制限されます")
    else:
        print("✅ 設定の検証が完了しました")
    
    if validation['warnings']:
        print("\n⚠️  設定警告:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    print("\n" + "=" * 60)
    print("スプレッドシート設定の確認中...")
    print("=" * 60)
    
    # スプレッドシートハンドラーの初期化
    if initialize_sheets_handler():
        print("✅ アプリケーションが正常に起動しました")
        print("📊 スプレッドシート機能: 有効")
    else:
        print("❌ スプレッドシートハンドラーの初期化に失敗しました")
        print("📊 スプレッドシート機能: 無効")
        print("\n🔧 設定を確認してください:")
        print("  1. SPREADSHEET_IDが正しく設定されているか")
        print("  2. credentials.jsonファイルが存在するか")
        print("  3. スプレッドシートへのアクセス権限があるか")
    
    print("\n" + "=" * 60)
    print("アプリケーション起動中...")
    print("=" * 60)
    
    # アプリケーション起動
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG) 