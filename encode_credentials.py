#!/usr/bin/env python3
"""
Google認証情報（credentials.json）をBase64エンコードするスクリプト
Renderデプロイ用の環境変数設定に使用します。
"""

import base64
import os
import sys

def encode_credentials():
    """credentials.jsonファイルをBase64エンコード"""
    
    # ファイルの存在確認
    if not os.path.exists('credentials.json'):
        print("❌ credentials.jsonファイルが見つかりません")
        print("Google Cloud Consoleからダウンロードした認証情報ファイルを、")
        print("このスクリプトと同じディレクトリに 'credentials.json' として保存してください。")
        return False
    
    try:
        # ファイルを読み込み
        with open('credentials.json', 'rb') as f:
            credentials_data = f.read()
        
        # Base64エンコード
        encoded = base64.b64encode(credentials_data).decode('utf-8')
        
        print("✅ credentials.jsonのBase64エンコードが完了しました")
        print("\n" + "="*50)
        print("以下の文字列をGOOGLE_CREDENTIALS_BASE64環境変数に設定してください：")
        print("="*50)
        print(encoded)
        print("="*50)
        
        # ファイルに保存（オプション）
        save_to_file = input("\nこの文字列をencoded_credentials.txtに保存しますか？ (y/n): ").lower()
        if save_to_file == 'y':
            with open('encoded_credentials.txt', 'w') as f:
                f.write(encoded)
            print("✅ encoded_credentials.txtに保存しました")
        
        return True
        
    except Exception as e:
        print(f"❌ エンコード中にエラーが発生しました: {e}")
        return False

def main():
    """メイン関数"""
    print("🔐 Google認証情報Base64エンコーダー")
    print("="*40)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("\n使用方法:")
        print("  python encode_credentials.py")
        print("\n必要なファイル:")
        print("  - credentials.json (Google Cloud Consoleからダウンロード)")
        print("\n出力:")
        print("  - Base64エンコードされた文字列")
        print("  - encoded_credentials.txt (オプション)")
        return
    
    success = encode_credentials()
    
    if success:
        print("\n📝 次のステップ:")
        print("1. 上記の文字列をコピー")
        print("2. Renderダッシュボードの環境変数設定で")
        print("   GOOGLE_CREDENTIALS_BASE64 に貼り付け")
        print("3. デプロイを実行")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 