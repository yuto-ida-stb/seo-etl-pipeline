import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import pandas as pd

# Google Drive設定
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FILE_ID = '1Lin1EJSuwgkNfPrEMBydTFTvXeGBpLrT'
OUTPUT_FILE = './data/category_mapping.csv'

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

def download_as_csv(service, file_id, output_file):
    """Excelファイルをダウンロードして特定シートをCSVに変換"""
    try:
        # ファイルのメタデータを取得
        file_metadata = service.files().get(fileId=file_id, fields='name,mimeType').execute()
        print(f"ファイル名: {file_metadata['name']}")
        print(f"MIMEタイプ: {file_metadata['mimeType']}")

        # Excelファイルとしてダウンロード
        request = service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f'ダウンロード進捗: {int(status.progress() * 100)}%')

        fh.seek(0)

        # pandasでExcelファイルを読み込み
        print("\nExcelファイルを解析中...")

        # 全シートを取得
        excel_file = pd.ExcelFile(fh)
        print(f"シート一覧: {excel_file.sheet_names}")

        # GID 1134122120 に対応するシートを探す（通常は2番目以降のシート）
        # とりあえず最初のシートを読み込む
        df = pd.read_excel(fh, sheet_name=0)

        print(f"\n読み込んだデータ:")
        print(f"行数: {len(df)}")
        print(f"列数: {len(df.columns)}")
        print(f"\n最初の5行:")
        print(df.head())

        # CSVに保存
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"\n✓ CSVファイルを保存しました: {output_file}")
        return True

    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        service = authenticate()
        success = download_as_csv(service, FILE_ID, OUTPUT_FILE)

        if success:
            print('\n✓ カテゴリマッピングのダウンロード完了')
        else:
            print('\n✗ ダウンロードに失敗しました')
            exit(1)

    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()
        exit(1)
