from typing import Dict, List, Optional, Tuple
import re
import logging
from config import Config

logger = logging.getLogger(__name__)

class PointSystem:
    """ポイントシステムを管理するクラス"""
    
    def __init__(self):
        """初期化時にデフォルトのポイントルールを設定"""
        self.point_rules = Config.DEFAULT_POINT_RULES.copy()
    
    def add_point_rule(self, keyword: str, points: int, message: str, description: str = ""):
        """
        新しいポイントルールを追加
        
        Args:
            keyword: 検索キーワード
            points: 付与ポイント
            message: 返信メッセージ（{points}プレースホルダー使用可能）
            description: ルールの説明
        """
        self.point_rules[keyword] = {
            'points': points,
            'message': message,
            'description': description
        }
        logger.info(f"新しいポイントルールを追加: {keyword} ({points}pt)")
    
    def remove_point_rule(self, keyword: str) -> bool:
        """
        ポイントルールを削除
        
        Args:
            keyword: 削除するキーワード
            
        Returns:
            削除成功時True
        """
        if keyword in self.point_rules:
            del self.point_rules[keyword]
            logger.info(f"ポイントルールを削除: {keyword}")
            return True
        return False
    
    def get_point_rule(self, keyword: str) -> Optional[Dict]:
        """
        指定されたキーワードのポイントルールを取得
        
        Args:
            keyword: 検索キーワード
            
        Returns:
            ポイントルール（存在しない場合はNone）
        """
        return self.point_rules.get(keyword)
    
    def get_all_rules(self) -> Dict[str, Dict]:
        """
        全てのポイントルールを取得
        
        Returns:
            ポイントルールの辞書
        """
        return self.point_rules.copy()
    
    def parse_message(self, message: str) -> List[Tuple[str, int, str]]:
        """
        メッセージを解析してポイントルールにマッチするものを抽出
        
        Args:
            message: 解析するメッセージ
            
        Returns:
            (キーワード, ポイント, メッセージ)のタプルのリスト
        """
        matches = []
        
        for keyword, rule in self.point_rules.items():
            if keyword in message:
                points = rule['points']
                response_message = rule['message'].format(points=points)
                matches.append((keyword, points, response_message))
        
        return matches
    
    def get_total_points_for_message(self, message: str) -> int:
        """
        メッセージから合計ポイントを計算
        
        Args:
            message: 解析するメッセージ
            
        Returns:
            合計ポイント
        """
        matches = self.parse_message(message)
        return sum(points for _, points, _ in matches)
    
    def format_response_message(self, matches: List[Tuple[str, int, str]], total_points: int) -> str:
        """
        返信メッセージをフォーマット
        
        Args:
            matches: マッチしたルールのリスト
            total_points: 合計ポイント
            
        Returns:
            フォーマットされた返信メッセージ
        """
        if not matches:
            return "ポイント対象の行動が見つからなかったよ😅"
        
        # 複数のルールにマッチした場合の処理
        if len(matches) == 1:
            keyword, points, message = matches[0]
            return f"{message}（合計：{total_points}pt）"
        else:
            # 複数マッチの場合は個別メッセージを結合
            messages = []
            for keyword, points, message in matches:
                messages.append(f"{message}")
            
            combined_message = " ".join(messages)
            return f"{combined_message}（合計：{total_points}pt）"
    
    def get_help_message(self) -> str:
        """
        ヘルプメッセージを生成
        
        Returns:
            ヘルプメッセージ
        """
        if not self.point_rules:
            return "現在、ポイント対象の行動は設定されていません。"
        
        help_lines = ["📝 ポイント対象の行動一覧："]
        
        for keyword, rule in self.point_rules.items():
            points = rule['points']
            description = rule['description'] or keyword
            help_lines.append(f"• {keyword} → {points}pt ({description})")
        
        help_lines.append("\n💡 メッセージに上記のキーワードを含めて送信するとポイントが付与されます！")
        
        return "\n".join(help_lines) 