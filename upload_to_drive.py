import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import glob

# Google Drive設定
SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = '1sSy8mDQgtkmyODigpIiWiNh6hOJxG1Pt'  # アップロード先フォルダのID
ANALYSIS_DIR = './data/analysis'

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

def upload_file(service, file_path, folder_id):
    """ファイルをGoogle Driveにアップロード"""
    file_name = os.path.basename(file_path)

    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }

    # MIMEタイプを判定
    if file_path.endswith('.csv'):
        mime_type = 'text/csv'
    elif file_path.endswith('.txt'):
        mime_type = 'text/plain'
    else:
        mime_type = 'application/octet-stream'

    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()

        print(f'アップロード完了: {file_name}')
        print(f'リンク: {file.get("webViewLink")}')
        return file
    except Exception as e:
        print(f'アップロード失敗: {file_name} - {e}')
        return None

def upload_analysis_results(service, analysis_dir, folder_id):
    """分析結果ファイルを全てアップロード"""
    # CSVファイルとTXTファイルを取得
    files = glob.glob(os.path.join(analysis_dir, '*.csv'))
    files += glob.glob(os.path.join(analysis_dir, '*.txt'))

    if not files:
        print(f'{analysis_dir}にアップロードするファイルが見つかりません')
        return

    print(f'{len(files)}個のファイルをアップロードします')

    for file_path in files:
        upload_file(service, file_path, folder_id)

if __name__ == '__main__':
    try:
        service = authenticate()
        upload_analysis_results(service, ANALYSIS_DIR, FOLDER_ID)
        print('\nアップロード完了')
    except Exception as e:
        print(f'エラー: {e}')
        exit(1)
