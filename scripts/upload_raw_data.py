"""
ローカルのdata/raw/にあるCSVファイルをGoogle Driveの00_raw_dataフォルダにアップロード
"""
import os
import pickle
import glob
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

# Google Drive設定
SCOPES = ['https://www.googleapis.com/auth/drive.file']
LOCAL_DIR = './data/raw'

# フォルダIDをロード
if os.path.exists('drive_folder_ids.json'):
    with open('drive_folder_ids.json', 'r') as f:
        FOLDER_IDS = json.load(f)
    FOLDER_ID = FOLDER_IDS.get('00_raw_data')
    if not FOLDER_ID:
        print("エラー: 00_raw_data フォルダIDが見つかりません")
        print("python scripts/setup_drive_folders.py を実行してください")
        exit(1)
else:
    print("エラー: drive_folder_ids.json が見つかりません")
    print("python scripts/setup_drive_folders.py を実行してください")
    exit(1)

def authenticate():
    """Google Drive APIの認証（OAuth）"""
    creds = None

    # token.pickleファイルがあれば読み込む
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 認証情報が無効または存在しない場合
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # OAuth認証フローを開始
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # 認証情報を保存
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def upload_file(service, file_path, folder_id):
    """ファイルをGoogle Driveにアップロード"""
    file_name = os.path.basename(file_path)

    # 既存ファイルを検索
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields='files(id, name)'
    ).execute()

    existing_files = results.get('files', [])

    media = MediaFileUpload(file_path, mimetype='text/csv', resumable=True)

    try:
        if existing_files:
            # 既存ファイルを更新
            file_id = existing_files[0]['id']
            file = service.files().update(
                fileId=file_id,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            print(f'更新: {file_name}')
        else:
            # 新規ファイルを作成
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            print(f'アップロード: {file_name}')

        return file
    except Exception as e:
        print(f'失敗: {file_name} - {e}')
        return None

if __name__ == '__main__':
    print("=" * 50)
    print("Google Driveに生データをアップロード")
    print("=" * 50)
    print()

    # CSVファイルを取得
    csv_files = glob.glob(os.path.join(LOCAL_DIR, '*.csv'))

    if not csv_files:
        print(f"{LOCAL_DIR} にCSVファイルが見つかりません")
        exit(1)

    print(f"{len(csv_files)}個のファイルをアップロードします")
    print(f"アップロード先: 00_raw_data フォルダ (ID: {FOLDER_ID})")
    print()

    service = authenticate()

    success_count = 0
    for file_path in csv_files:
        if upload_file(service, file_path, FOLDER_ID):
            success_count += 1

    print()
    print("=" * 50)
    print(f"✅ 完了: {success_count}/{len(csv_files)}件")
    print("=" * 50)
