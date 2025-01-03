import socket
import platform
from os import name
from typing import Dict, Optional, TypedDict, Union, List
import requests
from .path_converter import convert_wsl_path_to_windows

class FolderInfo(TypedDict):
    id: str
    name: str

def get_windows_host():
    """
    Get the appropriate hostname to access Windows host from WSL2
    Returns localhost for Windows, host.docker.internal for WSL2
    """
    if platform.system() == "Windows":
        return "localhost"
    
    # Check if running in WSL
    try:
        with open('/proc/version', 'r') as f:
            if 'microsoft' in f.read().lower():
                return "host.docker.internal"
    except:
        pass
    
    return "localhost"  # fallback

class EagleAPI:
    def __init__(self, base_url=None):
        """
        Initialize Eagle API client
        base_url: Optional override for the Eagle API endpoint
        """
        windows_host = get_windows_host()
        self.base_url = base_url or f"http://{windows_host}:41595"
        self.folder_list: Optional[List[FolderInfo]] = None
        
        # Test connection on initialization
        try:
            self._send_request("/api/application/info")
        except requests.RequestException as e:
            print(f"Warning: Could not connect to Eagle API at {self.base_url}")
            print(f"Error details: {str(e)}")
            print("Make sure Eagle is running and the port is correct")

    def add_item_from_path(self, data, folder_id=None):
        """
        画像をEagleに送信
        WSL2環境の場合はパスを変換
        """
        if "path" in data:
            # LinuxパスをWindowsパスに変換
            data["path"] = convert_wsl_path_to_windows(data["path"])
            
        if folder_id:
            data["folderId"] = folder_id
            
        return self._send_request("/api/item/addFromPath", method="POST", data=data)


    # #########################################
    # フォルダ名 or ID で該当フォルダを探してIDを返す
    # 存在しなければ作成してIDを返す
    def find_or_create_folder(self, name_or_id:str) -> str:
        folder = self._find_folder(name_or_id)

        if folder:
            return folder.get("id", "")
        return self._create_folder(name_or_id)


    # #########################################
    # フォルダ名 or ID で該当フォルダを取得
    # 存在しないなら None を返す
    def _find_folder(self, name_or_id:str) -> Optional[FolderInfo]:
        self._ensure_folder_list()

        if(self.folder_list is not None):
            # 名前とIDの両方で検索
            for folder in self.folder_list:
                if folder["name"] == name_or_id or folder["id"] == name_or_id:
                    return folder

        return None


    # #########################################
    # フォルダを作成
    # 作成できない or 名前指定がなければ "" を返す
    def _create_folder(self, name:str) -> str:
        if(not name):
            return ""

        try:
            data = {"folderName": name}
            response = self._send_request("/api/folder/create", method="POST", data=data)
            new_folder_id = response.get("data", {}).get("id", "")

           # フォルダリストを更新
            if new_folder_id and self.folder_list is not None:
                self.folder_list.append({"id": new_folder_id, "name": name})

            return new_folder_id

        except requests.RequestException:
            return ""


    # #########################################
    # Eagle のフォルダID、名前の一覧を取得
    def _ensure_folder_list(self):
        if self.folder_list is None:
            self._get_all_folder_list()

    def _get_all_folder_list(self):
        try:
            json = self._send_request("/api/folder/list")
            self.folder_list = self._extract_id_name_pairs(json["data"])
        except requests.RequestException:
            self.folder_list = []


    # #########################################
    # Private method for sending requests
    def _send_request(self, endpoint, method="GET", data=None):
        url = self.base_url + endpoint
        headers = {"Content-Type": "application/json"}

        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"Eagle request failed: {e}")
            raise


    # #########################################
    # フォルダリストを作成
    def _extract_id_name_pairs(self, data):
        result = []

        def recursive_extract(item):
            if isinstance(item, dict):
                if 'id' in item and 'name' in item:
                    result.append({'id': item['id'], 'name': item['name']})
                if 'children' in item and isinstance(item['children'], list):
                    for child in item['children']:
                        recursive_extract(child)
            elif isinstance(item, list):
                for element in item:
                    recursive_extract(element)

        recursive_extract(data)
        return result
