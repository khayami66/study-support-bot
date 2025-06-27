import os
from typing import Dict, Any
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

class Config:
    """アプリケーション設定を管理するクラス"""
    
    # LINE Messaging API設定
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
    
    # Google Sheets API設定
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
    WORKSHEET_NAME = os.getenv('WORKSHEET_NAME', 'ポイント記録')
    
    # Flask設定
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # アプリケーション設定
    DEBUG = FLASK_ENV == 'development'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # ポイントシステム設定
    DEFAULT_POINT_RULES = {
        '#宿題': {
            'points': 1,
            'message': '宿題がんばったね！{points}pt追加したよ✨',
            'description': '宿題を完了'
        },
        '#スタスタ': {
            'points': 3,
            'message': 'スタスタで運動できたね！{points}pt追加したよ💪',
            'description': 'スタスタを完了'
        },
        '#ごみ捨て': {
            'points': 5,
            'message': 'ごみ捨てお疲れさま！{points}pt追加したよ🗑️',
            'description': 'ごみ捨てを完了'
        }
    }
    
    # 履歴設定
    DEFAULT_HISTORY_LIMIT = 10
    
    # 100ptごと達成お祝いメッセージ設定
    CELEBRATION_MESSAGES = {
        100: [
            "🎉 100pt達成おめでとう！君の努力が形になってるよ！✨",
            "🌟 100ptゲット！毎日コツコツがんばってるね！すごいぞ！💪",
            "🏆 100pt達成！君は本当に頑張り屋さんだね！この調子で続けよう！🎊"
        ],
        200: [
            "🎉 200pt達成！すごいぞ！この調子でどんどんチャレンジしよう！",
            "🚀 200pt達成！君のやる気がどんどんパワーアップしてるね！",
            "🌈 200pt達成！毎日の積み重ねが力になってるよ！"
        ],
        300: [
            "🏆 300pt達成！君の継続力は本当に素晴らしい！",
            "🎊 300pt達成！ここまで続けられる君は本当にすごい！",
            "💫 300pt達成！君の努力は必ず実を結ぶよ！"
        ],
        400: [
            "🌟 400pt達成！毎日コツコツがんばってるね！",
            "🎉 400pt達成！君の成長が目に見えてるよ！素晴らしい！",
            "🚀 400pt達成！この調子でどんどん進もう！"
        ],
        500: [
            "🚀 500pt達成！ここまで続けられる君は本当にすごい！",
            "🏅 500pt達成！君の継続力は本物だね！",
            "🎉 500pt達成！これからも一緒にがんばろう！"
        ]
    }
    # それ以降（600pt, 700pt...）は500ptのメッセージを使い回します
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """
        設定の妥当性を検証
        
        Returns:
            検証結果の辞書
        """
        errors = []
        warnings = []
        
        # 必須設定の確認
        if not cls.LINE_CHANNEL_ACCESS_TOKEN:
            errors.append("LINE_CHANNEL_ACCESS_TOKENが設定されていません")
        
        if not cls.LINE_CHANNEL_SECRET:
            errors.append("LINE_CHANNEL_SECRETが設定されていません")
        
        if not cls.SPREADSHEET_ID:
            errors.append("SPREADSHEET_IDが設定されていません")
        
        # 警告の確認
        if cls.FLASK_SECRET_KEY == 'default-secret-key-change-in-production':
            warnings.append("本番環境ではFLASK_SECRET_KEYを変更してください")
        
        if not os.path.exists(cls.GOOGLE_SHEETS_CREDENTIALS_FILE):
            errors.append(f"Google API認証情報ファイルが見つかりません: {cls.GOOGLE_SHEETS_CREDENTIALS_FILE}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """
        設定の概要を取得（機密情報は除く）
        
        Returns:
            設定概要の辞書
        """
        return {
            'flask_env': cls.FLASK_ENV,
            'debug': cls.DEBUG,
            'host': cls.HOST,
            'port': cls.PORT,
            'worksheet_name': cls.WORKSHEET_NAME,
            'credentials_file': cls.GOOGLE_SHEETS_CREDENTIALS_FILE,
            'line_configured': bool(cls.LINE_CHANNEL_ACCESS_TOKEN and cls.LINE_CHANNEL_SECRET),
            'sheets_configured': bool(cls.SPREADSHEET_ID),
            'point_rules_count': len(cls.DEFAULT_POINT_RULES)
        } 