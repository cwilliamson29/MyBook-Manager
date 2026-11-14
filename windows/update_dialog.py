import os
import sys
import tempfile
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from windows.settings_helpers.updater import (
    APP_VERSION,
    get_current_version,
    get_configured_repo,
    check_for_updates,
    download_update_package,
    apply_update,
    restart_application,
    open_release_page,
    get_platform_info
)

# Colors matching the application theme
CARD_BG = ("#ffffff", "#21262d")
CARD_BORDER = ("#d0d7de", "#30363d")
INNER_BG = ("#f6f8fa", "#161b22")
INNER_BORDER = ("#d0d7de", "#30363d")
HEADER_BG = ("#f6f8fa", "#161b22")
TEXT_PRIMARY = ("#1f2328", "#f0f6fc")
TEXT_MUTED = ("#656d76", "#8b949e")
TEXT_ACCENT = ("#0969da", "#58a6ff")
BTN_SECONDARY_BG = ("#e1e4e8", "#21262d")
BTN_SECONDARY_HOVER = ("#d0d7de", "#30363d")
BTN_SECONDARY_BORDER = ("#d0d7de", "#30363d")
BTN_SECONDARY_TEXT = ("#1f2328", "#f0f6fc")


class UpdateDialog(ctk.CTkToplevel):
    def __init__(self, parent_window, release_info, on_update_completed=None):
        super().__init__(parent_window)

        self.withdraw()
        self.parent_window = parent_window
        self.release_info = release_info
        self.on_update_completed = on_update_completed

        self.title("Software Update Available")
        self.center_on_parent(parent_window, 560, 620)
        self.resizable(False, False)

        self.is_downloading = False
        self.is_cancelled = False
        self.download_temp_file = None
        self.deferred_restart_command = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.card_style = {
            "fg_color": CARD_BG,
            "corner_radius": 8,
            "border_width": 1,
            "border_color": CARD_BORDER
        }

        self.build_ui()
        self.deiconify()
        self.lift()
        self.focus_force()

    def build_ui(self):
        # 1. Header Frame
        header = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=70)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        header_box = ctk.CTkFrame(header, fg_color="transparent")
        header_box.pack(side="left", padx=16, pady=10)

        title_lbl = ctk.CTkLabel(
            header_box,
            text="🚀 Software Update Available",
            font=("Arial", 16, "bold"),
            text_color=TEXT_PRIMARY
        )
        title_lbl.pack(anchor="w")

        latest_tag = self.release_info.get("tag_name", self.release_info.get("latest_version", "New"))
        subtitle_lbl = ctk.CTkLabel(
            header_box,
            text=f"A new version of MyBook Manager ({latest_tag}) is available for download.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        )
        subtitle_lbl.pack(anchor="w")

        # 2. Main Content Container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=14, pady=10)

        # Version Comparison Badges
        ver_card = ctk.CTkFrame(main_frame, **self.card_style)
        ver_card.pack(fill="x", pady=(0, 8))

        ver_grid = ctk.CTkFrame(ver_card, fg_color="transparent")
        ver_grid.pack(fill="x", padx=12, pady=10)
        ver_grid.columnconfigure(0, weight=1)
        ver_grid.columnconfigure(1, weight=1)

        # Current Version tile
        c_tile = ctk.CTkFrame(ver_grid, fg_color=INNER_BG, corner_radius=6, border_width=1, border_color=INNER_BORDER)
        c_tile.grid(row=0, column=0, padx=(0, 4), sticky="nsew")
        ctk.CTkLabel(c_tile, text="Current Version", font=("Arial", 10), text_color=TEXT_MUTED).pack(pady=(6, 0))
        ctk.CTkLabel(c_tile, text=f"v{self.release_info.get('current_version', APP_VERSION)}", font=("Arial", 13, "bold"), text_color=TEXT_PRIMARY).pack(pady=(0, 6))

        # New Version tile
        n_tile = ctk.CTkFrame(ver_grid, fg_color=INNER_BG, corner_radius=6, border_width=1, border_color=INNER_BORDER)
        n_tile.grid(row=0, column=1, padx=(4, 0), sticky="nsew")
        ctk.CTkLabel(n_tile, text="Latest Version", font=("Arial", 10), text_color=TEXT_MUTED).pack(pady=(6, 0))
        ctk.CTkLabel(n_tile, text=f"v{self.release_info.get('latest_version')}", font=("Arial", 13, "bold"), text_color="#2ea043").pack(pady=(0, 6))

        # Release Info & Notes Card
        notes_card = ctk.CTkFrame(main_frame, **self.card_style)
        notes_card.pack(fill="both", expand=True, pady=(0, 8))

        n_header = ctk.CTkFrame(notes_card, fg_color="transparent")
        n_header.pack(fill="x", padx=12, pady=(10, 4))

        rel_name = self.release_info.get("release_name", "Release Notes")
        ctk.CTkLabel(n_header, text=rel_name, font=("Arial", 13, "bold"), text_color=TEXT_PRIMARY).pack(side="left")

        pub_date = self.release_info.get("published_at", "")
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                date_str = dt.strftime("%b %d, %Y")
            except Exception:
                date_str = pub_date[:10]
            ctk.CTkLabel(n_header, text=date_str, font=("Arial", 11), text_color=TEXT_MUTED).pack(side="right")

        # Scrollable changelog view
        self.notes_box = ctk.CTkTextbox(
            notes_card,
            fg_color=INNER_BG,
            corner_radius=6,
            border_width=1,
            border_color=INNER_BORDER,
            font=("Arial", 11),
            wrap="word"
        )
        self.notes_box.pack(fill="both", expand=True, padx=12, pady=(4, 10))
        raw_notes = self.release_info.get("release_notes", "No release details provided.")
        self.notes_box.insert("1.0", raw_notes)
        self.notes_box.configure(state="disabled")

        # Progress / Status Card
        self.progress_card = ctk.CTkFrame(main_frame, **self.card_style)
        self.progress_card.pack(fill="x", pady=(0, 8))

        p_inner = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        p_inner.pack(fill="x", padx=12, pady=10)

        target_asset = self.release_info.get("target_asset")
        asset_desc = f"Package: {target_asset.get('name')}" if target_asset else "Platform: Cross-Platform Source Archive"
        plat_info = get_platform_info()
        os_desc = f"{plat_info['os_name']} ({plat_info['arch']})"

        self.info_status_label = ctk.CTkLabel(
            p_inner,
            text=f"Target: {os_desc}  •  {asset_desc}",
            font=("Arial", 10),
            text_color=TEXT_MUTED,
            anchor="w"
        )
        self.info_status_label.pack(fill="x", pady=(0, 4))

        self.progress_bar = ctk.CTkProgressBar(p_inner, height=10, corner_radius=5)
        self.progress_bar.pack(fill="x", pady=(4, 4))
        self.progress_bar.set(0)

        self.status_detail_label = ctk.CTkLabel(
            p_inner,
            text="Ready to download and install update.",
            font=("Arial", 11),
            text_color=TEXT_PRIMARY,
            anchor="w"
        )
        self.status_detail_label.pack(fill="x")

        # 3. Footer Action Buttons
        footer = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=50)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        # View on GitHub button on left
        github_btn = ctk.CTkButton(
            footer,
            text="View on GitHub ↗",
            width=120,
            height=30,
            font=("Arial", 11),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            command=lambda: open_release_page(self.release_info.get("html_url"))
        )
        github_btn.pack(side="left", padx=14, pady=10)

        # Close / Later button
        self.close_btn = ctk.CTkButton(
            footer,
            text="Later",
            width=80,
            height=30,
            font=("Arial", 11),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            command=self.on_close
        )
        self.close_btn.pack(side="right", padx=(6, 14), pady=10)

        # Primary Action Button (Download & Install / Restart Now)
        self.action_btn = ctk.CTkButton(
            footer,
            text="Download & Install",
            width=150,
            height=30,
            font=("Arial", 12, "bold"),
            fg_color="#1f6feb",
            hover_color="#388bfd",
            command=self.start_download_and_install
        )
        self.action_btn.pack(side="right", padx=6, pady=10)

    def start_download_and_install(self):
        if self.is_downloading:
            return

        target_asset = self.release_info.get("target_asset")
        download_url = target_asset.get("download_url") if target_asset else self.release_info.get("zipball_url")

        if not download_url:
            messagebox.showerror(
                "Update Error",
                "No valid download URL was found for this release.\nPlease visit GitHub to download manually.",
                parent=self
            )
            return

        self.is_downloading = True
        self.is_cancelled = False
        self.action_btn.configure(state="disabled", text="Updating...")
        self.close_btn.configure(text="Cancel", command=self.cancel_download)
        self.progress_bar.set(0)
        self.status_detail_label.configure(text="Connecting to GitHub...", text_color="#58a6ff")

        def _progress(downloaded, total, percent, speed):
            def _ui():
                if self.is_cancelled:
                    return
                self.progress_bar.set(percent)
                if total > 0:
                    mb_down = downloaded / (1024 * 1024)
                    mb_tot = total / (1024 * 1024)
                    speed_mb = speed / (1024 * 1024)
                    pct_str = f"{int(percent * 100)}%"
                    self.status_detail_label.configure(
                        text=f"Downloading: {mb_down:.1f} MB / {mb_tot:.1f} MB ({pct_str}) • {speed_mb:.1f} MB/s",
                        text_color="#58a6ff"
                    )
                else:
                    mb_down = downloaded / (1024 * 1024)
                    speed_mb = speed / (1024 * 1024)
                    self.status_detail_label.configure(
                        text=f"Downloading: {mb_down:.1f} MB • {speed_mb:.1f} MB/s",
                        text_color="#58a6ff"
                    )
            self.after(0, _ui)

        def _cancel_check():
            return self.is_cancelled

        def _worker():
            # Create temp destination file
            fd, temp_file_path = tempfile.mkstemp(prefix="mybook_pkg_", suffix=".zip")
            os.close(fd)
            self.download_temp_file = temp_file_path

            success = download_update_package(
                download_url,
                temp_file_path,
                progress_callback=_progress,
                cancel_check=_cancel_check
            )

            if not success or self.is_cancelled:
                def _on_cancel():
                    self.is_downloading = False
                    self.action_btn.configure(state="normal", text="Download & Install")
                    self.close_btn.configure(text="Close", command=self.on_close)
                    self.status_detail_label.configure(text="Download cancelled.", text_color="#f85149")
                    if self.download_temp_file and os.path.exists(self.download_temp_file):
                        try:
                            os.remove(self.download_temp_file)
                        except Exception:
                            pass
                self.after(0, _on_cancel)
                return

            def _status_cb(msg):
                self.after(0, lambda: self.status_detail_label.configure(text=msg, text_color="#e3b341"))

            install_result = apply_update(temp_file_path, self.release_info, status_callback=_status_cb)

            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass

            def _on_finished():
                self.is_downloading = False
                if install_result.get("success"):
                    self.progress_bar.set(1.0)
                    self.status_detail_label.configure(
                        text="✓ Update installed successfully! Restart to apply changes.",
                        text_color="#3fb950"
                    )
                    self.action_btn.configure(
                        state="normal",
                        text="Restart Application Now",
                        fg_color="#238636",
                        hover_color="#2ea043",
                        command=self.perform_restart
                    )
                    self.close_btn.configure(text="Restart Later", command=self.on_close)
                    self.deferred_restart_command = install_result.get("deferred_command")

                    if self.on_update_completed:
                        self.on_update_completed(self.release_info)

                    if messagebox.askyesno(
                        "Update Ready",
                        f"MyBook Manager has been updated to v{self.release_info.get('latest_version')}!\n\nWould you like to restart the application now?",
                        parent=self
                    ):
                        self.perform_restart()
                else:
                    err_msg = install_result.get("error", "Unknown error during installation.")
                    self.status_detail_label.configure(
                        text=f"Installation failed: {err_msg}",
                        text_color="#f85149"
                    )
                    self.action_btn.configure(state="normal", text="Retry Update")
                    self.close_btn.configure(text="Close", command=self.on_close)
                    messagebox.showerror("Update Installation Failed", err_msg, parent=self)

            self.after(0, _on_finished)

        threading.Thread(target=_worker, daemon=True).start()

    def cancel_download(self):
        if self.is_downloading:
            self.is_cancelled = True
            self.status_detail_label.configure(text="Stopping download...", text_color="#f85149")

    def perform_restart(self):
        restart_application(self.deferred_restart_command)

    def on_close(self):
        if self.is_downloading:
            if not messagebox.askyesno("Cancel Update", "Download is in progress. Are you sure you want to cancel?", parent=self):
                return
            self.cancel_download()
        self.destroy()

    def center_on_parent(self, parent, width, height):
        try:
            parent.update_idletasks()
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            x = parent_x + (parent_width - width) // 2
            y = parent_y + (parent_height - height) // 2
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            self.geometry(f"{width}x{height}")
