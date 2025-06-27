import os
import json
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
            # 認証情報の読み込み
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(f"認証情報ファイルが見つかりません: {self.credentials_file}")
            
            # スコープの設定
            SCOPES = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # 認証情報の作成
            credentials = Credentials.from_service_account_file(
                self.credentials_file, scopes=SCOPES
            )
            
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
            range_name = f"{self.worksheet_name}!A:D"
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
                if len(row) >= 4 and row[0] == user_id:  # user_id列が存在する場合
                    try:
                        total_points += int(row[3])  # ポイント列
                    except (ValueError, IndexError):
                        continue
                elif len(row) >= 3:  # 従来の形式（user_id列なし）
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
            
            # 記録データの準備
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row_data = [timestamp, action, points, new_total]
            
            # スプレッドシートに追加
            range_name = f"{self.worksheet_name}!A:D"
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
            
            logger.info(f"行動記録完了: {action} (+{points}pt)")
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
            range_name = f"{self.worksheet_name}!A:D"
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
                if len(row) >= 4 and row[0] == user_id:
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
            # ヘッダー行の設定
            headers = ['日時', '行動', 'ポイント', '合計ポイント']
            
            # 既存のデータを確認
            range_name = f"{self.worksheet_name}!A:D"
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
                
                logger.info("スプレッドシートを初期化しました")
            
            return True
            
        except HttpError as e:
            logger.error(f"スプレッドシート初期化エラー: {e}")
            return False 