import os
import sys
import json
import time
import shutil
import zipfile
import tarfile
import platform
import tempfile
import subprocess
import threading
import sqlite3
import webbrowser
from pathlib import Path
from datetime import datetime
import urllib.request
import urllib.error

try:
    import requests
except ImportError:
    requests = None

try:
    from packaging import version as pkg_version
except ImportError:
    pkg_version = None

from db.config import DB_NAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / DB_NAME if not Path(DB_NAME).is_absolute() else Path(DB_NAME)

APP_VERSION = "1.2.0"
DEFAULT_GITHUB_REPO = "cwilliamson29/MyBook-Manager"
GITHUB_API_URL = "https://api.github.com/repos"
CONFIG_FILE = PROJECT_ROOT / ".updater_config.json"


def get_current_version():
    return APP_VERSION


def get_configured_repo():
    config = load_updater_config()
    return config.get("github_repo", DEFAULT_GITHUB_REPO)


def load_updater_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "github_repo": DEFAULT_GITHUB_REPO,
        "auto_check_on_startup": True,
        "last_check_timestamp": None,
        "ignored_versions": []
    }


def save_updater_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving updater config: {e}")


def parse_version_string(ver_str):
    if not ver_str:
        return (0, 0, 0)
    clean = str(ver_str).strip()
    if clean.lower().startswith("v"):
        clean = clean[1:].strip()

    if pkg_version is not None:
        try:
            return pkg_version.parse(clean)
        except Exception:
            pass

    # Fallback manual tuple parser
    parts = []
    # Strip any suffix like -beta, -alpha for base tuple comparison
    main_part = clean.split("-")[0].split("+")[0]
    for seg in main_part.split("."):
        try:
            parts.append(int(seg))
        except ValueError:
            # Extract digits from segment
            digits = "".join(ch for ch in seg if ch.isdigit())
            parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_version_newer(latest_ver_str, current_ver_str=APP_VERSION):
    try:
        latest = parse_version_string(latest_ver_str)
        current = parse_version_string(current_ver_str)
        return latest > current
    except Exception:
        # String fallback if parse fails
        return str(latest_ver_str).strip().lstrip("vV") != str(current_ver_str).strip().lstrip("vV")


def get_platform_info():
    sys_name = platform.system()  # 'Windows', 'Darwin' (macOS), 'Linux'
    arch = platform.machine()
    is_frozen = getattr(sys, "frozen", False)
    return {
        "system": sys_name,
        "os_name": "macOS" if sys_name == "Darwin" else sys_name,
        "arch": arch,
        "is_frozen": is_frozen,
        "executable": sys.executable,
        "project_root": str(PROJECT_ROOT)
    }


