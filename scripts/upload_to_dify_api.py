"""
Dify APIを使ってナレッジベースを自動更新

セットアップ手順:
1. Difyでナレッジベースを作成
2. Settings → API Keys でAPI Keyを取得
3. 環境変数に設定:
   export DIFY_API_KEY="dataset-xxxxx"
   export DIFY_DATASET_ID="xxxxx-xxxxx-xxxxx"

または、.envファイルを作成:
   DIFY_API_KEY=dataset-xxxxx
   DIFY_DATASET_ID=xxxxx-xxxxx-xxxxx
"""
import os
import requests
import glob
from pathlib import Path

# Dify API設定
DIFY_API_ENDPOINT = os.getenv('DIFY_API_ENDPOINT', 'https://api.dify.ai/v1')
DIFY_API_KEY = os.getenv('DIFY_API_KEY')
DIFY_DATASET_ID = os.getenv('DIFY_DATASET_ID')

# .envファイルから読み込み
def load_env():
    """簡易的な.envファイル読み込み"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

        # 再取得
        global DIFY_API_KEY, DIFY_DATASET_ID
        DIFY_API_KEY = os.getenv('DIFY_API_KEY')
        DIFY_DATASET_ID = os.getenv('DIFY_DATASET_ID')

def check_config():
    """設定を確認"""
    if not DIFY_API_KEY:
        print("❌ エラー: DIFY_API_KEYが設定されていません")
        print()
        print("セットアップ手順:")
        print("1. https://dify.ai でナレッジベースを作成")
        print("2. Settings → API Keys でAPI Keyを取得")
        print("3. .envファイルを作成:")
        print("   DIFY_API_KEY=dataset-xxxxx")
        print("   DIFY_DATASET_ID=xxxxx-xxxxx-xxxxx")
        return False

    if not DIFY_DATASET_ID:
        print("❌ エラー: DIFY_DATASET_IDが設定されていません")
        return False

    return True

def get_existing_documents():
    """既存のドキュメント一覧を取得"""
    url = f"{DIFY_API_ENDPOINT}/datasets/{DIFY_DATASET_ID}/documents"
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        documents = data.get('data', [])

        print(f"既存ドキュメント数: {len(documents)}")
        return {doc['name']: doc['id'] for doc in documents}
    except Exception as e:
        print(f"⚠ ドキュメント一覧取得エラー: {e}")
        return {}

def update_document(doc_id, file_path):
    """既存ドキュメントを更新"""
    url = f"{DIFY_API_ENDPOINT}/datasets/{DIFY_DATASET_ID}/documents/{doc_id}/update_by_file"
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}'
    }

    file_name = os.path.basename(file_path)

    with open(file_path, 'rb') as f:
        files = {
            'file': (file_name, f, 'text/markdown')
        }
        data = {
            'name': file_name,
            'indexing_technique': 'high_quality',
            'process_rule': {
                'mode': 'custom',
                'rules': {
                    'pre_processing_rules': [
                        {'id': 'remove_extra_spaces', 'enabled': True},
                        {'id': 'remove_urls_emails', 'enabled': False}
                    ],
                    'segmentation': {
                        'separator': '###',
                        'max_tokens': 1000
                    }
                }
            }
        }

        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            print(f"  ✓ 更新完了: {file_name}")
            return True
        except Exception as e:
            print(f"  ✗ 更新失敗: {file_name} - {e}")
            return False

def create_document(file_path):
    """新規ドキュメントを作成"""
    url = f"{DIFY_API_ENDPOINT}/datasets/{DIFY_DATASET_ID}/document/create_by_file"
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}'
    }

    file_name = os.path.basename(file_path)

    with open(file_path, 'rb') as f:
        files = {
            'file': (file_name, f, 'text/markdown')
        }
        data = {
            'name': file_name,
            'indexing_technique': 'high_quality',
            'process_rule': {
                'mode': 'custom',
                'rules': {
                    'pre_processing_rules': [
                        {'id': 'remove_extra_spaces', 'enabled': True},
                        {'id': 'remove_urls_emails', 'enabled': False}
                    ],
                    'segmentation': {
                        'separator': '###',
                        'max_tokens': 1000
                    }
                }
            }
        }

        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            print(f"  ✓ 作成完了: {file_name}")
            return True
        except Exception as e:
            print(f"  ✗ 作成失敗: {file_name} - {e}")
            return False

def upload_documents(directory='./data/dify_export'):
    """指定ディレクトリのMarkdownファイルをDifyにアップロード"""
    md_files = glob.glob(os.path.join(directory, '*.md'))

    if not md_files:
        print(f"⚠ {directory} にMarkdownファイルが見つかりません")
        return

    print(f"\n{len(md_files)}個のファイルをアップロードします\n")

    # 既存ドキュメントを取得
    existing_docs = get_existing_documents()

    success_count = 0
    for file_path in md_files:
        file_name = os.path.basename(file_path)
        print(f"処理中: {file_name}")

        # 既存のドキュメントがあれば更新、なければ作成
        if file_name in existing_docs:
            doc_id = existing_docs[file_name]
            if update_document(doc_id, file_path):
                success_count += 1
        else:
            if create_document(file_path):
                success_count += 1

        print()

    print(f"✅ 完了: {success_count}/{len(md_files)}件成功")

if __name__ == '__main__':
    print("=" * 50)
    print("Dify ナレッジベース自動更新")
    print("=" * 50)
    print()

    # .envファイルから設定を読み込み
    load_env()

    # 設定確認
    if not check_config():
        exit(1)

    print(f"API Endpoint: {DIFY_API_ENDPOINT}")
    print(f"Dataset ID: {DIFY_DATASET_ID}")
    print()

    # ドキュメントをアップロード
    upload_documents()
