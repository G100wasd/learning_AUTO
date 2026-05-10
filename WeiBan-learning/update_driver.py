"""
Edge Driver 自动更新工具
检测当前 Edge 浏览器版本，自动下载匹配的 msedgedriver.exe
"""

import os
import re
import sys
import json
import zipfile
import shutil
import subprocess
import tempfile
import urllib.request
import ssl
from pathlib import Path

# === 配置 ===
BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
DRIVER_PATH = BASE_DIR / "msedgedriver.exe"

# Edge 浏览器安装目录（x64 系统）
EDGE_DIRS = [
    Path("C:/Program Files (x86)/Microsoft/Edge/Application"),
    Path("C:/Program Files/Microsoft/Edge/Application"),
]

# 下载源（微软官方 CDN）
DOWNLOAD_BASE = "https://msedgedriver.microsoft.com"

# 跳过 SSL 验证（公司网络常见问题）
SSL_CTX = ssl._create_unverified_context()


# ============================================================
# 版本检测
# ============================================================

def get_edge_version() -> str | None:
    """读取已安装 Edge 浏览器的完整版本号。"""
    for edge_dir in EDGE_DIRS:
        if not edge_dir.is_dir():
            continue
        # 找到版本号格式的子目录（如 147.0.3912.86）
        versions = []
        for entry in edge_dir.iterdir():
            if entry.is_dir() and re.match(r"\d+\.\d+\.\d+\.\d+$", entry.name):
                versions.append(entry.name)
        if versions:
            # 取最新版本
            versions.sort(key=lambda v: tuple(map(int, v.split("."))))
            latest = versions[-1]
            return latest
    return None


def get_driver_version() -> str | None:
    """读取当前 msedgedriver.exe 的版本号。"""
    if not DRIVER_PATH.is_file():
        return None
    try:
        result = subprocess.run(
            [str(DRIVER_PATH), "--version"],
            capture_output=True, text=True, timeout=10
        )
        # 输出示例: "Microsoft Edge WebDriver 145.0.3800.97 (xxx)"
        m = re.search(r"(\d+\.\d+\.\d+\.\d+)", result.stdout)
        return m.group(1) if m else None
    except Exception:
        return None


def normalize_major(version: str) -> str:
    """提取主版本号（如 147.0.3912.86 → 147）"""
    return version.split(".")[0]


# ============================================================
# 驱动下载
# ============================================================

def fetch_available_versions() -> list[str]:
    """从 Edge WebDriver 官方页面抓取所有可用的驱动版本号（去重、降序）。"""
    url = "https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [!] 无法访问下载页面: {e}")
        return []

    # 页面中的下载链接格式:
    # https://msedgedriver.microsoft.com/147.0.3912.98/edgedriver_win64.zip
    versions = set()
    for m in re.finditer(
        r"https://msedgedriver\.microsoft\.com/(\d+\.\d+\.\d+\.\d+)/edgedriver_win64\.zip",
        html,
    ):
        versions.add(m.group(1))
    if not versions:
        print("  [!] 页面中未找到驱动下载链接（页面结构可能已变更）")
        return []
    return sorted(versions, key=lambda v: tuple(map(int, v.split("."))), reverse=True)


