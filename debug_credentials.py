#!/usr/bin/env python3
"""
認証情報のデバッグとbase64復元を確認するスクリプト
Renderデプロイ時の問題解決に使用します。
"""

import os
import base64
import json
import tempfile
from dotenv import load_dotenv

def debug_credentials():
    """認証情報のデバッグ"""
    print("🔍 認証情報デバッグツール")
    print("="*50)
    
    # 環境変数の読み込み
    load_dotenv()
    
    # 環境変数の確認
    google_credentials_base64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
    credentials_file_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    
    print(f"1. 環境変数の確認:")
    print(f"   GOOGLE_CREDENTIALS_BASE64: {'設定済み' if google_credentials_base64 else '未設定'}")
    print(f"   GOOGLE_SHEETS_CREDENTIALS_FILE: {credentials_file_path}")
    
    if not google_credentials_base64:
        print("❌ GOOGLE_CREDENTIALS_BASE64が設定されていません")
        return False
    
    # Base64デコードのテスト
    print(f"\n2. Base64デコードのテスト:")
    try:
        # Base64デコード
        credentials_json = base64.b64decode(google_credentials_base64).decode('utf-8')
        print("✅ Base64デコード成功")
        
        # JSONパースのテスト
        credentials_info = json.loads(credentials_json)
        print("✅ JSONパース成功")
        
        # 認証情報の妥当性確認
        if 'type' in credentials_info:
            print(f"✅ 認証情報タイプ: {credentials_info['type']}")
        else:
            print("❌ 認証情報タイプが見つかりません")
            return False
        
        if credentials_info.get('type') != 'service_account':
            print("❌ サービスアカウント認証情報ではありません")
            return False
        
        if 'client_email' in credentials_info:
            print(f"✅ クライアントメール: {credentials_info['client_email']}")
        else:
            print("❌ クライアントメールが見つかりません")
            return False
        
        if 'project_id' in credentials_info:
            print(f"✅ プロジェクトID: {credentials_info['project_id']}")
        else:
            print("❌ プロジェクトIDが見つかりません")
            return False
        
    except Exception as e:
        print(f"❌ Base64デコードまたはJSONパースに失敗: {e}")
        return False
    
    # ファイル作成のテスト
    print(f"\n3. 認証情報ファイル作成のテスト:")
    try:
        # 一時ファイルとして作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file.write(credentials_json)
            temp_credentials_path = temp_file.name
        
        print(f"✅ 一時ファイル作成成功: {temp_credentials_path}")
        
        # ファイルの存在確認
        if os.path.exists(temp_credentials_path):
            print("✅ ファイル存在確認成功")
            
            # ファイルサイズの確認
            file_size = os.path.getsize(temp_credentials_path)
            print(f"✅ ファイルサイズ: {file_size} bytes")
            
            # ファイル内容の読み込みテスト
            with open(temp_credentials_path, 'r') as f:
                test_content = f.read()
                test_info = json.loads(test_content)
                print("✅ ファイル読み込みテスト成功")
            
            # 一時ファイルの削除
            os.unlink(temp_credentials_path)
            print("✅ 一時ファイル削除完了")
            
        else:
            print("❌ ファイル存在確認失敗")
            return False
        
    except Exception as e:
        print(f"❌ ファイル作成テストに失敗: {e}")
        return False
    
    print(f"\n✅ 全てのテストが成功しました！")
    return True

def restore_credentials():
    """認証情報ファイルを復元"""
    print("\n🔄 認証情報ファイルの復元")
    print("="*50)
    
    load_dotenv()
    google_credentials_base64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
    
    if not google_credentials_base64:
        print("❌ GOOGLE_CREDENTIALS_BASE64が設定されていません")
        return False
    
    try:
        # Base64デコード
        credentials_json = base64.b64decode(google_credentials_base64).decode('utf-8')
        
        # 認証情報の妥当性を確認
        credentials_info = json.loads(credentials_json)
        if 'type' not in credentials_info or credentials_info['type'] != 'service_account':
            raise ValueError("無効なサービスアカウント認証情報です")
        
        # 一時ファイルとして作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file.write(credentials_json)
            temp_credentials_path = temp_file.name
        
        # 環境変数を更新
        os.environ['GOOGLE_SHEETS_CREDENTIALS_FILE'] = temp_credentials_path
        print(f"✅ 認証情報ファイルを復元しました: {temp_credentials_path}")
        
        return temp_credentials_path
        
    except Exception as e:
        print(f"❌ 認証情報ファイルの復元に失敗: {e}")
        return False

def main():
    """メイン関数"""
    print("🔐 Google認証情報デバッグ・復元ツール")
    print("="*60)
    
    # デバッグ実行
    if debug_credentials():
        print("\n📝 デバッグ結果: 認証情報は正常です")
        
        # 復元の確認
        restore = input("\n認証情報ファイルを復元しますか？ (y/n): ").lower()
        if restore == 'y':
            restored_path = restore_credentials()
            if restored_path:
                print(f"\n✅ 復元完了！")
                print(f"ファイルパス: {restored_path}")
                print(f"環境変数: GOOGLE_SHEETS_CREDENTIALS_FILE={restored_path}")
            else:
                print("❌ 復元に失敗しました")
    else:
        print("\n❌ デバッグ結果: 認証情報に問題があります")
        print("環境変数 GOOGLE_CREDENTIALS_BASE64 を確認してください")

if __name__ == "__main__":
    main() 