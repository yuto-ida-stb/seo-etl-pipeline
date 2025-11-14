import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import glob

# Google Drive設定
SCOPES = ['https://www.googleapis.com/auth/drive.file']
PARENT_FOLDER_ID = '1sSy8mDQgtkmyODigpIiWiNh6hOJxG1Pt'
ANALYSIS_DIR = './data/analysis'

# フォルダIDをロード
import json
if os.path.exists('drive_folder_ids.json'):
    with open('drive_folder_ids.json', 'r') as f:
        FOLDER_IDS = json.load(f)
else:
    FOLDER_IDS = {}

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

def create_folder_in_drive(service, folder_name, parent_folder_id):
    """Google Driveにフォルダを作成"""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }

    folder = service.files().create(
        body=file_metadata,
        fields='id, name, webViewLink'
    ).execute()

    print(f'フォルダ作成: {folder_name}')
    print(f'フォルダID: {folder.get("id")}')
    print(f'リンク: {folder.get("webViewLink")}')
    return folder

def find_or_create_folder(service, folder_name, parent_folder_id):
    """フォルダを検索、なければ作成"""
    # 既存フォルダを検索
    query = f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(
        q=query,
        fields='files(id, name, webViewLink)'
    ).execute()

    folders = results.get('files', [])

    if folders:
        folder = folders[0]
        print(f'既存フォルダを使用: {folder_name} (ID: {folder.get("id")})')
        return folder
    else:
        return create_folder_in_drive(service, folder_name, parent_folder_id)

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

    # MIMEタイプを判定
    if file_path.endswith('.csv'):
        mime_type = 'text/csv'
    elif file_path.endswith('.txt'):
        mime_type = 'text/plain'
    else:
        mime_type = 'application/octet-stream'

    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

    try:
        if existing_files:
            # 既存ファイルを更新
            file_id = existing_files[0]['id']
            file = service.files().update(
                fileId=file_id,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            print(f'更新完了: {file_name}')
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
            print(f'アップロード完了: {file_name}')

        print(f'  リンク: {file.get("webViewLink")}')
        return file
    except Exception as e:
        print(f'アップロード失敗: {file_name} - {e}')
        return None

def upload_analysis_results(service, analysis_dir):
    """SEOランク分析結果をアップロード"""
    # 最新のファイルのみをアップロード
    csv_files = sorted(glob.glob(os.path.join(analysis_dir, 'weekly_analysis_*.csv')))
    txt_files = sorted(glob.glob(os.path.join(analysis_dir, 'insights_report_*.txt')))

    if not csv_files and not txt_files:
        print(f'{analysis_dir}にアップロードするファイルが見つかりません')
        return

    # 最新のファイルを取得
    files = []
    if csv_files:
        files.append(csv_files[-1])
    if txt_files:
        files.append(txt_files[-1])

    print(f'SEOランク分析: 最新の{len(files)}個のファイルをアップロードします')

    # 01_seo_rank_analysis フォルダにアップロード
    folder_id = FOLDER_IDS.get('01_seo_rank_analysis')
    if not folder_id:
        print('エラー: フォルダIDが見つかりません。setup_drive_folders.pyを実行してください。')
        return

    print(f'アップロード先: 01_seo_rank_analysis\n')

    for file_path in files:
        upload_file(service, file_path, folder_id)
        print()

def upload_search_console_results(service, search_console_dir='./data/search_console'):
    """Search Console分析結果をアップロード"""
    # 最新のCSVファイルを取得
    csv_files = sorted(glob.glob(os.path.join(search_console_dir, 'search_console_weekly_*.csv')))

    if not csv_files:
        print(f'{search_console_dir}にアップロードするファイルが見つかりません')
        return

    latest_file = csv_files[-1]
    print(f'Search Console分析: 最新ファイルをアップロードします')

    # 02_search_console_analysis フォルダにアップロード
    folder_id = FOLDER_IDS.get('02_search_console_analysis')
    if not folder_id:
        print('エラー: フォルダIDが見つかりません。setup_drive_folders.pyを実行してください。')
        return

    print(f'アップロード先: 02_search_console_analysis\n')
    upload_file(service, latest_file, folder_id)
    print()

def upload_index_drop_results(service, analysis_dir='./data/analysis'):
    """インデックス落ち分析結果をアップロード"""
    # 最新のインデックス落ちファイルを取得
    summary_files = sorted(glob.glob(os.path.join(analysis_dir, 'index_drops_summary_*.txt')))
    final_files = sorted(glob.glob(os.path.join(analysis_dir, 'index_drops_final_*.csv')))

    if not summary_files and not final_files:
        print(f'{analysis_dir}にインデックス落ち分析結果が見つかりません')
        return

    files_to_upload = []
    if summary_files:
        files_to_upload.append(summary_files[-1])
    if final_files:
        files_to_upload.append(final_files[-1])

    print(f'インデックス落ち分析: {len(files_to_upload)}個のファイルをアップロードします')

    # 01_seo_rank_analysis フォルダにアップロード（暫定）
    folder_id = FOLDER_IDS.get('01_seo_rank_analysis')
    if not folder_id:
        print('エラー: フォルダIDが見つかりません。')
        return

    print(f'アップロード先: 01_seo_rank_analysis\n')

    for file_path in files_to_upload:
        upload_file(service, file_path, folder_id)
        print()

if __name__ == '__main__':
    try:
        service = authenticate()

        # SEOランク分析結果をアップロード
        upload_analysis_results(service, ANALYSIS_DIR)

        # Search Console分析結果をアップロード（ファイルがあれば）
        upload_search_console_results(service)

        # インデックス落ち分析結果をアップロード（ファイルがあれば）
        upload_index_drop_results(service)

        print('✓ 全てのアップロードが完了しました')
    except Exception as e:
        print(f'エラー: {e}')
        exit(1)
