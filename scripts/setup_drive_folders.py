import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Google Drive設定
SCOPES = ['https://www.googleapis.com/auth/drive.file']
PARENT_FOLDER_ID = '1sSy8mDQgtkmyODigpIiWiNh6hOJxG1Pt'  # 既存フォルダID

def authenticate():
    """Google Drive APIの認証（OAuth）"""
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def create_folder(service, folder_name, parent_folder_id):
    """Google Driveにフォルダを作成"""
    # 既存フォルダを検索
    query = f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(
        q=query,
        fields='files(id, name, webViewLink)'
    ).execute()

    folders = results.get('files', [])

    if folders:
        folder = folders[0]
        print(f'✓ 既存フォルダ: {folder_name} (ID: {folder.get("id")})')
        return folder
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }

        folder = service.files().create(
            body=file_metadata,
            fields='id, name, webViewLink'
        ).execute()

        print(f'✓ 新規作成: {folder_name} (ID: {folder.get("id")})')
        return folder

def setup_folder_structure():
    """フォルダ構造をセットアップ"""
    service = authenticate()

    print("Google Driveのフォルダ構造をセットアップします\n")
    print(f"親フォルダID: {PARENT_FOLDER_ID}\n")

    # フォルダ構成
    folders = {
        '00_raw_data': '週次平均データ（手動アップロード用）',
        '01_seo_rank_analysis': 'SEOランク・距離の分析結果',
        '02_search_console_analysis': 'Search Console(r_hash)の分析結果'
    }

    folder_ids = {}

    for folder_name, description in folders.items():
        print(f"[{folder_name}] {description}")
        folder = create_folder(service, folder_name, PARENT_FOLDER_ID)
        folder_ids[folder_name] = folder.get('id')
        print(f"  リンク: {folder.get('webViewLink')}\n")

    # フォルダIDをファイルに保存
    import json
    with open('drive_folder_ids.json', 'w') as f:
        json.dump(folder_ids, f, indent=2)

    print("✅ フォルダ構造のセットアップが完了しました")
    print(f"\nフォルダIDは drive_folder_ids.json に保存されました")

    return folder_ids

if __name__ == '__main__':
    setup_folder_structure()
