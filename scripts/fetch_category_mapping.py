import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
import csv

# Google Sheets設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1Lin1EJSuwgkNfPrEMBydTFTvXeGBpLrT'
SHEET_GID = '1134122120'

# 出力先
OUTPUT_FILE = './data/category_mapping.csv'

def authenticate_sheets():
    """Google Sheets APIの認証"""
    creds = None

    # token_sheets.pickleファイルがあれば読み込む
    if os.path.exists('token_sheets.pickle'):
        with open('token_sheets.pickle', 'rb') as token:
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
        with open('token_sheets.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('sheets', 'v4', credentials=creds)

def get_sheet_name_from_gid(service, spreadsheet_id, gid):
    """GIDからシート名を取得"""
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    for sheet in spreadsheet.get('sheets', []):
        properties = sheet.get('properties', {})
        if str(properties.get('sheetId')) == gid:
            return properties.get('title')

    return None

def fetch_category_mapping(service, spreadsheet_id, gid):
    """スプレッドシートからカテゴリマッピングを取得"""

    # GIDからシート名を取得
    sheet_name = get_sheet_name_from_gid(service, spreadsheet_id, gid)

    if not sheet_name:
        print(f"エラー: GID {gid} に対応するシートが見つかりません")
        return []

    print(f"シート名: {sheet_name}")

    # シートのデータを取得
    range_name = f"'{sheet_name}'!A:Z"  # A列からZ列まで取得
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    if not values:
        print('データが見つかりません')
        return []

    print(f'{len(values)}行のデータを取得しました')
    print(f'ヘッダー: {values[0]}')
    print(f'サンプル（最初の5行）:')
    for i, row in enumerate(values[1:6], 1):
        print(f'{i}. {row}')

    return values

def save_mapping_to_csv(data, output_file):
    """マッピングデータをCSVに保存"""
    if not data:
        print('保存するデータがありません')
        return

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

    print(f'\nマッピングデータを保存しました: {output_file}')

if __name__ == '__main__':
    try:
        service = authenticate_sheets()
        mapping_data = fetch_category_mapping(service, SPREADSHEET_ID, SHEET_GID)

        if mapping_data:
            save_mapping_to_csv(mapping_data, OUTPUT_FILE)
            print('\n✓ カテゴリマッピングの取得完了')
    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()
        exit(1)
