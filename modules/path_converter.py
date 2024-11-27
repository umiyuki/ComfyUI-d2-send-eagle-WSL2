import subprocess
import os
import platform

def convert_wsl_path_to_windows(linux_path):
    """
    WSL2のLinuxパスをWindowsパスに変換する
    """
    try:
        # WSLかどうかチェック
        is_wsl = False
        if platform.system() == "Linux":
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    is_wsl = True

        if not is_wsl:
            return linux_path

        # wslpathコマンドを使ってパスを変換
        result = subprocess.run(
            ['wslpath', '-w', linux_path],
            capture_output=True,
            text=True,
            check=True
        )
        windows_path = result.stdout.strip()
        return windows_path
    except Exception as e:
        print(f"Path conversion error: {str(e)}")
        return linux_path  # 変換に失敗した場合は元のパスを返す