def download_driver(version: str, target_path: Path) -> bool:
    """下载指定版本的 edgedriver_win64.zip 并解压到目标路径。"""
    zip_url = f"{DOWNLOAD_BASE}/{version}/edgedriver_win64.zip"
    print(f"    下载: {zip_url}")

    req = urllib.request.Request(zip_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=60) as r:
            data = r.read()
    except Exception as e:
        print(f"    [!] 下载失败: {e}")
        return False

    # 保存到临时 zip 并解压
    tmp_dir = Path(tempfile.mkdtemp())
    zip_path = tmp_dir / "edgedriver_win64.zip"
    try:
        zip_path.write_bytes(data)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extract("msedgedriver.exe", tmp_dir)
        # 替换目标文件
        src = tmp_dir / "msedgedriver.exe"
        shutil.move(str(src), str(target_path))
        print(f"    OK: 已更新 -> {target_path}")
        return True
    except Exception as e:
        print(f"    [!] 解压/替换失败: {e}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ============================================================
# 主流程
# ============================================================

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("                                              ...                                               ")
    print("                                        .:::::+X$XXX.                                            ")
    print("                                        .:;...;X$$$$.                                            ")
    print("                         ..;;.          .::...;X$$$$..         .x$x:.                            ")
    print("                      .::....::. ...::;;:::...+X$$$$$$Xx+;:.  .x$X$$$X;.                        ")
    print("                   .:::.......:;:::...........+X$$$XXXXX$$$XXxX$XXXX$$$$x:                      ")
    print("                   .;;.........:............+;;;;X$$$$$$XXXXXX$XXX$$$$$$$x                      ")
    print("                    .;;.....:...............+;;;;X$$$$$$$$XXXXXX$$$$$$$&x.                      ")
    print("                    .:;:...:;;;+:...:::;;;;+;;;;;+xxXX$$$$$$$Xx+X$$$$$&X:.                      ")
    print("                  .::.....;;:::;+;;;;;::::::::::::::::::;+xX$+;;;;+$$$$$$x.                     ")
    print("                 :;:......:+::::::::::::::::;;;;;::::::::::::::::;$$$$$$X$$x.                   ")
    print("         ::::...;;:......::;;:::::::;+xxx+++++x$X$$$&$Xx;::::::::X$$$$$$$$$$$;..;XXX:           ")
    print("       .;:....:::......::;;:::::;+x+;:::;+XXXXx;;++xXX$$&$Xx;::::::x$$$$$$$$$&$$$XX$X;          ")
    print("      .;:.............:;::.:.:+x+:::+$$$&$X++xx:.:.::::+xX$$$$x::::::+$$$$$$$$$$$$$$$$;         ")
    print("     .::........:;:..:;....:++;;:::xxxX&$$$+xxx:.........:;x$X$$X::::::X$$X$$$$$$$$$$$$:        ")
    print("     :::.......::..;+:....;x;::+x$$$;++$&$xxxx:............:x$$&$X:::::+X;::x$$$$$$$$$$:       ")
    print("     ..;;;:...::........:+;;X&$xX$X$++x$&$$xxxx:..............;x$$$X;:::::::::x$$$$$$$+:        ")
    print("        .;::..;+;......:+:.;$$xxX$$$xxx$&$$xxxx:...............:x$$$$x.:::::;X$$$$$$;.          ")
    print("        .;.....::+....:+:.:X$$Xx$$$$xxx$$$$xxxx:................:+$$$$X....;$$$$$$X$x.          ")
    print("       .;:......;....:x:..;$$$$xX$$xXx+xXXx++x+:................;;x$XXXx....+$$$$$$$$;          ")
    print("       ::......:;...:+:...xX$$$XxxxXxx+++++++++:........:.......;;+X$$$$+...:X$$$$$X$x.         ")
    print("      .;:.....:;+;;:+;..::$xX&$$XXxxx++x+x+++++:......:::......:+;;X$XXXx:...x$$$$$$$X:         ")
    print("  ....:;;.....:++++;+:...;$xX$&$$XxxXXxx+++XXx+:.....:::.......;+++x$$$&&++xxx$$$$$$$&+.....    ")
    print(" ::..::.:....:;++++;;....+$$XXx+xXXXxXXXXXXxxx+:.....:........:+xx+x$$$$&X;xxxX$$$$$$$$$$XXX.   ")
    print(" ::.......;+++++xx+;;:.;xx&$XXxxxxxxxxxxX$x++++:...::.....::...;xxxX$XXXXX:xxx+xxxx$$$$XXXX$.   ")
    print(" ::......:;+++++x++;;::x+x$xX$XxX$$$$Xx$$$XXXXX+;;++;;+xXX$$$$x;;xxX$$$$$$:xxxxxx++$$$$$XX$$.   ")
    print(".::......:;++++++++;;:+$X+XxXxX$$x$&x$$XxxX$$Xx++xX$$$$$$$&&&&&&x:X$&&&&&$:xxxxx+++$$$XXXX$$.   ")
    print(" ::...:::::;;;+++++;;:xX;;xxXXXx&xX&x$xxXxXxxx+:;x$$$$$$$$&&&&&&X:+$$$$$$X:+++X&&$$$$$$$$$X$.   ")
    print(" .;;;;;;:.:::::+++;;+:$X+:+XXX$$&$$&$&$XXxXXXXx::;X$$$$$$$&&&&&&x;+$XXX$$+;+++$$$$$$$$XXXXx+    ")
    print("      .::::..::;+;;:+;$xX+;XXX$$&$&&$$$XxXxxX$X$$;+X$$$$$$$$$&&&+:+$$$$$X:+++x$$$$$$$$:         ")
    print("       :;:.:...;;;;;:+X+:.:X$$Xx$&&&$$xXXxxx$$&&&X+++X&&&$$$$$$x::;XX$$$+;;;;X$$$$$$$X.         ")
    print("       .+::....:+;;;:;Xx+;;XX$X$$XXXX$XxxxxX$$&&&$++++;;++xx+;::..;$$XXx:;;;+$$$$$$$$+.         ")
    print("        :;:.....:+;;;:;+++;xXX$XXX$$$xxxxxX$$$&&$$X++++++++++;::::+$$$X:;;;;$$$$$$$&X:          ")
    print("        .;;:...:;;:;;;:;;::xxxXXX$&&&$$$XxX$$$$$$$X+x+++xXXXXxx++x$$$X:;;;;;x$$$$$$$;           ")
    print("       .;;::.:;::::::::::+::+XXx+xX$$&$$XxxX$$X+$X;;+x++xx$&&&&&&$X$+:;;;;;;::;&$$$$X;.         ")
    print("     :;:......:+:::;;::::.+;:;;;;;+XX$XXx+++++x;:::::;++xX$$$$$XX$X;:;;;;;;::+$$$$$$X$$X:       ")
    print("     .;::......:++++;+;:::::+;::::;X$$XXx+++++x;::::;:;++X&$X$$$X+::::;x$&$xx$$$$$$$$$$+        ")
    print("     ..;::..:.::::::::;+::::::++::;xXxXxxxxXx+x+::;:+;;;++$$XXX;:::::;$$$$$$$$$$$$$$&$+         ")
    print("       .+;:..:;+;::...::+;:::::::xxXXXX+xx+XxXx:.:;:;:;;+x$X;.:::::;X&$$$$$$$$$$$$$&$+.         ")
    print("        .;;;++;:;;::::::::++::::::..;xXXXXXXXX$$XX$$&$$X+;:::::::+$&$$$$$$$$$x.;xX$$;.          ")
    print("         .::.  ..;;;:::::::;::...:::::::::;;;;;;;;;;;::::::::::::+$$$$$$$$$X;.   .:..           ")
    print("                  .;++;..:;:...:+x+:.:::::::::::::::::::::;x$+::::;$$$$$$$;.                    ")
    print("                  ...+;::::++::++:;;+xx+;::::::::::::+x$&&&$$&x:+$$$XX$$;.                      ")
    print("                    .;:..::::;+;:::::::;;;;++::::x&$$$$$$$$$$$$$$$$$$$$$+.                      ")
    print("                   .::.:::.....:::::::::::::;::::x$$$$$$$$$$$$$$$$$$$$$$$+                      ")
    print("                   .;;;;::::.::+++;;;:::::::+xX$$$$$$$$X$$$$$$$$$$$$$$$$$+.                     ")
    print("                     .:+++;:::;...:;++++++;:::+$$$$$&&$$$$+:. .+$$$&&$X:.                       ")
    print("                        .:;+;:.    .   ..;;:::;X$$$$:..        .x$Xx:.                          ")
    print("                            ..          .:;:::;$$$$$.           ..                              ")
    print("                                        .:;+++x$$$$$.                                           ")
    print("                                          .........                                             ")
    print("=" * 55)
    print("Edge Driver 自动更新工具")
    print("=" * 55)

    # 1. 检测 Edge 浏览器版本
    print("\n[1/4] 检测 Edge 浏览器版本…")
    edge_ver = get_edge_version()
    if not edge_ver:
        print("  [!] 未找到 Edge 浏览器安装目录")
        print(f"  查找路径: {[str(d) for d in EDGE_DIRS]}")
        return
    print(f"  Edge: v{edge_ver}")

    # 2. 检测当前驱动版本
    print("\n[2/4] 检测当前 Edge Driver 版本…")
    driver_ver = get_driver_version()
    if driver_ver:
        print(f"  Driver: v{driver_ver}")
    else:
        print(f"  Driver: 未找到 ({DRIVER_PATH})")

    # 判断是否需要更新
    if driver_ver and normalize_major(driver_ver) == normalize_major(edge_ver):
        print("\n  [OK] 驱动版本已匹配，无需更新")
        return

    print(f"\n  需要更新: Edge v{edge_ver}  vs  Driver v{driver_ver or 'N/A'}")

    # 3. 查找匹配版本
    print("\n[3/4] 查找匹配的驱动版本…")
    edge_major = normalize_major(edge_ver)
    all_versions = fetch_available_versions()
    if not all_versions:
        print("  [!] 无法获取可用版本列表")
        print("  请手动下载: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        return

    # 找到与 Edge 主版本匹配的最新驱动
    matched = [v for v in all_versions if v.startswith(f"{edge_major}.")]
    if not matched:
        print(f"  [!] 未找到匹配 Edge v{edge_major}.x 的驱动")
        print(f"  可用主版本: {sorted(set(normalize_major(v) for v in all_versions))}")
        return

    target_ver = matched[0]  # 已降序，取第一个即最新
    print(f"  Edge v{edge_ver} -> Driver v{target_ver}")

    # 4. 下载并替换
    print(f"\n[4/4] 下载 Driver v{target_ver}...")
    if download_driver(target_ver, DRIVER_PATH):
        # 验证新驱动
        new_ver = get_driver_version()
        print(f"\n  [OK] 更新完成: Driver v{new_ver}")
    else:
        print("\n  [!] 更新失败，请手动下载:")
        print(f"  {DOWNLOAD_BASE}/{target_ver}/edgedriver_win64.zip")

    input("\n按 Enter 键退出...")


if __name__ == "__main__":
    main()
