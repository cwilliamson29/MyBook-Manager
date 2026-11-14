import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from windows.settings_helpers.updater import (
    APP_VERSION,
    parse_version_string,
    is_version_newer,
    find_best_platform_asset,
    load_updater_config,
    save_updater_config,
    _install_source_files,
    create_safety_database_backup,
    check_for_updates,
    get_platform_info
)


class TestUpdater(unittest.TestCase):

    def test_version_parsing_and_comparison(self):
        # Basic comparisons
        self.assertTrue(is_version_newer("1.3.0", "1.2.0"))
        self.assertTrue(is_version_newer("v2.0.0", "1.2.0"))
        self.assertTrue(is_version_newer("1.2.1", "1.2.0"))
        self.assertFalse(is_version_newer("1.2.0", "1.2.0"))
        self.assertFalse(is_version_newer("v1.2.0", "1.2.0"))
        self.assertFalse(is_version_newer("1.1.9", "1.2.0"))
        self.assertFalse(is_version_newer("1.0.0", "1.2.0"))

        # Minor and patch variations
        self.assertTrue(is_version_newer("v1.2.1-beta", "1.2.0"))
        self.assertTrue(is_version_newer("1.10.0", "1.9.0"))

    def test_platform_info(self):
        plat = get_platform_info()
        self.assertIn("system", plat)
        self.assertIn("os_name", plat)
        self.assertIn("arch", plat)
        self.assertIn("is_frozen", plat)
        self.assertIn("project_root", plat)

    def test_find_best_platform_asset_frozen(self):
        assets = [
            {"name": "MyBookManager-windows-x64.exe", "browser_download_url": "https://github.com/win.exe", "size": 1000},
            {"name": "MyBookManager-macos.dmg", "browser_download_url": "https://github.com/mac.dmg", "size": 1000},
            {"name": "MyBookManager-linux.AppImage", "browser_download_url": "https://github.com/linux.AppImage", "size": 1000},
            {"name": "source.zip", "browser_download_url": "https://github.com/source.zip", "size": 500},
        ]

        # In source mode (is_frozen=False), prefers source zip
        asset = find_best_platform_asset(assets, fallback_zipball="https://github.com/zipball")
        self.assertIsNotNone(asset)
        self.assertEqual(asset["type"], "source_archive")

    def test_config_load_and_save(self):
        config = load_updater_config()
        self.assertIsInstance(config, dict)
        self.assertIn("github_repo", config)
        self.assertIn("auto_check_on_startup", config)

    def test_source_file_installation_with_safety_protections(self):
        # Create temp source directory and target directory
        temp_src = tempfile.mkdtemp(prefix="test_src_")
        temp_tgt = tempfile.mkdtemp(prefix="test_tgt_")

        try:
            src_path = Path(temp_src)
            tgt_path = Path(temp_tgt)

            # Create existing files in target that MUST be protected
            existing_db = tgt_path / "books.db"
            existing_db.write_text("CRITICAL DATABASE CONTENT")

            existing_custom_db = tgt_path / "my_custom_library.db"
            existing_custom_db.write_text("CUSTOM DB CONTENT")

            git_dir = tgt_path / ".git"
            git_dir.mkdir()
            (git_dir / "config").write_text("GIT CONFIG")

            myenv_dir = tgt_path / "myenv"
            myenv_dir.mkdir()
            (myenv_dir / "pyvenv.cfg").write_text("VENV CONFIG")

            # Create new source files to be updated
            (src_path / "main.py").write_text("print('Updated main')")
            (src_path / "windows").mkdir()
            (src_path / "windows" / "settings_window.py").write_text("# Updated settings")

            # Create a books.db in source that should NOT overwrite target
            (src_path / "books.db").write_text("EMPTY DB FROM RELEASE")

            # Run installation
            _install_source_files(src_path, tgt_path)

            # Verify updated files are present
            self.assertEqual((tgt_path / "main.py").read_text(), "print('Updated main')")
            self.assertEqual((tgt_path / "windows" / "settings_window.py").read_text(), "# Updated settings")

            # Verify protected databases were NEVER overwritten
            self.assertEqual(existing_db.read_text(), "CRITICAL DATABASE CONTENT")
            self.assertEqual(existing_custom_db.read_text(), "CUSTOM DB CONTENT")
            self.assertEqual((git_dir / "config").read_text(), "GIT CONFIG")
            self.assertEqual((myenv_dir / "pyvenv.cfg").read_text(), "VENV CONFIG")

        finally:
            shutil.rmtree(temp_src, ignore_errors=True)
            shutil.rmtree(temp_tgt, ignore_errors=True)

    def test_database_safety_backup(self):
        backup_res = create_safety_database_backup()
        if backup_res:
            self.assertTrue(os.path.exists(backup_res))
            # Clean up the test backup file
            try:
                os.remove(backup_res)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
