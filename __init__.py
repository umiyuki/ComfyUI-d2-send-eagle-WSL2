"""
@author: da2el
@title: D2 Send Eagle
@description: Send images to Eagle, an image management application
"""

# from .send_eagle import SendEagle
from .D2_SendEagle import D2_SendEagle
from .D2_SendVideoEagle import D2_SendVideoEagle

WEB_DIRECTORY = "./web"

NODE_CLASS_MAPPINGS = {
    "D2 Send Eagle": D2_SendEagle,
    "D2 Send Video Eagle": D2_SendVideoEagle,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "D2 Send Eagle": "D2 Send Eagle",
    "D2 Send Video Eagle": "D2 Send Video Eagle",
}


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
