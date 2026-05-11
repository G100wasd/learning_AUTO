"""
Edge Driver 自动更新工具
检测当前 Edge 浏览器版本，自动下载匹配的 msedgedriver.exe
"""

import os
import re
import sys
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



# ============================================================
# 驱动下载
# ============================================================

CDN_URLS = [
    "https://msedgedriver.microsoft.com/{version}/edgedriver_win64.zip",
    "https://msedgedriver.azureedge.net/{version}/edgedriver_win64.zip",
]


def find_driver_version(edge_ver: str) -> str | None:
    """用二分试探法找到可用的驱动版本（优先精确匹配，失败则逐级降版本）。"""
    parts = list(map(int, edge_ver.split(".")))
    # 从当前版本开始向下试探，最多降 10 个 patch 号
    for patch_delta in range(11):
        if patch_delta == 0:
            candidate = parts
        else:
            candidate = parts[:3] + [max(parts[3] - patch_delta, 0)]
        ver = ".".join(map(str, candidate))
        for cdn_url in CDN_URLS:
            url = cdn_url.format(version=ver)
            try:
                req = urllib.request.Request(url, method="HEAD")
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=10):
                    pass
                print(f"    可用: Driver v{ver}")
                return ver
            except Exception:
                continue
    return None


def download_driver(version: str, target_path: Path) -> bool:
    """遍历 CDN 源下载指定版本的 edgedriver_win64.zip 并解压到目标路径。"""
    for cdn_url in CDN_URLS:
        zip_url = cdn_url.format(version=version)
        print(f"    尝试: {zip_url}")

        req = urllib.request.Request(zip_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        try:
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=60) as r:
                data = r.read()
        except Exception:
            print(f"     -> 不可用")
            continue

        # 下载成功，解压替换
        tmp_dir = Path(tempfile.mkdtemp())
        zip_path = tmp_dir / "edgedriver_win64.zip"
        try:
            zip_path.write_bytes(data)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extract("msedgedriver.exe", tmp_dir)
            src = tmp_dir / "msedgedriver.exe"
            shutil.move(str(src), str(target_path))
            print(f"    OK: 已更新 -> {target_path}")
            return True
        except Exception as e:
            print(f"    [!] 解压/替换失败: {e}")
            return False
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    print("    [!] 所有 CDN 均不可用")
    return False


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

    # 判断是否需要更新（主版本号相同且已有驱动则跳过）
    if driver_ver and driver_ver.split(".")[0] == edge_ver.split(".")[0]:
        print("\n  [OK] 驱动版本已匹配，无需更新")
        return

    print(f"\n  需要更新: Edge v{edge_ver}  vs  Driver v{driver_ver or 'N/A'}")

    # 3. 查找匹配版本
    print("\n[3/4] 查找匹配的驱动版本…")
    target_ver = find_driver_version(edge_ver)
    if not target_ver:
        print(f"  [!] 无法找到 Edge v{edge_ver} 对应的驱动版本")
        print("  请手动下载: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        return
    print(f"  Edge v{edge_ver} -> Driver v{target_ver}")

    # 4. 下载并替换
    print(f"\n[4/4] 下载 Driver v{target_ver}...")
    if download_driver(target_ver, DRIVER_PATH):
        # 验证新驱动
        new_ver = get_driver_version()
        print(f"\n  [OK] 更新完成: Driver v{new_ver}")
    else:
        print("\n  [!] 更新失败，请手动下载:")
        print(f"  {CDN_URLS[0].format(version=target_ver)}")

    input("\n按 Enter 键退出...")


if __name__ == "__main__":
    main()
