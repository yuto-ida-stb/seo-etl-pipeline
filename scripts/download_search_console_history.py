import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from pathlib import Path
from datetime import datetime, timedelta

# Google Drive設定
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
OUTPUT_DIR = './data/search_console'

# フォルダIDをロード
import json
if os.path.exists('drive_folder_ids.json'):
    with open('drive_folder_ids.json', 'r') as f:
        FOLDER_IDS = json.load(f)
    FOLDER_ID = FOLDER_IDS.get('02_search_console_analysis')
    if not FOLDER_ID:
        print("エラー: 02_search_console_analysisフォルダIDが見つかりません")
        exit(1)
else:
    print("エラー: drive_folder_ids.jsonが見つかりません")
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

def download_search_console_history(service, folder_id, output_dir, months=3):
    """
    Google Driveから過去N ヶ月分のSearch Console週次データをダウンロード

    Args:
        service: Google Drive APIサービス
        folder_id: 02_search_console_analysisフォルダID
        output_dir: 出力ディレクトリ
        months: ダウンロードする期間（月数）
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 過去N ヶ月の日付を計算
    cutoff_date = datetime.now() - timedelta(days=months * 30)

    print("="*80)
    print(f"Google Drive 02_search_console_analysis から過去{months}ヶ月分のデータをダウンロード")
    print("="*80)
    print(f"フォルダID: {folder_id}")
    print(f"期間: {cutoff_date.strftime('%Y-%m-%d')} 以降\n")

    # search_console_weekly_*.csv ファイルを検索
    query = f"'{folder_id}' in parents and name contains 'search_console_weekly_' and (mimeType='text/csv' or mimeType='text/plain')"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, modifiedTime)",
        orderBy="modifiedTime desc"
    ).execute()

    files = results.get('files', [])

    if not files:
        print('Search Console週次データが見つかりませんでした')
        return

    print(f'{len(files)}個のSearch Console週次ファイルを検出しました\n')

    # 過去N ヶ月以内のファイルのみダウンロード
    downloaded_count = 0
    for file in files:
        file_id = file['id']
        file_name = file['name']
        modified_time = datetime.strptime(file['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ')

        # 過去N ヶ月以内のファイルのみ
        if modified_time < cutoff_date:
            print(f'スキップ（期間外）: {file_name} (更新日: {modified_time.strftime("%Y-%m-%d")})')
            continue

        file_path = os.path.join(output_dir, file_name)

        print(f'ダウンロード中: {file_name} (更新日: {modified_time.strftime("%Y-%m-%d")})')

        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        with open(file_path, 'wb') as f:
            f.write(fh.read())

        print(f'✓ 完了: {file_name}')
        downloaded_count += 1

    print(f'\n✓ {downloaded_count}個のファイルをダウンロードしました')
    return downloaded_count

if __name__ == '__main__':
    try:
        service = authenticate()
        download_search_console_history(service, FOLDER_ID, OUTPUT_DIR, months=3)
    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()
        exit(1)