def check_for_updates(repo=None, current_version=APP_VERSION, timeout=12):
    if not repo:
        repo = get_configured_repo()

    url = f"{GITHUB_API_URL}/{repo}/releases/latest"
    headers = {
        "User-Agent": f"MyBookManager-AutoUpdater/{current_version} ({platform.system()}; {platform.machine()})",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        if requests is not None:
            response = requests.get(url, headers=headers, timeout=timeout)
            status_code = response.status_code
            if status_code == 404:
                # No formal release found; try list of releases or tags
                list_url = f"{GITHUB_API_URL}/{repo}/releases"
                list_resp = requests.get(list_url, headers=headers, timeout=timeout)
                if list_resp.status_code == 200 and list_resp.json():
                    data = list_resp.json()[0]
                else:
                    return {
                        "success": True,
                        "update_available": False,
                        "message": "No releases found on GitHub repository.",
                        "current_version": current_version,
                        "latest_version": current_version,
                        "repo": repo
                    }
            elif status_code == 403:
                return {
                    "success": False,
                    "error": "GitHub API rate limit reached. Please try again in a few minutes.",
                    "rate_limited": True,
                    "current_version": current_version,
                    "repo": repo
                }
            elif status_code != 200:
                return {
                    "success": False,
                    "error": f"GitHub returned HTTP {status_code}: {response.text[:200]}",
                    "current_version": current_version,
                    "repo": repo
                }
            else:
                data = response.json()
        else:
            # Fallback to urllib
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return {
                        "success": True,
                        "update_available": False,
                        "message": "No releases found on GitHub repository.",
                        "current_version": current_version,
                        "latest_version": current_version,
                        "repo": repo
                    }
                elif e.code == 403:
                    return {
                        "success": False,
                        "error": "GitHub API rate limit reached. Please try again in a few minutes.",
                        "rate_limited": True,
                        "current_version": current_version,
                        "repo": repo
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP Error {e.code}: {e.reason}",
                        "current_version": current_version,
                        "repo": repo
                    }

        # Update last check timestamp
        config = load_updater_config()
        config["last_check_timestamp"] = datetime.now().isoformat()
        save_updater_config(config)

        tag_name = data.get("tag_name", "").strip()
        version_num = tag_name.lstrip("vV").strip() if tag_name else "0.0.0"
        release_name = data.get("name") or tag_name or f"Release {version_num}"
        body = data.get("body", "") or "No release notes provided."
        published_at = data.get("published_at", "")
        html_url = data.get("html_url", f"https://github.com/{repo}/releases")
        assets = data.get("assets", [])
        zipball_url = data.get("zipball_url", "")
        tarball_url = data.get("tarball_url", "")

        is_newer = is_version_newer(version_num, current_version)
        matched_asset = find_best_platform_asset(assets, zipball_url)

        return {
            "success": True,
            "update_available": is_newer,
            "current_version": current_version,
            "latest_version": version_num,
            "tag_name": tag_name,
            "release_name": release_name,
            "release_notes": body,
            "published_at": published_at,
            "html_url": html_url,
            "assets": assets,
            "zipball_url": zipball_url,
            "tarball_url": tarball_url,
            "target_asset": matched_asset,
            "repo": repo
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check for updates: {str(e)}",
            "current_version": current_version,
            "repo": repo
        }


def find_best_platform_asset(assets, fallback_zipball=None):
    plat = get_platform_info()
    sys_name = plat["system"].lower()  # 'windows', 'darwin', 'linux'
    is_frozen = plat["is_frozen"]

    target_asset = None

    if is_frozen:
        # Look for binary release asset matching the OS
        for asset in assets:
            name = asset.get("name", "").lower()
            if sys_name == "windows":
                if name.endswith(".exe") or name.endswith(".msi") or ("win" in name and name.endswith(".zip")):
                    target_asset = {
                        "name": asset.get("name"),
                        "download_url": asset.get("browser_download_url"),
                        "size": asset.get("size", 0),
                        "type": "binary_windows"
                    }
                    break
            elif sys_name == "darwin":
                if name.endswith(".dmg") or name.endswith(".pkg") or (("mac" in name or "darwin" in name or "osx" in name) and (name.endswith(".zip") or name.endswith(".tar.gz"))):
                    target_asset = {
                        "name": asset.get("name"),
                        "download_url": asset.get("browser_download_url"),
                        "size": asset.get("size", 0),
                        "type": "binary_macos"
                    }
                    break
            elif sys_name == "linux":
                if name.endswith(".appimage") or name.endswith(".deb") or name.endswith(".rpm") or (("linux" in name) and (name.endswith(".tar.gz") or name.endswith(".zip"))):
                    target_asset = {
                        "name": asset.get("name"),
                        "download_url": asset.get("browser_download_url"),
                        "size": asset.get("size", 0),
                        "type": "binary_linux"
                    }
                    break

    # If no frozen asset matched, or running in source mode: look for project zip asset or use fallback_zipball
    if not target_asset:
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".zip") and not any(k in name for k in ["win", "mac", "linux", "darwin"]):
                target_asset = {
                    "name": asset.get("name"),
                    "download_url": asset.get("browser_download_url"),
                    "size": asset.get("size", 0),
                    "type": "source_archive"
                }
                break

    if not target_asset and fallback_zipball:
        target_asset = {
            "name": "source_code.zip",
            "download_url": fallback_zipball,
            "size": 0,
            "type": "source_archive"
        }

    return target_asset


