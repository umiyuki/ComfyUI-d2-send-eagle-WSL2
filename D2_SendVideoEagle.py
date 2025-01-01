import json
import os
from typing import Dict, Optional
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from .modules.util import util
from .modules.eagle_api import EagleAPI
from .modules.params_extractor import ParamsExtractor

class D2_SendVideoEagle:
    def __init__(self):
        self.type = "output"
        self.eagle_api = EagleAPI()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": ""}),
                # ポジティブプロンプト
                "positive": (
                    "STRING",
                    {"forceInput": True, "multiline": True},
                ),
                # ネガティブプロンプト
                "negative": (
                    "STRING",
                    {"forceInput": True, "multiline": True},
                ),
                # プロンプトやモデルをEagleタグに保存するか
                "save_tags": ([
                    "None",
                    "Prompt + Checkpoint",
                    "Prompt",
                    "Checkpoint",
                ],),
                # メタデータPNGも送信するか
                "send_metadata_png": (
                    "BOOLEAN",
                    {"default": True, "label_on": "Send", "label_off": "Skip"},
                ),
                # Eagleフォルダ
                "eagle_folder": (
                    "STRING",
                    {"default": ""}
                ),
            },
            "optional": {
                # その他メモ
                "memo_text": (
                    "STRING",
                    {"multiline": True},
                ),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("positive", "negative",)
    FUNCTION = "add_video"
    OUTPUT_NODE = True
    CATEGORY = "D2"

    def add_video(
        self,
        video_path: str,
        save_tags = "None",
        send_metadata_png = True,
        eagle_folder = "",
        positive = "",
        negative = "",
        memo_text = "",
        prompt: Optional[Dict] = None,
        extra_pnginfo: Optional[Dict] = None,
    ):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # パラメータを整理
        params = ParamsExtractor({
            "positive": positive,
            "negative": negative,
            "prompt": prompt,
            "extra_pnginfo": extra_pnginfo
        })

        # 情報を整形
        formatted_info = params.format_info(memo_text)

        # Eagleフォルダが指定されているならフォルダIDを取得
        folder_id = self.eagle_api.find_or_create_folder(eagle_folder)

        # タグのリストを作成
        tags = self._get_tags(save_tags, positive, params)

        # 動画ファイルを送信
        self._send_video_to_eagle(video_path, formatted_info, tags, folder_id)

        # メタデータPNGファイルを送信
        if send_metadata_png:
            self._send_metadata_png_to_eagle(video_path, formatted_info, tags, folder_id)

        return {"result": (positive, negative,)}

    def _get_tags(self, save_tags, positive, params):
        """タグリストを生成"""
        if save_tags == "Prompt + Checkpoint":
            return [*util.get_prompt_tags(positive), params.gen_info["model_name"]]
        elif save_tags == "Prompt":
            return util.get_prompt_tags(positive)
        elif save_tags == "Checkpoint":
            return [params.gen_info["model_name"]]
        return []

    def _send_video_to_eagle(self, video_path, formatted_info, tags, folder_id):
        """動画ファイルをEagleに送信"""
        file_name = os.path.basename(video_path)
        item = {
            "path": video_path,
            "name": file_name,
            "annotation": formatted_info,
            "tags": tags,
        }
        self.eagle_api.add_item_from_path(data=item, folder_id=folder_id)

    def _send_metadata_png_to_eagle(self, video_path, formatted_info, tags, folder_id):
        """メタデータPNGファイルをEagleに送信"""
        # 動画ファイルと同じ名前のPNGファイルを探す
        png_path = os.path.splitext(video_path)[0] + '.png'
        
        if not os.path.exists(png_path):
            print(f"Metadata PNG not found: {png_path}")
            return

        # PNGファイルを送信
        item = {
            "path": png_path,
            "name": os.path.basename(png_path),
            "annotation": formatted_info + "\n[Metadata PNG for " + os.path.basename(video_path) + "]",
            "tags": [*tags, "metadata_png"],  # メタデータPNG用のタグを追加
        }
        self.eagle_api.add_item_from_path(data=item, folder_id=folder_id)