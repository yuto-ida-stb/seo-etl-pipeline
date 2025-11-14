"""
Google Driveフォルダの中身を確認
"""
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Google Drive設定
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = '1ZSbnuyV3w718eA1lF-qyuDUPxJbYGTws'

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

def list_folder_contents(service, folder_id):
    """フォルダの中身を一覧表示"""
    # 全てのファイルとフォルダを取得
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, modifiedTime)",
        orderBy="modifiedTime desc",
        pageSize=100
    ).execute()

    files = results.get('files', [])

    if not files:
        print('ファイルが見つかりませんでした')
        return

    print(f'\n{len(files)}個のアイテムを検出しました:')
    print('-' * 80)

    for file in files:
        mime_type = file['mimeType']
        # フォルダかファイルか判定
        if mime_type == 'application/vnd.google-apps.folder':
            file_type = '[フォルダ]'
        else:
            file_type = mime_type.split('/')[-1].upper()

        print(f'{file_type:15} {file["name"]:50} (ID: {file["id"]})')

if __name__ == '__main__':
    try:
        service = authenticate()
        list_folder_contents(service, FOLDER_ID)
    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()
