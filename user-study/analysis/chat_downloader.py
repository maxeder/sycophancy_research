import firebase_admin
from firebase_admin import credentials, storage
import os


cred = credentials.Certificate('firebasekey.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'sycllm.firebasestorage.app'
})

bucket = storage.bucket()

def download_all_json(folder_path, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    blobs = bucket.list_blobs(prefix=folder_path)

    for blob in blobs:
        if blob.name.endswith('.json'):
            dest = os.path.join(dest_dir, os.path.basename(blob.name))
            blob.download_to_filename(dest)
            print(f'Downloaded: {blob.name} → {dest}')

download_all_json('chats/', './chats')