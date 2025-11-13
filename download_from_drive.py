import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from pathlib import Path

# Google Drive設定
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = '1sSy8mDQgtkmyODigpIiWiNh6hOJxG1Pt'  # 共有フォルダのID
OUTPUT_DIR = './data/raw'

def authenticate():
    """Google Drive APIの認証"""
    creds = None

    # GitHub Actionsの場合は環境変数から認証情報を取得
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        creds = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS'), scopes=SCOPES)
    # ローカル実行の場合
    elif os.path.exists('credentials.json'):
        creds = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES)
    else:
        raise Exception("認証情報が見つかりません。credentials.jsonを配置するか、環境変数を設定してください。")

    return build('drive', 'v3', credentials=creds)

def download_files_from_folder(service, folder_id, output_dir):
    """指定されたGoogle DriveフォルダからCSVファイルをダウンロード"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # フォルダ内のファイルを取得
    query = f"'{folder_id}' in parents and mimeType='text/csv'"
    results = service.files().list(
        q=query,
        fields="files(id, name, modifiedTime)",
        orderBy="modifiedTime desc"
    ).execute()

    files = results.get('files', [])

    if not files:
        print('ファイルが見つかりませんでした')
        return

    print(f'{len(files)}個のCSVファイルを検出しました')

    for file in files:
        file_id = file['id']
        file_name = file['name']
        file_path = os.path.join(output_dir, file_name)

        # ファイルが既に存在する場合はスキップ
        if os.path.exists(file_path):
            print(f'スキップ: {file_name} (既に存在)')
            continue

        print(f'ダウンロード中: {file_name}')

        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        with open(file_path, 'wb') as f:
            f.write(fh.read())

        print(f'完了: {file_name}')

if __name__ == '__main__':
    try:
        service = authenticate()
        download_files_from_folder(service, FOLDER_ID, OUTPUT_DIR)
        print('\nダウンロード完了')
    except Exception as e:
        print(f'エラー: {e}')
        exit(1)