def download_update_package(download_url, dest_path, progress_callback=None, cancel_check=None):
    headers = {
        "User-Agent": f"MyBookManager-AutoUpdater/{APP_VERSION}"
    }

    if requests is not None:
        response = requests.get(download_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        start_time = time.time()

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                if cancel_check and cancel_check():
                    return False

                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback:
                        elapsed = time.time() - start_time
                        speed = (downloaded / elapsed) if elapsed > 0 else 0
                        percent = (downloaded / total_size) if total_size > 0 else 0.0
                        progress_callback(downloaded, total_size, percent, speed)

        return True
    else:
        req = urllib.request.Request(download_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            start_time = time.time()

            with open(dest_path, "wb") as f:
                while True:
                    if cancel_check and cancel_check():
                        return False
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        elapsed = time.time() - start_time
                        speed = (downloaded / elapsed) if elapsed > 0 else 0
                        percent = (downloaded / total_size) if total_size > 0 else 0.0
                        progress_callback(downloaded, total_size, percent, speed)
        return True


def create_safety_database_backup():
    try:
        if not DB_PATH.exists():
            return None
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"pre_update_backup_{timestamp}.db"
        backup_path = PROJECT_ROOT / backup_filename

        with sqlite3.connect(DB_PATH) as src_conn:
            with sqlite3.connect(backup_path) as dst_conn:
                src_conn.backup(dst_conn)
        return str(backup_path)
    except Exception as e:
        print(f"Safety backup failed: {e}")
        return None


def apply_update(archive_path, release_info, status_callback=None):
    if status_callback:
        status_callback("Creating database safety snapshot...")

    safety_backup = create_safety_database_backup()

    plat = get_platform_info()
    is_frozen = plat["is_frozen"]
    sys_name = plat["system"]

    if status_callback:
        status_callback("Extracting update package...")

    temp_extract_dir = tempfile.mkdtemp(prefix="mybook_update_")

    try:
        # Determine format and extract
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(temp_extract_dir)
        elif tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, "r:*") as tf:
                tf.extractall(temp_extract_dir)
        else:
            # Standalone binary file replacement for frozen apps
            if is_frozen:
                return _apply_frozen_binary_update(archive_path, status_callback)
            else:
                raise ValueError("Downloaded file is not a supported zip/tar archive.")

        # Find the root folder inside the extracted contents
        extracted_items = list(Path(temp_extract_dir).iterdir())
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            source_root = extracted_items[0]
        else:
            source_root = Path(temp_extract_dir)

        if not is_frozen:
            # Source / Python script update
            if status_callback:
                status_callback("Installing updated application files...")

            _install_source_files(source_root, PROJECT_ROOT)

            # Clean up
            shutil.rmtree(temp_extract_dir, ignore_errors=True)

            return {
                "success": True,
                "safety_backup": safety_backup,
                "restart_required": True,
                "message": f"Successfully updated MyBook Manager to version {release_info.get('latest_version')}!"
            }
        else:
            # Frozen app update
            return _apply_frozen_app_update(source_root, status_callback)

    except Exception as e:
        shutil.rmtree(temp_extract_dir, ignore_errors=True)
        return {
            "success": False,
            "error": f"Failed to apply update: {str(e)}",
            "safety_backup": safety_backup
        }


def _install_source_files(source_dir: Path, target_dir: Path):
    PROTECTED_FILES = {
        "books.db",
        DB_NAME,
        ".updater_config.json"
    }

    PROTECTED_DIRS = {
        ".git",
        "myenv",
        "venv",
        ".venv",
        "env",
        "__pycache__"
    }

    for src_path in source_dir.rglob("*"):
        rel_path = src_path.relative_to(source_dir)

        # Check if any parent or self is protected directory
        parts = rel_path.parts
        if any(p in PROTECTED_DIRS for p in parts):
            continue

        dest_path = target_dir / rel_path

        # Protect databases and backups
        if dest_path.name in PROTECTED_FILES or dest_path.name.endswith(".db"):
            if dest_path.exists():
                continue

        if src_path.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)


