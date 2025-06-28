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
        logger.info("スプレッドシートハンドラーの初期化を開始...")
        
        if not Config.SPREADSHEET_ID or Config.SPREADSHEET_ID == 'your_spreadsheet_id_here':
            logger.warning("Google Sheets設定が不完全です。スプレッドシート機能は無効化されます。")
            return False
        
        logger.info(f"認証情報ファイル: {Config.GOOGLE_SHEETS_CREDENTIALS_FILE}")
        logger.info(f"スプレッドシートID: {Config.SPREADSHEET_ID}")
        logger.info(f"ワークシート名: {Config.WORKSHEET_NAME}")
        
        # 認証情報ファイルの存在確認
        if os.path.exists(Config.GOOGLE_SHEETS_CREDENTIALS_FILE):
            logger.info("認証情報ファイルが存在します")
        else:
            logger.warning(f"認証情報ファイルが見つかりません: {Config.GOOGLE_SHEETS_CREDENTIALS_FILE}")
        
        sheets_handler = SheetsHandler(
            Config.GOOGLE_SHEETS_CREDENTIALS_FILE, 
            Config.SPREADSHEET_ID, 
            Config.WORKSHEET_NAME
        )
        
        # スプレッドシートの初期化
        if sheets_handler.initialize_sheet():
            logger.info("スプレッドシートハンドラーの初期化が完了しました")
            return True
        else:
            logger.error("スプレッドシートの初期化に失敗しました")
            return False
            
    except Exception as e:
        logger.error(f"スプレッドシートハンドラーの初期化エラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
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
    
    return jsonify({
        "validation": validation,
        "summary": summary,
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
    logger.info("="*60)
    logger.info("LINE Point System 起動中...")
    logger.info("="*60)
    
    # 設定の検証
    validation = Config.validate_config()
    if not validation['valid']:
        logger.error("設定エラー:")
        for error in validation['errors']:
            logger.error(f"  - {error}")
        logger.warning("一部の機能が制限されます")
    else:
        logger.info("✅ 設定検証が完了しました")
    
    if validation['warnings']:
        logger.warning("設定警告:")
        for warning in validation['warnings']:
            logger.warning(f"  - {warning}")
    
    # 設定概要の表示
    summary = Config.get_config_summary()
    logger.info("設定概要:")
    logger.info(f"  - Flask環境: {summary['flask_env']}")
    logger.info(f"  - デバッグモード: {summary['debug']}")
    logger.info(f"  - ホスト: {summary['host']}:{summary['port']}")
    logger.info(f"  - ワークシート名: {summary['worksheet_name']}")
    logger.info(f"  - 認証情報ファイル: {summary['credentials_file']}")
    logger.info(f"  - 認証情報作成: {summary['credentials_created']}")
    logger.info(f"  - LINE設定: {summary['line_configured']}")
    logger.info(f"  - スプレッドシート設定: {summary['sheets_configured']}")
    logger.info(f"  - 認証情報設定: {summary['credentials_configured']}")
    logger.info(f"  - ポイントルール数: {summary['point_rules_count']}")
    
    # スプレッドシートハンドラーの初期化
    logger.info("\nスプレッドシートハンドラーの初期化を開始...")
    if initialize_sheets_handler():
        logger.info("✅ スプレッドシートハンドラーの初期化が完了しました")
        logger.info("✅ アプリケーションが正常に起動しました")
    else:
        logger.warning("❌ スプレッドシートハンドラーの初期化に失敗しました")
        logger.warning("スプレッドシート機能は利用できません")
    
    logger.info("="*60)
    
    # アプリケーション起動
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG) 