import os
import re
import signal
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

try:
    import AVFoundation
    import Foundation
    HAS_AVFOUNDATION = True
except ImportError:
    HAS_AVFOUNDATION = False

try:
    from tinytag import TinyTag
except ImportError:
    TinyTag = None

from db import db_get, db_update


def natural_sort_key(text):
    """Sort strings containing numbers in human/natural chronological order."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(text))]


def format_time(seconds):
    """Formats seconds into MM:SS or HH:MM:SS string."""
    if seconds is None or seconds < 0:
        return "00:00"
    s = int(round(seconds))
    hrs = s // 3600
    mins = (s % 3600) // 60
    secs = s % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def clean_chapter_title(filename):
    """Produces a clean, human-friendly chapter title from filename."""
    name, _ = os.path.splitext(filename)
    # Replace underscores/hyphens with spaces if appropriate
    name = re.sub(r'[_\-]+', ' ', name).strip()
    return name


class AudioPlayerPane(ctk.CTkFrame):
    """
    Audiobook MP3 / Chapter Player component for the Details Pane.
    Allows selecting a folder of audiobook chapters, compiling a playlist,
    and controlling audio playback (play/pause, seek, skip, chapter jump, volume, speed).
    """

    AUDIO_EXTENSIONS = ('.mp3', '.m4a', '.m4b', '.aac', '.flac', '.wav', '.ogg', '.wma')

    def __init__(self, parent, app=None, width=380):
        super().__init__(parent, width=width, fg_color=("gray88", "gray20"), corner_radius=8)
        self.app = app
        self.book_id = None
        self.folder_path = None
        self.playlist = []  # list of dicts: {path, filename, title, duration}
        self.current_index = -1

        # Playback engine state
        self.is_playlist_collapsed = False
        self.native_player = None
        self.current_process = None
        self.is_playing = False
        self.is_paused = False
        self.track_position = 0.0
        self.track_duration = 0.0
        self.playback_speed = 1.0
        self.volume = 1.0
        self.is_user_scrubbing = False
        self.monitor_thread = None
        self.stop_monitor_event = threading.Event()
        self.play_start_time = 0.0
        self.play_start_offset = 0.0

        # UI references for playlist items
        self.item_widgets = []

        self._build_ui()
        self._start_progress_loop()

    def _build_ui(self):
        # 1. Top Header Bar
        header_bar = ctk.CTkFrame(self, fg_color="transparent")
        header_bar.pack(side="top", fill="x", padx=10, pady=(8, 4))

        title_lbl = ctk.CTkLabel(
            header_bar,
            text="🎧 Audiobook Player",
            font=("Arial", 13, "bold"),
            text_color=("#0969da", "#58a6ff")
        )
        title_lbl.pack(side="left", anchor="w")

        self.unlink_btn = ctk.CTkButton(
            header_bar,
            text="✕ Unlink",
            width=58,
            height=22,
            font=("Arial", 10, "bold"),
            fg_color=("#cf222e", "#8b1a1a"),
            hover_color=("#f85149", "#a82020"),
            command=self.unlink_folder
        )

        self.folder_btn = ctk.CTkButton(
            header_bar,
            text="📁 Select Folder",
            width=92,
            height=22,
            font=("Arial", 11, "bold"),
            fg_color="#1f6feb",
            hover_color="#388bfd",
            command=self.choose_folder
        )
        self.folder_btn.pack(side="right", padx=(4, 0))

        # 2. Main Content Stack (Empty View vs Playlist View)
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(side="top", fill="both", expand=True, padx=8, pady=(0, 4))

        # Empty View
        self.empty_view = ctk.CTkFrame(self.content_container, fg_color=("gray82", "gray24"), corner_radius=6)
        empty_lbl = ctk.CTkLabel(
            self.empty_view,
            text="No audiobook folder linked.\nSelect a folder of chapter files to play.",
            font=("Arial", 11),
            text_color=("#57606a", "gray70"),
            justify="center"
        )
        empty_lbl.pack(side="top", pady=(24, 10))

        empty_btn = ctk.CTkButton(
            self.empty_view,
            text="📁 Select Audiobook Folder",
            font=("Arial", 11, "bold"),
            height=28,
            fg_color="#1f6feb",
            hover_color="#388bfd",
            command=self.choose_folder
        )
        empty_btn.pack(side="top", pady=(0, 24))

        # Playlist / Chapters View
        self.playlist_view = ctk.CTkFrame(self.content_container, fg_color="transparent")

        # Playlist Header (Summary and Collapse/Expand Toggle)
        self.playlist_header = ctk.CTkFrame(self.playlist_view, fg_color="transparent")
        self.playlist_header.pack(side="top", fill="x", padx=2, pady=(0, 2))

        # Playlist Summary Subtitle
        self.summary_label = ctk.CTkLabel(
            self.playlist_header,
            text="0 Chapters",
            font=("Arial", 10, "italic"),
            text_color=("#57606a", "gray70"),
            anchor="w",
            cursor="hand2"
        )
        self.summary_label.pack(side="left", fill="x", expand=True)
        self.summary_label.bind("<Button-1>", lambda e: self.toggle_playlist_collapse())

        self.collapse_btn = ctk.CTkButton(
            self.playlist_header,
            text="▲ Hide List",
            width=70,
            height=20,
            font=("Arial", 10, "bold"),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            text_color=("#1f2328", "#f0f6fc"),
            command=self.toggle_playlist_collapse
        )
        self.collapse_btn.pack(side="right", padx=(4, 0))

        # Scrollable Playlist Frame
        self.playlist_scroll = ctk.CTkScrollableFrame(
            self.playlist_view,
            height=85,
            fg_color=("gray80", "gray18"),
            corner_radius=6
        )
        self.playlist_scroll.pack(side="top", fill="both", expand=True, pady=(0, 4))

        # 3. Playback Controls Card
        self.controls_card = ctk.CTkFrame(self, fg_color=("gray82", "gray24"), corner_radius=6)
        self.controls_card.pack(side="bottom", fill="x", padx=8, pady=(0, 8))

        # Now Playing Chapter Label
        self.now_playing_label = ctk.CTkLabel(
            self.controls_card,
            text="No Chapter Playing",
            font=("Arial", 11, "bold"),
            text_color=("#1f2328", "#f0f6fc"),
            anchor="w"
        )
        self.now_playing_label.pack(side="top", fill="x", padx=8, pady=(4, 0))

        # Time & Scrub Slider Row
        time_row = ctk.CTkFrame(self.controls_card, fg_color="transparent")
        time_row.pack(side="top", fill="x", padx=8, pady=(2, 2))

        self.time_elapsed_label = ctk.CTkLabel(
            time_row,
            text="00:00",
            font=("Arial", 10),
            text_color=("#57606a", "gray75"),
            width=36,
            anchor="w"
        )
        self.time_elapsed_label.pack(side="left")

        self.progress_slider = ctk.CTkSlider(
            time_row,
            from_=0,
            to=100,
            height=14,
            command=self.on_slider_change
        )
        self.progress_slider.set(0)
        self.progress_slider.pack(side="left", fill="x", expand=True, padx=4)
        self.progress_slider.bind("<Button-1>", lambda e: self._on_slider_press())
        self.progress_slider.bind("<ButtonRelease-1>", lambda e: self._on_slider_release())

        self.time_total_label = ctk.CTkLabel(
            time_row,
            text="00:00",
            font=("Arial", 10),
            text_color=("#57606a", "gray75"),
            width=36,
            anchor="e"
        )
        self.time_total_label.pack(side="right")

        # Playback Buttons Row
        btn_row = ctk.CTkFrame(self.controls_card, fg_color="transparent")
        btn_row.pack(side="top", fill="x", padx=6, pady=(0, 4))

        self.prev_btn = ctk.CTkButton(
            btn_row,
            text="⏮",
            width=28,
            height=24,
            font=("Arial", 11),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.play_previous_chapter
        )
        self.prev_btn.pack(side="left", padx=2, expand=True)

        self.skip_back_btn = ctk.CTkButton(
            btn_row,
            text="-15s",
            width=36,
            height=24,
            font=("Arial", 10, "bold"),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=lambda: self.seek_relative(-15)
        )
        self.skip_back_btn.pack(side="left", padx=2, expand=True)

        self.play_btn = ctk.CTkButton(
            btn_row,
            text="▶ Play",
            width=64,
            height=26,
            font=("Arial", 11, "bold"),
            fg_color="#238636",
            hover_color="#2ea043",
            command=self.toggle_play_pause
        )
        self.play_btn.pack(side="left", padx=3, expand=True)

        self.skip_fwd_btn = ctk.CTkButton(
            btn_row,
            text="+15s",
            width=36,
            height=24,
            font=("Arial", 10, "bold"),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=lambda: self.seek_relative(15)
        )
        self.skip_fwd_btn.pack(side="left", padx=2, expand=True)

        self.next_btn = ctk.CTkButton(
            btn_row,
            text="⏭",
            width=28,
            height=24,
            font=("Arial", 11),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.play_next_chapter
        )
        self.next_btn.pack(side="left", padx=2, expand=True)

        self.stop_btn = ctk.CTkButton(
            btn_row,
            text="⏹",
            width=26,
            height=24,
            font=("Arial", 10),
            fg_color=("#cf222e", "#8b1a1a"),
            hover_color=("#f85149", "#a82020"),
            command=self.stop
        )
        self.stop_btn.pack(side="left", padx=2, expand=True)

        # Secondary Row: Speed & Volume Controls
        extra_row = ctk.CTkFrame(self.controls_card, fg_color="transparent")
        extra_row.pack(side="top", fill="x", padx=8, pady=(0, 4))

        # Speed Dropdown
        speed_lbl = ctk.CTkLabel(extra_row, text="Speed:", font=("Arial", 10), text_color=("#57606a", "gray70"))
        speed_lbl.pack(side="left", padx=(0, 2))

        self.speed_menu = ctk.CTkOptionMenu(
            extra_row,
            values=["0.75x", "1.0x", "1.25x", "1.5x", "1.75x", "2.0x"],
            width=68,
            height=20,
            font=("Arial", 10),
            command=self.on_speed_change
        )
        self.speed_menu.set("1.0x")
        self.speed_menu.pack(side="left", padx=(0, 10))

        # Volume Slider
        vol_lbl = ctk.CTkLabel(extra_row, text="🔊", font=("Arial", 11))
        vol_lbl.pack(side="left", padx=(0, 2))

        self.volume_slider = ctk.CTkSlider(
            extra_row,
            from_=0,
            to=100,
            height=12,
            width=80,
            command=self.on_volume_change
        )
        self.volume_slider.set(100)
        self.volume_slider.pack(side="left", fill="x", expand=True)

        # Show initial empty view
        self._show_empty_view()

    def _update_speed_ui(self, speed_val):
        """Updates the speed dropdown menu value."""
        try:
            val = float(speed_val) if speed_val else 1.0
            speed_str = f"{val:g}x"
            valid_options = ["0.75x", "1.0x", "1.25x", "1.5x", "1.75x", "2.0x"]
            if speed_str in valid_options:
                self.speed_menu.set(speed_str)
            else:
                self.speed_menu.set(f"{val:.2f}x")
        except Exception as e:
            print("Error updating speed UI:", e)
            self.speed_menu.set("1.0x")

    def _show_empty_view(self):
        """Displays empty state when no audiobook folder is linked."""
        self.folder_path = None
        self.playlist = []
        self.current_index = -1
        self.track_position = 0.0
        self.track_duration = 0.0
        self.is_playing = False
        self.is_paused = False

        # Clear playlist rows
        for item in self.item_widgets:
            try:
                if isinstance(item, dict) and "frame" in item:
                    item["frame"].destroy()
                else:
                    item.destroy()
            except Exception:
                pass
        self.item_widgets = []

        if hasattr(self, "playlist_scroll"):
            for widget in self.playlist_scroll.winfo_children():
                try:
                    widget.destroy()
                except Exception:
                    pass

        self.playlist_view.pack_forget()
        self.empty_view.pack(fill="both", expand=True, pady=10)
        self.unlink_btn.pack_forget()
        self.folder_btn.configure(text="📁 Select Folder")
        self.now_playing_label.configure(text="No Chapter Playing")
        self.time_elapsed_label.configure(text="00:00")
        self.time_total_label.configure(text="00:00")
        self.progress_slider.set(0)
        self.play_btn.configure(text="▶ Play", fg_color="#238636", hover_color="#2ea043")
        self._update_controls_state(enabled=False)

    def _show_playlist_view(self):
        """Displays the compiled chapter playlist."""
        self.empty_view.pack_forget()
        self.playlist_view.pack(fill="both", expand=True)
        self.unlink_btn.pack(side="right", padx=(4, 0))
        self.folder_btn.configure(text="📁 Change")
        self._update_playlist_collapse_ui()
        self._update_controls_state(enabled=True)

    def toggle_playlist_collapse(self):
        """Toggles visibility of the scrollable chapters list."""
        self.is_playlist_collapsed = not self.is_playlist_collapsed
        self._update_playlist_collapse_ui()

    def _update_playlist_collapse_ui(self):
        """Updates the chapter playlist collapse state and button text."""
        if not hasattr(self, "collapse_btn") or not hasattr(self, "playlist_scroll"):
            return
        if self.is_playlist_collapsed:
            self.playlist_scroll.pack_forget()
            self.collapse_btn.configure(text="▼ Show List")
        else:
            self.playlist_scroll.pack(side="top", fill="both", expand=True, pady=(0, 4))
            self.collapse_btn.configure(text="▲ Hide List")

    def _update_controls_state(self, enabled=True):
        """Enables or disables playback controls based on playlist availability."""
        state = "normal" if enabled and len(self.playlist) > 0 else "disabled"
        self.play_btn.configure(state=state)
        self.prev_btn.configure(state=state)
        self.next_btn.configure(state=state)
        self.skip_back_btn.configure(state=state)
        self.skip_fwd_btn.configure(state=state)
        self.stop_btn.configure(state=state)
        self.progress_slider.configure(state=state)

    def set_book(self, book_id):
        """
        Loads the audiobook folder for the given book_id from the database.
        Compiles the playlist and prepares playback, restoring saved position and speed.
        """
        if self.book_id == book_id:
            return

        # Save progress of previous book before switching
        if self.book_id:
            self.save_progress()

        self.stop()
        self.book_id = book_id
        self.current_index = -1
        self.playlist = []

        if not book_id:
            self.playback_speed = 1.0
            self._update_speed_ui(1.0)
            self._show_empty_view()
            return

        # Load per-book playback speed
        saved_speed = db_get.get_book_audio_speed(book_id)
        self.playback_speed = float(saved_speed) if saved_speed else 1.0
        self._update_speed_ui(self.playback_speed)

        folder = db_get.get_book_audio_folder(book_id)
        if folder and os.path.isdir(folder):
            self.load_folder(folder, save_to_db=False)
        else:
            self._show_empty_view()

    def choose_folder(self):
        """Prompts user to select a folder from their file system."""
        initial_dir = self.folder_path if self.folder_path and os.path.isdir(self.folder_path) else os.path.expanduser("~")
        selected = filedialog.askdirectory(
            title="Select Audiobook Chapter Folder",
            initialdir=initial_dir
        )
        if selected:
            self.load_folder(selected, save_to_db=True)

    def unlink_folder(self):
        """Clears the linked audiobook folder and saved progress from book record."""
        if not self.folder_path:
            return
        if messagebox.askyesno("Unlink Folder", "Remove the audiobook folder link for this book?"):
            self.stop_current_process()
            self.is_playing = False
            self.is_paused = False
            self.folder_path = None
            self.playlist = []
            self.current_index = -1
            self.track_position = 0.0
            if self.book_id:
                db_update.update_book_audio_folder(self.book_id, None)
                db_update.update_book_audio_progress(self.book_id, None, 0.0)
            self._show_empty_view()

    def load_folder(self, folder_path, save_to_db=True):
        """
        Scans folder for audio files, compiles sorted chapter playlist,
        extracts durations, restores saved progress, and populates UI.
        """
        if not folder_path or not os.path.isdir(folder_path):
            self._show_empty_view()
            return

        self.folder_path = folder_path
        if save_to_db and self.book_id:
            db_update.update_book_audio_folder(self.book_id, folder_path)

        # Scan for supported audio files
        audio_files = []
        try:
            for entry in os.scandir(folder_path):
                if entry.is_file() and entry.name.lower().endswith(self.AUDIO_EXTENSIONS):
                    audio_files.append(entry.path)
        except Exception as e:
            print("Error scanning audio folder:", e)
            messagebox.showerror("Error", f"Could not read audio folder:\n{e}")
            self._show_empty_view()
            return

        # Sort files naturally so Chapter 1, Chapter 2, ..., Chapter 10 sort chronologically
        audio_files.sort(key=lambda p: natural_sort_key(os.path.basename(p)))

        if not audio_files:
            messagebox.showwarning(
                "No Audio Files",
                f"No MP3 or supported audio files found in:\n{folder_path}"
            )
            self._show_empty_view()
            return

        # Build playlist objects with metadata
        self.playlist = []
        total_duration = 0.0

        for path in audio_files:
            fname = os.path.basename(path)
            clean_title = clean_chapter_title(fname)
            duration = 0.0

            if TinyTag:
                try:
                    tag = TinyTag.get(path)
                    if tag.duration:
                        duration = float(tag.duration)
                    if tag.title and str(tag.title).strip():
                        clean_title = str(tag.title).strip()
                except Exception:
                    pass

            if duration <= 0 and HAS_AVFOUNDATION:
                try:
                    url = Foundation.NSURL.fileURLWithPath_(path)
                    tmp_p, _ = AVFoundation.AVAudioPlayer.alloc().initWithContentsOfURL_error_(url, None)
                    if tmp_p:
                        duration = float(tmp_p.duration())
                except Exception:
                    pass

            total_duration += duration
            self.playlist.append({
                "path": path,
                "filename": fname,
                "title": clean_title,
                "duration": duration
            })

        # Update Summary
        folder_display = os.path.basename(folder_path) or folder_path
        count = len(self.playlist)
        dur_str = f" • Total: {format_time(total_duration)}" if total_duration > 0 else ""
        self.summary_label.configure(
            text=f"📁 {folder_display} ({count} Chapter{'s' if count != 1 else ''}{dur_str})"
        )

        self._render_playlist()
        self._show_playlist_view()

        # Restore saved audio progress if available
        saved_track, saved_pos = (None, 0.0)
        if self.book_id:
            saved_track, saved_pos = db_get.get_book_audio_progress(self.book_id)

        target_idx = 0
        initial_pos = 0.0
        if saved_track and self.playlist:
            for idx, item in enumerate(self.playlist):
                if item["filename"] == saved_track or item["title"] == saved_track:
                    target_idx = idx
                    initial_pos = max(0.0, float(saved_pos))
                    break

        if self.playlist:
            self.select_chapter(target_idx, auto_start=False, initial_position=initial_pos)

    def _render_playlist(self):
        """Renders playlist rows in scrollable frame."""
        for widget in self.playlist_scroll.winfo_children():
            widget.destroy()
        self.item_widgets = []

        for idx, item in enumerate(self.playlist):
            row_frame = ctk.CTkFrame(
                self.playlist_scroll,
                fg_color=("gray85", "gray22"),
                corner_radius=4,
                cursor="hand2"
            )
            row_frame.pack(side="top", fill="x", padx=2, pady=1)

            # Click to play
            row_frame.bind("<Button-1>", lambda e, i=idx: self.select_chapter(i, auto_start=True))

            # Index & Status indicator
            idx_lbl = ctk.CTkLabel(
                row_frame,
                text=f"{idx + 1}.",
                font=("Arial", 10, "bold"),
                width=24,
                anchor="e",
                text_color=("#57606a", "gray70")
            )
            idx_lbl.pack(side="left", padx=(4, 2), pady=2)
            idx_lbl.bind("<Button-1>", lambda e, i=idx: self.select_chapter(i, auto_start=True))

            # Chapter Title
            display_title = item["title"]
            if len(display_title) > 34:
                display_title = display_title[:31] + "..."
            title_lbl = ctk.CTkLabel(
                row_frame,
                text=display_title,
                font=("Arial", 10),
                anchor="w"
            )
            title_lbl.pack(side="left", fill="x", expand=True, padx=2, pady=2)
            title_lbl.bind("<Button-1>", lambda e, i=idx: self.select_chapter(i, auto_start=True))

            # Duration
            dur_str = format_time(item["duration"]) if item["duration"] > 0 else ""
            dur_lbl = ctk.CTkLabel(
                row_frame,
                text=dur_str,
                font=("Arial", 9),
                text_color=("#57606a", "gray70"),
                width=36,
                anchor="e"
            )
            dur_lbl.pack(side="right", padx=(2, 6), pady=2)
            dur_lbl.bind("<Button-1>", lambda e, i=idx: self.select_chapter(i, auto_start=True))

            self.item_widgets.append({
                "frame": row_frame,
                "idx_lbl": idx_lbl,
                "title_lbl": title_lbl,
                "dur_lbl": dur_lbl
            })

    def _highlight_current_item(self):
        """Updates visual highlight for currently active chapter."""
        for idx, widgets in enumerate(self.item_widgets):
            if idx == self.current_index:
                widgets["frame"].configure(fg_color=("#21262d", "#1f6feb"))
                widgets["idx_lbl"].configure(text="▶", text_color="#ffffff")
                widgets["title_lbl"].configure(font=("Arial", 10, "bold"), text_color="#ffffff")
                widgets["dur_lbl"].configure(text_color="#e6edf3")
            else:
                widgets["frame"].configure(fg_color=("gray85", "gray22"))
                widgets["idx_lbl"].configure(text=f"{idx + 1}.", text_color=("#57606a", "gray70"))
                widgets["title_lbl"].configure(font=("Arial", 10), text_color=("gray10", "gray90"))
                widgets["dur_lbl"].configure(text_color=("#57606a", "gray70"))

    def save_progress(self):
        """Saves current chapter filename and playback timestamp to the database."""
        if not self.book_id or not self.playlist:
            return
        if self.current_index < 0 or self.current_index >= len(self.playlist):
            return

        try:
            current_track = self.playlist[self.current_index]["filename"]
            if self.native_player and self.is_playing and not self.is_paused:
                self.track_position = max(0.0, float(self.native_player.currentTime()))
            elif self.is_playing and not self.is_paused:
                elapsed = self.play_start_offset + (time.time() - self.play_start_time) * self.playback_speed
                self.track_position = max(0.0, elapsed)
            pos = max(0.0, float(self.track_position))
            if self.track_duration > 0 and pos > self.track_duration:
                pos = self.track_duration
            db_update.update_book_audio_progress(self.book_id, current_track, pos)
        except Exception as e:
            print("Error saving audio progress:", e)

    def select_chapter(self, index, auto_start=True, initial_position=0.0):
        """Selects chapter at index in playlist, optionally starting playback."""
        if index < 0 or index >= len(self.playlist):
            return

        if self.current_index != index and self.current_index >= 0:
            self.save_progress()

        self.current_index = index
        self._highlight_current_item()

        chapter = self.playlist[index]
        self.now_playing_label.configure(text=f"▶ {index + 1}. {chapter['title']}")
        self.track_duration = chapter.get("duration", 0.0)
        self.track_position = max(0.0, float(initial_position))
        if self.track_duration > 0 and self.track_position > self.track_duration:
            self.track_position = self.track_duration

        self.time_elapsed_label.configure(text=format_time(self.track_position))
        self.time_total_label.configure(text=format_time(self.track_duration))
        if self.track_duration > 0:
            self.progress_slider.set(min(100.0, (self.track_position / self.track_duration) * 100.0))
        else:
            self.progress_slider.set(0)

        if auto_start:
            self.play_chapter(index, start_offset=self.track_position)
        else:
            self.stop_current_process()
            self.is_playing = False
            self.is_paused = False
            self.play_btn.configure(text="▶ Play", fg_color="#238636", hover_color="#2ea043")

    def play_chapter(self, index, start_offset=0.0):
        """Starts audio playback for chapter at index."""
        if index < 0 or index >= len(self.playlist):
            return

        self.stop_current_process()

        self.current_index = index
        self._highlight_current_item()
        chapter = self.playlist[index]
        file_path = chapter["path"]

        self.track_position = max(0.0, float(start_offset))
        self.track_duration = chapter.get("duration", 0.0)
        if self.track_duration > 0 and self.track_position > self.track_duration:
            self.track_position = self.track_duration

        self.play_start_time = time.time()
        self.play_start_offset = self.track_position

        self.now_playing_label.configure(text=f"▶ {index + 1}. {chapter['title']}")
        self.time_elapsed_label.configure(text=format_time(self.track_position))
        self.time_total_label.configure(text=format_time(self.track_duration))
        if self.track_duration > 0:
            self.progress_slider.set(min(100.0, (self.track_position / self.track_duration) * 100.0))

        try:
            if HAS_AVFOUNDATION:
                url = Foundation.NSURL.fileURLWithPath_(file_path)
                player, err = AVFoundation.AVAudioPlayer.alloc().initWithContentsOfURL_error_(url, None)
                if err or not player:
                    raise RuntimeError(f"Could not load audio file: {err}")
                player.setEnableRate_(True)
                player.prepareToPlay()
                player.setVolume_(max(0.0, min(1.0, float(self.volume))))
                player.setRate_(float(self.playback_speed))
                if self.track_position > 0:
                    player.setCurrentTime_(self.track_position)
                player.play()
                self.native_player = player
            else:
                vol_val = max(0.0, min(1.0, float(self.volume)))
                cmd = ["afplay", "-v", str(vol_val)]
                if self.playback_speed != 1.0:
                    cmd.extend(["-q", "1", "-r", str(self.playback_speed)])
                cmd.append(file_path)
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self._start_track_monitor(self.current_process, index)

            self.is_playing = True
            self.is_paused = False
            self.play_btn.configure(text="⏸ Pause", fg_color="#1f6feb", hover_color="#388bfd")
            self.save_progress()

        except Exception as e:
            print("Error playing audio chapter:", e)
            messagebox.showerror("Audio Playback Error", f"Failed to play audio file:\n{e}")
            self.stop()

    def _start_track_monitor(self, proc, track_idx):
        """Spawns background thread to detect when current chapter finishes playing (fallback mode)."""
        self.stop_monitor_event.set()
        self.stop_monitor_event = threading.Event()
        event = self.stop_monitor_event

        def _monitor():
            try:
                proc.wait()
            except Exception:
                pass

            if not event.is_set():
                # Process ended naturally (chapter finished)
                if self.winfo_exists():
                    self.after(0, lambda: self._on_chapter_finished(track_idx))

        self.monitor_thread = threading.Thread(target=_monitor, daemon=True)
        self.monitor_thread.start()

    def _on_chapter_finished(self, track_idx):
        """Callback when current track finishes naturally -> advances to next chapter."""
        if not self.is_playing or self.current_index != track_idx:
            return

        if self.current_index + 1 < len(self.playlist):
            self.play_chapter(self.current_index + 1, start_offset=0.0)
        else:
            self.stop()
            self.track_position = 0.0
            self.current_index = 0
            self.save_progress()
            self.now_playing_label.configure(text="Finished Audiobook")
            self.time_elapsed_label.configure(text="00:00")
            self.progress_slider.set(0)

    def toggle_play_pause(self):
        """Toggles between Play and Pause states."""
        if not self.playlist:
            return

        if self.current_index < 0:
            self.select_chapter(0, auto_start=True)
            return

        if self.is_playing and not self.is_paused:
            self.pause()
        elif self.is_paused:
            self.resume()
        else:
            self.play_chapter(self.current_index, start_offset=self.track_position)

    def pause(self):
        """Pauses audio playback and saves current position."""
        if self.native_player and self.is_playing and not self.is_paused:
            try:
                self.track_position = max(0.0, float(self.native_player.currentTime()))
                self.native_player.pause()
                self.is_paused = True
                self.play_btn.configure(text="▶ Resume", fg_color="#238636", hover_color="#2ea043")
                self.save_progress()
            except Exception as e:
                print("Error pausing native player:", e)
        elif self.current_process and self.is_playing and not self.is_paused:
            try:
                os.kill(self.current_process.pid, signal.SIGSTOP)
                self.is_paused = True
                self.track_position = self.play_start_offset + (time.time() - self.play_start_time) * self.playback_speed
                self.play_btn.configure(text="▶ Resume", fg_color="#238636", hover_color="#2ea043")
                self.save_progress()
            except Exception as e:
                print("Error pausing playback:", e)

    def resume(self):
        """Resumes paused audio playback."""
        if self.native_player and self.is_paused:
            try:
                self.native_player.play()
                self.is_paused = False
                self.play_btn.configure(text="⏸ Pause", fg_color="#1f6feb", hover_color="#388bfd")
            except Exception as e:
                print("Error resuming native player:", e)
                self.play_chapter(self.current_index, start_offset=self.track_position)
        elif self.current_process and self.is_paused:
            try:
                os.kill(self.current_process.pid, signal.SIGCONT)
                self.is_paused = False
                self.play_start_time = time.time()
                self.play_start_offset = self.track_position
                self.play_btn.configure(text="⏸ Pause", fg_color="#1f6feb", hover_color="#388bfd")
            except Exception as e:
                print("Error resuming playback:", e)
                self.play_chapter(self.current_index, start_offset=self.track_position)

    def stop_current_process(self):
        """Terminates currently running audio player safely."""
        self.stop_monitor_event.set()
        if self.native_player:
            try:
                self.native_player.stop()
            except Exception:
                pass
            self.native_player = None

        if self.current_process:
            try:
                if self.is_paused:
                    try:
                        os.kill(self.current_process.pid, signal.SIGCONT)
                    except Exception:
                        pass
                self.current_process.terminate()
                self.current_process.wait(timeout=0.2)
            except Exception:
                pass
            self.current_process = None

    def stop(self):
        """Stops playback and saves where audio stopped."""
        self.save_progress()
        self.stop_current_process()
        self.is_playing = False
        self.is_paused = False
        self.play_btn.configure(text="▶ Play", fg_color="#238636", hover_color="#2ea043")

    def play_previous_chapter(self):
        """Plays previous chapter or restarts current if > 3 seconds in."""
        if not self.playlist:
            return

        current = self.track_position
        if self.native_player and self.is_playing and not self.is_paused:
            current = float(self.native_player.currentTime())

        if current > 3.0 or self.current_index <= 0:
            self.seek_to(0.0)
            if not self.is_playing or self.is_paused:
                self.play_chapter(self.current_index, start_offset=0.0)
        else:
            self.select_chapter(self.current_index - 1, auto_start=True)

    def play_next_chapter(self):
        """Advances to and plays next chapter in playlist."""
        if not self.playlist:
            return
        if self.current_index + 1 < len(self.playlist):
            self.select_chapter(self.current_index + 1, auto_start=True)

    def seek_relative(self, seconds_delta):
        """Skips forward or backward by seconds_delta seconds."""
        if self.current_index < 0 or not self.playlist:
            return

        current = self.track_position
        if self.native_player and self.is_playing and not self.is_paused:
            current = float(self.native_player.currentTime())

        new_pos = max(0.0, current + seconds_delta)
        if self.track_duration > 0:
            new_pos = min(self.track_duration, new_pos)

        self.seek_to(new_pos)

    def seek_to(self, target_seconds):
        """Seeks directly to target_seconds in current chapter."""
        self.track_position = max(0.0, float(target_seconds))
        if self.track_duration > 0 and self.track_position > self.track_duration:
            self.track_position = self.track_duration

        if self.native_player:
            self.native_player.setCurrentTime_(self.track_position)
            if self.is_playing and not self.is_paused:
                self.native_player.play()
        elif self.is_playing and not self.is_paused:
            self.play_chapter(self.current_index, start_offset=self.track_position)
        else:
            self.stop_current_process()
            self.is_playing = False
            self.is_paused = False
            self.play_btn.configure(text="▶ Play", fg_color="#238636", hover_color="#2ea043")

        self.time_elapsed_label.configure(text=format_time(self.track_position))
        if self.track_duration > 0:
            self.progress_slider.set(min(100.0, (self.track_position / self.track_duration) * 100.0))
        self.save_progress()

    def _on_slider_press(self):
        self.is_user_scrubbing = True

    def _on_slider_release(self):
        self.is_user_scrubbing = False
        if self.track_duration > 0:
            pct = self.progress_slider.get() / 100.0
            target_sec = pct * self.track_duration
            self.seek_to(target_sec)

    def on_slider_change(self, value):
        if self.is_user_scrubbing and self.track_duration > 0:
            sec = (float(value) / 100.0) * self.track_duration
            self.time_elapsed_label.configure(text=format_time(sec))

    def on_speed_change(self, speed_str):
        """Changes playback speed (e.g. 1.25x) seamlessly in real time without restarting."""
        try:
            val = float(speed_str.replace("x", ""))
            self.playback_speed = val
            if self.native_player:
                self.native_player.setRate_(self.playback_speed)
                if self.is_playing and not self.is_paused:
                    self.native_player.play()
            elif self.is_playing and not self.is_paused:
                current_pos = self.track_position
                self.play_chapter(self.current_index, start_offset=current_pos)

            if self.book_id:
                db_update.update_book_audio_speed(self.book_id, self.playback_speed)
        except Exception as e:
            print("Error changing speed:", e)

    def on_volume_change(self, value):
        """Updates volume setting (0.0 to 1.0) in real time."""
        self.volume = max(0.0, min(1.0, float(value) / 100.0))
        if self.native_player:
            try:
                self.native_player.setVolume_(self.volume)
            except Exception as e:
                print("Error updating volume:", e)

    def _start_progress_loop(self):
        """Periodic loop to update elapsed time label, progress bar, and autosave progress."""
        self._last_save_time = time.time()

        def _update():
            if self.winfo_exists():
                if self.is_playing and not self.is_paused and not self.is_user_scrubbing:
                    if self.native_player:
                        pos = float(self.native_player.currentTime())
                        self.track_position = pos
                        self.time_elapsed_label.configure(text=format_time(pos))
                        if self.track_duration > 0:
                            pct = min(100.0, (pos / self.track_duration) * 100.0)
                            self.progress_slider.set(pct)

                        if not self.native_player.isPlaying():
                            # Track finished naturally
                            self._on_chapter_finished(self.current_index)
                    else:
                        elapsed = self.play_start_offset + (time.time() - self.play_start_time) * self.playback_speed
                        self.track_position = elapsed
                        self.time_elapsed_label.configure(text=format_time(elapsed))
                        if self.track_duration > 0:
                            pct = min(100.0, (elapsed / self.track_duration) * 100.0)
                            self.progress_slider.set(pct)

                    now = time.time()
                    if now - self._last_save_time >= 5.0:
                        self._last_save_time = now
                        self.save_progress()

                self.after(200, _update)

        self.after(200, _update)

    def cleanup(self):
        """Stops all background processes and threads, saving progress."""
        self.stop()
