import os
import json
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SheetsHandler:
    """Googleスプレッドシート操作を管理するクラス"""
    
    def __init__(self, credentials_file: str, spreadsheet_id: str, worksheet_name: str = "ポイント記録"):
        """
        初期化
        
        Args:
            credentials_file: Google API認証情報ファイルのパス
            spreadsheet_id: スプレッドシートのID
            worksheet_name: ワークシート名
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Google Sheets APIの認証を行う"""
        try:
            # スコープの設定
            SCOPES = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = None
            
            # 1. まずファイルから認証情報を読み込みを試行
            if os.path.exists(self.credentials_file):
                try:
                    logger.info(f"認証情報ファイルから読み込み: {self.credentials_file}")
                    credentials = Credentials.from_service_account_file(
                        self.credentials_file, scopes=SCOPES
                    )
                    logger.info("ファイルからの認証情報読み込みが完了しました")
                except Exception as e:
                    logger.warning(f"ファイルからの認証情報読み込みに失敗: {e}")
            
            # 2. ファイルが存在しない場合、Base64認証情報から直接認証情報を作成
            if not credentials:
                google_credentials_base64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
                if not google_credentials_base64:
                    raise ValueError("認証情報ファイルが見つからず、GOOGLE_CREDENTIALS_BASE64も設定されていません")
                
                try:
                    logger.info("Base64認証情報から認証情報を作成中...")
                    # Base64デコード
                    credentials_json = base64.b64decode(google_credentials_base64).decode('utf-8')
                    credentials_info = json.loads(credentials_json)
                    
                    # 認証情報の妥当性を確認
                    if 'type' not in credentials_info or credentials_info['type'] != 'service_account':
                        raise ValueError("無効なサービスアカウント認証情報です")
                    
                    # 認証情報の作成
                    credentials = Credentials.from_service_account_info(
                        credentials_info, scopes=SCOPES
                    )
                    logger.info("Base64認証情報から認証が完了しました")
                    
                except Exception as e:
                    logger.error(f"Base64認証情報の処理に失敗: {e}")
                    raise
            
            # サービスオブジェクトの作成
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets API認証が完了しました")
            
        except Exception as e:
            logger.error(f"Google Sheets API認証エラー: {e}")
            raise
    
    def get_total_points(self, user_id: str) -> int:
        """
        ユーザーの合計ポイントを取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            合計ポイント
        """
        try:
            # ユーザーの記録を検索
            range_name = f"{self.worksheet_name}!A:E"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return 0
            
            # ヘッダー行をスキップ
            total_points = 0
            for row in values[1:]:  # ヘッダーを除く
                if len(row) >= 5 and row[0] == user_id:  # 新しい形式（user_id列あり）
                    try:
                        total_points += int(row[3])  # ポイント列
                    except (ValueError, IndexError):
                        continue
                elif len(row) >= 4:  # 従来の形式（user_id列なし）
                    try:
                        total_points += int(row[2])  # ポイント列
                    except (ValueError, IndexError):
                        continue
            
            return total_points
            
        except HttpError as e:
            logger.error(f"スプレッドシート読み取りエラー: {e}")
            return 0
    
    def record_action(self, user_id: str, action: str, points: int) -> bool:
        """
        行動を記録し、ポイントを追加
        
        Args:
            user_id: ユーザーID
            action: 行動内容
            points: 付与ポイント
            
        Returns:
            記録成功時True
        """
        try:
            # 現在の合計ポイントを取得
            current_total = self.get_total_points(user_id)
            new_total = current_total + points
            
            # 記録データの準備（新しい形式：user_id, 日時, 行動, ポイント, 合計ポイント）
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row_data = [user_id, timestamp, action, points, new_total]
            
            # スプレッドシートに追加
            range_name = f"{self.worksheet_name}!A:E"
            body = {
                'values': [row_data]
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"行動記録完了: {user_id} - {action} (+{points}pt)")
            return True
            
        except HttpError as e:
            logger.error(f"スプレッドシート書き込みエラー: {e}")
            return False
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        ユーザーの行動履歴を取得
        
        Args:
            user_id: ユーザーID
            limit: 取得件数
            
        Returns:
            行動履歴のリスト
        """
        try:
            range_name = f"{self.worksheet_name}!A:E"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return []
            
            # ヘッダー行をスキップして、ユーザーの記録のみを抽出
            history = []
            for row in values[1:]:
                if len(row) >= 5 and row[0] == user_id:  # 新しい形式
                    history.append({
                        'timestamp': row[1],
                        'action': row[2],
                        'points': int(row[3]),
                        'total': int(row[4])
                    })
                elif len(row) >= 4:  # 従来の形式（user_id列なし）
                    # 従来の形式の場合は、すべての記録を対象とする
                    history.append({
                        'timestamp': row[0],
                        'action': row[1],
                        'points': int(row[2]),
                        'total': int(row[3])
                    })
            
            # 最新の記録から指定件数まで返す
            return history[-limit:]
            
        except HttpError as e:
            logger.error(f"履歴取得エラー: {e}")
            return []
    
    def initialize_sheet(self) -> bool:
        """
        スプレッドシートを初期化（ヘッダー行を作成）
        
        Returns:
            初期化成功時True
        """
        try:
            # ヘッダー行の設定（新しい形式）
            headers = ['ユーザーID', '日時', '行動', 'ポイント', '合計ポイント']
            
            # 既存のデータを確認
            range_name = f"{self.worksheet_name}!A:E"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # ヘッダーが存在しない場合のみ追加
            if not values:
                body = {
                    'values': [headers]
                }
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                logger.info("スプレッドシートを初期化しました（新しい形式）")
            else:
                # 既存のヘッダーを確認し、必要に応じて更新
                existing_headers = values[0] if values else []
                if len(existing_headers) < 5 or existing_headers[0] != 'ユーザーID':
                    # ヘッダーを更新
                    body = {
                        'values': [headers]
                    }
                    
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{self.worksheet_name}!A1",
                        valueInputOption='RAW',
                        body=body
                    ).execute()
                    
                    logger.info("スプレッドシートのヘッダーを更新しました")
            
            return True
            
        except HttpError as e:
            logger.error(f"スプレッドシート初期化エラー: {e}")
            return False 