def _apply_frozen_binary_update(new_binary_path, status_callback=None):
    sys_name = platform.system()
    current_exe = Path(sys.executable)

    if sys_name == "Windows":
        # On Windows, running exe is locked. We write a batch script that waits for current process to exit, replaces exe, and relaunches.
        updater_bat = current_exe.parent / "update_runner.bat"
        pid = os.getpid()
        bat_content = f"""@echo off
timeout /t 2 /nobreak >nul
:loop
tasklist /fi "PID eq {pid}" 2>nul | find "{pid}" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto loop
)
copy /y "{new_binary_path}" "{current_exe}"
del "{new_binary_path}"
start "" "{current_exe}"
del "%~f0"
"""
        with open(updater_bat, "w", encoding="utf-8") as f:
            f.write(bat_content)

        return {
            "success": True,
            "restart_required": True,
            "deferred_command": ["cmd.exe", "/c", str(updater_bat)],
            "message": "Update prepared. The application will restart to complete installation."
        }
    else:
        # macOS / Linux
        staged_path = current_exe.with_suffix(".new")
        shutil.copy2(new_binary_path, staged_path)
        os.chmod(staged_path, 0o755)
        # Atomic rename or replacement
        os.replace(staged_path, current_exe)
        return {
            "success": True,
            "restart_required": True,
            "message": "Update installed. Ready to restart application."
        }


def _apply_frozen_app_update(extracted_source_root: Path, status_callback=None):
    sys_name = platform.system()
    current_exe = Path(sys.executable)

    if sys_name == "Windows":
        updater_bat = current_exe.parent / "update_runner.bat"
        pid = os.getpid()
        bat_content = f"""@echo off
timeout /t 2 /nobreak >nul
:loop
tasklist /fi "PID eq {pid}" 2>nul | find "{pid}" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto loop
)
xcopy /s /e /y "{extracted_source_root}\\*" "{current_exe.parent}\\"
start "" "{current_exe}"
del "%~f0"
"""
        with open(updater_bat, "w", encoding="utf-8") as f:
            f.write(bat_content)

        return {
            "success": True,
            "restart_required": True,
            "deferred_command": ["cmd.exe", "/c", str(updater_bat)],
            "message": "Update staged. Application will restart to finish installation."
        }
    else:
        # macOS / Linux
        _install_source_files(extracted_source_root, current_exe.parent)
        return {
            "success": True,
            "restart_required": True,
            "message": "Update installed successfully."
        }


def restart_application(deferred_command=None):
    if deferred_command:
        if platform.system() == "Windows":
            subprocess.Popen(deferred_command, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if hasattr(subprocess, "DETACHED_PROCESS") else 0)
        else:
            subprocess.Popen(deferred_command)
        sys.exit(0)

    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        subprocess.Popen([sys.executable] + sys.argv[1:])
        sys.exit(0)
    else:
        main_script = PROJECT_ROOT / "main.py"
        args = [sys.executable, str(main_script)] + sys.argv[1:]
        if platform.system() == "Windows":
            subprocess.Popen(args)
        else:
            try:
                os.execv(sys.executable, args)
            except Exception:
                subprocess.Popen(args)
        sys.exit(0)


def open_release_page(url=None):
    target = url or f"https://github.com/{get_configured_repo()}/releases"
    try:
        webbrowser.open(target)
    except Exception as e:
        print(f"Error opening browser: {e}")
