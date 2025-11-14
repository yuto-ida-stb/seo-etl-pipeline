#!/usr/bin/env python3
"""
プレゼンテーションファイルをGoogle Driveにアップロードし、Google Slidesとして公開するスクリプト
"""
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

# Google Drive設定
SCOPES = ['https://www.googleapis.com/auth/drive.file']
PARENT_FOLDER_ID = '1sSy8mDQgtkmyODigpIiWiNh6hOJxG1Pt'
PRESENTATION_FILE = './docs/presentation.pptx'
PRESENTATION_NAME = 'スタンバイSEO 11月大阪合宿'

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
        # フォルダを作成
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = service.files().create(
            body=file_metadata,
            fields='id, name, webViewLink'
        ).execute()
        print(f'フォルダ作成: {folder_name} (ID: {folder.get("id")})')
        return folder

def upload_presentation_as_slides(service, file_path, folder_id, presentation_name):
    """プレゼンテーションファイルをGoogle Slidesとしてアップロード"""

    # 既存ファイルを検索
    query = f"name='{presentation_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields='files(id, name, webViewLink)'
    ).execute()

    existing_files = results.get('files', [])

    # ファイルのMIMEタイプを判定
    if file_path.endswith('.pptx'):
        source_mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    elif file_path.endswith('.pdf'):
        source_mime_type = 'application/pdf'
    else:
        source_mime_type = 'application/octet-stream'

    # Google Slides形式
    target_mime_type = 'application/vnd.google-apps.presentation'

    media = MediaFileUpload(file_path, mimetype=source_mime_type, resumable=True)

    try:
        if existing_files:
            # 既存ファイルを更新
            file_id = existing_files[0]['id']
            print(f'既存のGoogle Slidesを更新中: {presentation_name}')

            # 既存ファイルの内容を更新（URLは維持される）
            file = service.files().update(
                fileId=file_id,
                media_body=media,
                fields='id, name, webViewLink, mimeType'
            ).execute()
            print(f'  Google Slidesを更新しました（URLは変わりません）')
        else:
            # 新規ファイルを作成
            print(f'新しいGoogle Slidesを作成中: {presentation_name}')
            file_metadata = {
                'name': presentation_name,
                'parents': [folder_id],
                'mimeType': target_mime_type
            }
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, mimeType'
            ).execute()

        print(f'\n✓ Google Slidesとして公開しました')
        print(f'  名前: {file.get("name")}')
        print(f'  ID: {file.get("id")}')
        print(f'  リンク: {file.get("webViewLink")}')

        # 共有設定を変更（リンクを知っている人が閲覧可能に）
        set_public_permission(service, file.get("id"))

        return file
    except Exception as e:
        print(f'\nエラー: アップロード失敗 - {e}')
        return None

def set_public_permission(service, file_id):
    """ファイルをリンク共有可能に設定"""
    try:
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()
        print(f'  共有設定: リンクを知っている人が閲覧可能')
    except Exception as e:
        print(f'  警告: 共有設定の変更に失敗しました - {e}')

def main():
    """メイン処理"""
    print('=' * 50)
    print('プレゼンテーションをGoogle Slidesにアップロード')
    print('=' * 50)
    print()

    # プレゼンテーションファイルが存在するか確認
    if not os.path.exists(PRESENTATION_FILE):
        print(f'エラー: プレゼンテーションファイルが見つかりません: {PRESENTATION_FILE}')
        print('先に "make slides" を実行してください')
        exit(1)

    try:
        # 認証
        service = authenticate()
        print()

        # プレゼンテーション用フォルダを取得または作成
        folder_name = '03_presentations'

        # drive_folder_ids.jsonからフォルダIDを読み込む
        folder_id = None
        if os.path.exists('drive_folder_ids.json'):
            with open('drive_folder_ids.json', 'r') as f:
                folder_ids = json.load(f)
                folder_id = folder_ids.get(folder_name)

        if not folder_id:
            # フォルダを検索または作成
            folder = find_or_create_folder(service, folder_name, PARENT_FOLDER_ID)
            folder_id = folder.get('id')

            # folder_ids.jsonに保存
            if os.path.exists('drive_folder_ids.json'):
                with open('drive_folder_ids.json', 'r') as f:
                    folder_ids = json.load(f)
            else:
                folder_ids = {}

            folder_ids[folder_name] = folder_id

            with open('drive_folder_ids.json', 'w') as f:
                json.dump(folder_ids, f, indent=2)
        else:
            print(f'既存フォルダを使用: {folder_name} (ID: {folder_id})')

        print()

        # プレゼンテーションをアップロード
        result = upload_presentation_as_slides(
            service,
            PRESENTATION_FILE,
            folder_id,
            PRESENTATION_NAME
        )

        if result:
            print()
            print('=' * 50)
            print('✅ 完了！')
            print('=' * 50)
            print()
            print('Google Slidesで開くには下記リンクをクリック:')
            print(result.get("webViewLink"))
            print()
        else:
            exit(1)

    except Exception as e:
        print(f'\nエラー: {e}')
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == '__main__':
    main()
