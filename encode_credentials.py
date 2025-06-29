#!/usr/bin/env python3
"""
Google認証情報（credentials.json）をJSON文字列として出力するスクリプト
Renderデプロイ用の環境変数設定に使用します。
"""

import json
import os
import sys

def encode_credentials():
    """credentials.jsonファイルをJSON文字列として出力"""
    
    # ファイルの存在確認
    if not os.path.exists('credentials.json'):
        print("❌ credentials.jsonファイルが見つかりません")
        print("Google Cloud Consoleからダウンロードした認証情報ファイルを、")
        print("このスクリプトと同じディレクトリに 'credentials.json' として保存してください。")
        return False
    
    try:
        # ファイルを読み込み
        with open('credentials.json', 'r', encoding='utf-8') as f:
            credentials_data = json.load(f)
        
        # 認証情報の妥当性を確認
        if 'type' not in credentials_data or credentials_data['type'] != 'service_account':
            print("❌ 無効なサービスアカウント認証情報です")
            return False
        
        # JSON文字列として出力
        credentials_json = json.dumps(credentials_data, separators=(',', ':'))
        
        print("✅ credentials.jsonのJSON文字列変換が完了しました")
        print("\n" + "="*50)
        print("以下の文字列をGOOGLE_CREDENTIALS_JSON環境変数に設定してください：")
        print("="*50)
        print(credentials_json)
        print("="*50)
        
        # ファイルに保存（オプション）
        save_to_file = input("\nこの文字列をencoded_credentials.txtに保存しますか？ (y/n): ").lower()
        if save_to_file == 'y':
            with open('encoded_credentials.txt', 'w') as f:
                f.write(credentials_json)
            print("✅ encoded_credentials.txtに保存しました")
        
        return True
        
    except Exception as e:
        print(f"❌ 変換中にエラーが発生しました: {e}")
        return False

def main():
    """メイン関数"""
    print("🔐 Google認証情報JSON文字列変換ツール")
    print("="*40)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("\n使用方法:")
        print("  python encode_credentials.py")
        print("\n必要なファイル:")
        print("  - credentials.json (Google Cloud Consoleからダウンロード)")
        print("\n出力:")
        print("  - JSON文字列")
        print("  - encoded_credentials.txt (オプション)")
        return
    
    success = encode_credentials()
    
    if success:
        print("\n📝 次のステップ:")
        print("1. 上記の文字列をコピー")
        print("2. Renderダッシュボードの環境変数設定で")
        print("   GOOGLE_CREDENTIALS_JSON に貼り付け")
        print("3. デプロイを実行")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 