import sys
import os
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

from db.config import DB_NAME
from db import db_get, db_update
from windows.settings_helpers.backup_database import backup_database, quick_backup_database
from windows.settings_helpers.import_database import import_database
from windows.settings_helpers.import_excel import import_excel_workbook
from windows.settings_helpers.cover_fetcher import batch_fetch_covers_for_missing, fetch_cover_by_isbn


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / DB_NAME if not Path(DB_NAME).is_absolute() else Path(DB_NAME)


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app.root)

        self.withdraw()
        self.app = app

        self.title("Settings & Preferences")
        self.center_on_parent(app.root, 620, 700)
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.batch_fetch_running = False
        self.batch_fetch_cancelled = False

        # Style dictionary
        self.card_style = {
            "fg_color": "#21262d",
            "corner_radius": 8,
            "border_width": 1,
            "border_color": "#30363d"
        }

        # -------------------------------------------------------------
        # Header Banner
        # -------------------------------------------------------------
        header_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=0, height=65)
        header_frame.pack(side="top", fill="x", anchor="n")
        header_frame.pack_propagate(False)

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=16, pady=10)

        title_label = ctk.CTkLabel(
            title_box,
            text="Application Settings",
            font=("Arial", 16, "bold"),
            text_color="#f0f6fc"
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_box,
            text="Database management, author & series editing, and preferences",
            font=("Arial", 11),
            text_color="#8b949e"
        )
        subtitle_label.pack(anchor="w")

        # -------------------------------------------------------------
        # Footer Action Bar (built first so status_label is available)
        # -------------------------------------------------------------
        footer_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=0, height=45)
        footer_frame.pack(side="bottom", fill="x")
        footer_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            footer_frame,
            text="Ready",
            font=("Arial", 11),
            text_color="#8b949e"
        )
        self.status_label.pack(side="left", padx=16, pady=8)

        close_btn = ctk.CTkButton(
            footer_frame,
            text="Close",
            width=80,
            height=28,
            fg_color="#30363d",
            hover_color="#484f58",
            font=("Arial", 12),
            command=self.on_close
        )
        close_btn.pack(side="right", padx=16, pady=8)

        # -------------------------------------------------------------
        # Main Tabview
        # -------------------------------------------------------------
        self.tabview = ctk.CTkTabview(
            self,
            fg_color="#0d1117",
            segmented_button_fg_color="#161b22",
            segmented_button_selected_color="#1f6feb",
            segmented_button_selected_hover_color="#388bfd",
            segmented_button_unselected_color="#21262d",
            segmented_button_unselected_hover_color="#30363d",
            corner_radius=8
        )
        self.tabview.pack(fill="both", expand=True, padx=14, pady=(6, 4))

        self.db_tab = self.tabview.add("Database")
        self.authors_series_tab = self.tabview.add("Authors & Series")
        self.import_tab = self.tabview.add("Import Data")
        self.appearance_tab = self.tabview.add("Appearance")
        self.about_tab = self.tabview.add("About")

        self.build_database_tab()
        self.build_authors_series_tab()
        self.build_import_tab()
        self.build_appearance_tab()
        self.build_about_tab()

        self.deiconify()

    # =========================================================================
    # TAB 1: DATABASE MANAGEMENT
    # =========================================================================
    def build_database_tab(self):
        tab = self.db_tab

        # Card 1: Overview & Statistics
        stats_card = ctk.CTkFrame(tab, **self.card_style)
        stats_card.pack(fill="x", padx=4, pady=6)

        header_row = ctk.CTkFrame(stats_card, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            header_row,
            text="Database Status & Statistics",
            font=("Arial", 13, "bold"),
            text_color="#f0f6fc"
        ).pack(side="left")

        refresh_btn = ctk.CTkButton(
            header_row,
            text="Refresh",
            width=60,
            height=22,
            font=("Arial", 11),
            fg_color="#21262d",
            hover_color="#30363d",
            border_width=1,
            border_color="#30363d",
            command=self.refresh_stats
        )
        refresh_btn.pack(side="right")

        # Stat Badges Grid
        self.stats_grid = ctk.CTkFrame(stats_card, fg_color="transparent")
        self.stats_grid.pack(fill="x", padx=12, pady=6)
        for i in range(3):
            self.stats_grid.columnconfigure(i, weight=1)

        self.stat_labels = {}
        items = [
            ("Books", "books", 0, 0),
            ("Authors", "authors", 0, 1),
            ("Series", "series", 0, 2),
            ("Genres", "genres", 1, 0),
            ("Topics", "topics", 1, 1),
            ("File Size", "size", 1, 2),
        ]

        for label_text, key, row, col in items:
            tile = ctk.CTkFrame(self.stats_grid, fg_color="#161b22", corner_radius=6, border_width=1, border_color="#30363d")
            tile.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            val_lbl = ctk.CTkLabel(tile, text="--", font=("Arial", 14, "bold"), text_color="#58a6ff")
            val_lbl.pack(pady=(4, 0))

            sub_lbl = ctk.CTkLabel(tile, text=label_text, font=("Arial", 10), text_color="#8b949e")
            sub_lbl.pack(pady=(0, 4))

            self.stat_labels[key] = val_lbl

        # Card 2: Backup and Restore Operations
        ops_card = ctk.CTkFrame(tab, **self.card_style)
        ops_card.pack(fill="x", padx=4, pady=6)

        ctk.CTkLabel(
            ops_card,
            text="Backup & Restore",
            font=("Arial", 13, "bold"),
            text_color="#f0f6fc"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            ops_card,
            text="Safely duplicate or restore your SQLite database records.",
            font=("Arial", 11),
            text_color="#8b949e"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        btn_row = ctk.CTkFrame(ops_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 10))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)
        btn_row.columnconfigure(2, weight=1)

        backup_btn = ctk.CTkButton(
            btn_row,
            text="Save Backup...",
            font=("Arial", 12, "bold"),
            fg_color="#1f6feb",
            hover_color="#388bfd",
            height=32,
            command=self.handle_backup
        )
        backup_btn.grid(row=0, column=0, padx=4, sticky="ew")

        quick_backup_btn = ctk.CTkButton(
            btn_row,
            text="Quick Snapshot",
            font=("Arial", 12),
            fg_color="#21262d",
            hover_color="#30363d",
            border_width=1,
            border_color="#30363d",
            height=32,
            command=self.handle_quick_backup
        )
        quick_backup_btn.grid(row=0, column=1, padx=4, sticky="ew")

        restore_btn = ctk.CTkButton(
            btn_row,
            text="Restore Backup...",
            font=("Arial", 12),
            fg_color="#8957e5",
            hover_color="#a371f7",
            height=32,
            command=self.handle_restore
        )
        restore_btn.grid(row=0, column=2, padx=4, sticky="ew")

        # Card 3: Database Optimization
        maint_card = ctk.CTkFrame(tab, **self.card_style)
        maint_card.pack(fill="x", padx=4, pady=6)

        maint_row = ctk.CTkFrame(maint_card, fg_color="transparent")
        maint_row.pack(fill="x", padx=12, pady=10)

        maint_text_box = ctk.CTkFrame(maint_row, fg_color="transparent")
        maint_text_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            maint_text_box,
            text="Database Optimization",
            font=("Arial", 13, "bold"),
            text_color="#f0f6fc"
        ).pack(anchor="w")

        ctk.CTkLabel(
            maint_text_box,
            text="Defragment SQLite file, rebuild query indexes, and reclaim space.",
            font=("Arial", 11),
            text_color="#8b949e"
        ).pack(anchor="w")

        vacuum_btn = ctk.CTkButton(
            maint_row,
            text="Optimize (Vacuum)",
            font=("Arial", 11),
            width=140,
            height=30,
            fg_color="#238636",
            hover_color="#2ea043",
            command=self.handle_optimize
        )
        vacuum_btn.pack(side="right", padx=(8, 0))

        self.refresh_stats()

    # =========================================================================
    # TAB 2: AUTHORS & SERIES MANAGEMENT
    # =========================================================================
    def build_authors_series_tab(self):
        tab = self.authors_series_tab

        self.author_display_to_id = {}
        self.author_id_to_obj = {}
        self.author_id_to_display = {}
        self.series_display_to_id = {}
        self.series_id_to_obj = {}
        self.series_id_to_display = {}

        # Top Mode Switcher Card
        top_card = ctk.CTkFrame(tab, **self.card_style)
        top_card.pack(fill="x", padx=4, pady=6)

        top_row = ctk.CTkFrame(top_card, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=10)

        info_box = ctk.CTkFrame(top_row, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            info_box,
            text="Author & Series Editor",
            font=("Arial", 13, "bold"),
            text_color="#f0f6fc"
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_box,
            text="Edit existing author names and series titles across your library.",
            font=("Arial", 11),
            text_color="#8b949e"
        ).pack(anchor="w")

        self.as_mode_var = ctk.StringVar(value="Authors")
        self.as_mode_segment = ctk.CTkSegmentedButton(
            top_row,
            values=["Authors", "Series"],
            variable=self.as_mode_var,
            command=self.switch_authors_series_view,
            fg_color="#161b22",
            selected_color="#1f6feb",
            selected_hover_color="#388bfd",
            unselected_color="#21262d",
            unselected_hover_color="#30363d",
            font=("Arial", 11, "bold"),
            width=150,
            height=28
        )
        self.as_mode_segment.pack(side="right", padx=(10, 0))

        # Container for sub-views
        self.as_content_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.as_content_frame.pack(fill="both", expand=True, padx=4, pady=2)

        self.author_subframe = ctk.CTkFrame(self.as_content_frame, fg_color="transparent")
        self.series_subframe = ctk.CTkFrame(self.as_content_frame, fg_color="transparent")

        self.build_author_editor()
        self.build_series_editor()

        # Initial display
        self.switch_authors_series_view("Authors")

    def build_author_editor(self):
        parent = self.author_subframe

        # 1. Author Selection Card
        sel_card = ctk.CTkFrame(parent, **self.card_style)
        sel_card.pack(fill="x", pady=(0, 6))

        sel_header = ctk.CTkFrame(sel_card, fg_color="transparent")
        sel_header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            sel_header,
            text="Select Author to Edit",
            font=("Arial", 13, "bold"),
            text_color="#f0f6fc"
        ).pack(side="left")

        reload_btn = ctk.CTkButton(
            sel_header,
            text="Reload",
            width=60,
            height=22,
            font=("Arial", 11),
            fg_color="#21262d",
            hover_color="#30363d",
            border_width=1,
            border_color="#30363d",
            command=self.refresh_authors_dropdown
        )
        reload_btn.pack(side="right")

        sel_body = ctk.CTkFrame(sel_card, fg_color="transparent")
        sel_body.pack(fill="x", padx=12, pady=(4, 12))

        self.author_select_var = ctk.StringVar()
        self.author_select_combo = ctk.CTkComboBox(
            sel_body,
            variable=self.author_select_var,
            values=["Loading..."],
            command=self.on_author_selected,
            font=("Arial", 12),
            dropdown_font=("Arial", 12),
            height=32,
            corner_radius=6
        )
        self.author_select_combo.pack(fill="x")

        # 2. Author Details & Edit Card
        edit_card = ctk.CTkFrame(parent, **self.card_style)
        edit_card.pack(fill="both", expand=True, pady=(0, 6))

        ctk.CTkLabel(
            edit_card,
            text="Edit Author Details",
            font=("Arial", 13, "bold"),
            text_color="#f0f6fc"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            edit_card,
            text="Changes will update author metadata across all associated books and series.",
            font=("Arial", 11),
            text_color="#8b949e"
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Fields Form Grid
        form_frame = ctk.CTkFrame(edit_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=12, pady=4)
        form_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="First Name:", font=("Arial", 12, "bold"), text_color="#f0f6fc", anchor="w").grid(row=0, column=0, padx=(0, 10), pady=6, sticky="w")
        self.author_first_entry = ctk.CTkEntry(form_frame, font=("Arial", 12), height=32, corner_radius=6)
        self.author_first_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(form_frame, text="Last Name:", font=("Arial", 12, "bold"), text_color="#f0f6fc", anchor="w").grid(row=1, column=0, padx=(0, 10), pady=6, sticky="w")
        self.author_last_entry = ctk.CTkEntry(form_frame, font=("Arial", 12), height=32, corner_radius=6)
        self.author_last_entry.grid(row=1, column=1, sticky="ew", pady=6)

        # Author Metrics Badges
        metrics_frame = ctk.CTkFrame(edit_card, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=12, pady=8)
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)

        b_tile = ctk.CTkFrame(metrics_frame, fg_color="#161b22", corner_radius=6, border_width=1, border_color="#30363d")
        b_tile.grid(row=0, column=0, padx=(0, 4), sticky="nsew")
        self.author_books_badge = ctk.CTkLabel(b_tile, text="0 Books", font=("Arial", 12, "bold"), text_color="#58a6ff")
        self.author_books_badge.pack(pady=6)

        s_tile = ctk.CTkFrame(metrics_frame, fg_color="#161b22", corner_radius=6, border_width=1, border_color="#30363d")
        s_tile.grid(row=0, column=1, padx=(4, 0), sticky="nsew")
        self.author_series_badge = ctk.CTkLabel(s_tile, text="0 Series", font=("Arial", 12, "bold"), text_color="#a371f7")
        self.author_series_badge.pack(pady=6)

        # Feedback message
        self.author_feedback_label = ctk.CTkLabel(
            edit_card,
            text="",
            font=("Arial", 11),
            text_color="#3fb950"
        )
        self.author_feedback_label.pack(anchor="w", padx=12, pady=(2, 6))

        # Action Buttons Row
        btn_row = ctk.CTkFrame(edit_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 6))
        btn_row.columnconfigure(0, weight=2)
        btn_row.columnconfigure(1, weight=1)

        self.save_author_btn = ctk.CTkButton(
            btn_row,
            text="Save Author Name",
            font=("Arial", 12, "bold"),
            fg_color="#1f6feb",
            hover_color="#388bfd",
            height=34,
            command=self.save_author_changes
        )
        self.save_author_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        revert_author_btn = ctk.CTkButton(
            btn_row,
            text="Reset",
            font=("Arial", 12),
            fg_color="#21262d",
            hover_color="#30363d",
            border_width=1,
            border_color="#30363d",
            height=34,
            command=self.revert_author_changes
        )
        revert_author_btn.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # Merge Duplicates Button
        self.merge_authors_btn = ctk.CTkButton(
            edit_card,
            text="Combine & Merge Duplicate Authors",
            font=("Arial", 11, "bold"),
            fg_color="#238636",
            hover_color="#2ea043",
            height=30,
            command=self.handle_merge_duplicate_authors
        )
        self.merge_authors_btn.pack(fill="x", padx=12, pady=(0, 12))

    def build_series_editor(self):
        parent = self.series_subframe

        # 1. Series Selection Card
        sel_card = ctk.CTkFrame(parent, **self.card_style)
        sel_card.pack(fill="x", pady=(0, 6))

        sel_header = ctk.CTkFrame(sel_card, fg_color="transparent")
        sel_header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            sel_header,
            text="Select Series to Edit",
            font=("Arial", 13, "bold"),
            text_color="#f0f6fc"
        ).pack(side="left")

        reload_btn = ctk.CTkButton(
            sel_header,
            text="Reload",
            width=60,
            height=22,
            font=("Arial", 11),
            fg_color="#21262d",
            hover_color="#30363d",
            border_width=1,
            border_color="#30363d",
            command=self.refresh_series_dropdown
        )
        reload_btn.pack(side="right")

        sel_body = ctk.CTkFrame(sel_card, fg_color="transparent")
        sel_body.pack(fill="x", padx=12, pady=(4, 12))

        self.series_select_var = ctk.StringVar()
        self.series_select_combo = ctk.CTkComboBox(
            sel_body,
            variable=self.series_select_var,
            values=["Loading..."],
            command=self.on_series_selected,
            font=("Arial", 12),
            dropdown_font=("Arial", 12),
            height=32,
            corner_radius=6
        )
        self.series_select_combo.pack(fill="x")

        # 2. Series Details & Edit Card
        edit_card = ctk.CTkFrame(parent, **self.card_style)
        edit_card.pack(fill="both", expand=True, pady=(0, 6))

        ctk.CTkLabel(
            edit_card,
            text="Edit Series Details",
            font=("Arial", 13, "bold"),
            text_color="#f0f6fc"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            edit_card,
            text="Update series title or reassign its primary author association.",
            font=("Arial", 11),
            text_color="#8b949e"
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Fields Form Grid
        form_frame = ctk.CTkFrame(edit_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=12, pady=4)
        form_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="Series Title:", font=("Arial", 12, "bold"), text_color="#f0f6fc", anchor="w").grid(row=0, column=0, padx=(0, 10), pady=6, sticky="w")
        self.series_title_entry = ctk.CTkEntry(form_frame, font=("Arial", 12), height=32, corner_radius=6)
        self.series_title_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(form_frame, text="Author:", font=("Arial", 12, "bold"), text_color="#f0f6fc", anchor="w").grid(row=1, column=0, padx=(0, 10), pady=6, sticky="w")
        self.series_author_var = ctk.StringVar()
        self.series_author_combo = ctk.CTkComboBox(
            form_frame,
            variable=self.series_author_var,
            values=["(None)"],
            font=("Arial", 12),
            dropdown_font=("Arial", 12),
            height=32,
            corner_radius=6
        )
        self.series_author_combo.grid(row=1, column=1, sticky="ew", pady=6)

        # Series Metrics Badges
        metrics_frame = ctk.CTkFrame(edit_card, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=12, pady=8)
        metrics_frame.columnconfigure(0, weight=1)

        b_tile = ctk.CTkFrame(metrics_frame, fg_color="#161b22", corner_radius=6, border_width=1, border_color="#30363d")
        b_tile.grid(row=0, column=0, padx=0, sticky="nsew")
        self.series_books_badge = ctk.CTkLabel(b_tile, text="0 Books in Series", font=("Arial", 12, "bold"), text_color="#58a6ff")
        self.series_books_badge.pack(pady=6)

        # Feedback message
        self.series_feedback_label = ctk.CTkLabel(
            edit_card,
            text="",
            font=("Arial", 11),
            text_color="#3fb950"
        )
        self.series_feedback_label.pack(anchor="w", padx=12, pady=(2, 6))

        # Action Buttons Row
        btn_row = ctk.CTkFrame(edit_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 12))
        btn_row.columnconfigure(0, weight=2)
        btn_row.columnconfigure(1, weight=1)

        self.save_series_btn = ctk.CTkButton(
            btn_row,
            text="Save Series Title",
            font=("Arial", 12, "bold"),
            fg_color="#1f6feb",
            hover_color="#388bfd",
            height=34,
            command=self.save_series_changes
        )
        self.save_series_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        revert_series_btn = ctk.CTkButton(
            btn_row,
            text="Reset",
            font=("Arial", 12),
            fg_color="#21262d",
            hover_color="#30363d",
            border_width=1,
            border_color="#30363d",
            height=34,
            command=self.revert_series_changes
        )
        revert_series_btn.grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def switch_authors_series_view(self, mode):
        if mode == "Authors":
            self.series_subframe.pack_forget()
            self.author_subframe.pack(fill="both", expand=True)
            self.load_authors_data()
        else:
            self.author_subframe.pack_forget()
            self.series_subframe.pack(fill="both", expand=True)
            self.load_series_data()

    def refresh_authors_dropdown(self):
        curr_id = self.current_selected_author_id()
        self.load_authors_data(selected_id=curr_id)
        self.status_label.configure(text="Author records refreshed.")

    def refresh_series_dropdown(self):
        curr_id = self.current_selected_series_id()
        self.load_series_data(selected_id=curr_id)
        self.status_label.configure(text="Series records refreshed.")

    def current_selected_author_id(self):
        disp = self.author_select_var.get()
        return self.author_display_to_id.get(disp)

    def current_selected_series_id(self):
        disp = self.series_select_var.get()
        return self.series_display_to_id.get(disp)

    def load_authors_data(self, selected_id=None):
        self.author_display_to_id = {}
        self.author_id_to_obj = {}
        self.author_id_to_display = {}

        authors = db_get.get_authors()
        if not authors:
            self.author_select_combo.configure(values=["(No authors in database)"])
            self.author_select_var.set("(No authors in database)")
            self.author_first_entry.delete(0, tk.END)
            self.author_last_entry.delete(0, tk.END)
            self.author_books_badge.configure(text="0 Books")
            self.author_series_badge.configure(text="0 Series")
            self.author_feedback_label.configure(text="")
            return

        names_seen = set()
        duplicate_names = set()
        for aid, first, last in authors:
            full = f"{first} {last}".strip()
            if full in names_seen:
                duplicate_names.add(full)
            names_seen.add(full)

        display_values = []
        for aid, first, last in authors:
            full = f"{first} {last}".strip()
            disp = f"{full} (ID: {aid})" if full in duplicate_names else full
            self.author_display_to_id[disp] = aid
            self.author_id_to_obj[aid] = (first, last)
            self.author_id_to_display[aid] = disp
            display_values.append(disp)

        self.author_select_combo.configure(values=display_values)
        if hasattr(self, "series_author_combo"):
            self.series_author_combo.configure(values=display_values)

        target_disp = None
        if selected_id is not None and selected_id in self.author_id_to_display:
            target_disp = self.author_id_to_display[selected_id]
        elif display_values:
            target_disp = display_values[0]

        if target_disp:
            self.author_select_var.set(target_disp)
            self.on_author_selected(target_disp)

    def on_author_selected(self, choice):
        self.author_feedback_label.configure(text="")
        author_id = self.author_display_to_id.get(choice)
        if author_id is None:
            return

        first, last = self.author_id_to_obj.get(author_id, ("", ""))
        self.author_first_entry.delete(0, tk.END)
        self.author_first_entry.insert(0, first if first is not None else "")
        self.author_last_entry.delete(0, tk.END)
        self.author_last_entry.insert(0, last if last is not None else "")

        stats = db_get.get_author_stats(author_id)
        book_count = stats.get("books", 0)
        series_count = stats.get("series", 0)
        self.author_books_badge.configure(text=f"{book_count} {'Book' if book_count == 1 else 'Books'}")
        self.author_series_badge.configure(text=f"{series_count} Series")

    def revert_author_changes(self):
        disp = self.author_select_var.get()
        if disp:
            self.on_author_selected(disp)
            self.author_feedback_label.configure(text="Reverted unsaved edits.", text_color="#8b949e")

    def save_author_changes(self):
        author_id = self.current_selected_author_id()
        if author_id is None:
            self.author_feedback_label.configure(text="Please select an author first.", text_color="#f85149")
            return

        new_first = self.author_first_entry.get().strip()
        new_last = self.author_last_entry.get().strip()

        if not new_first and not new_last:
            self.author_feedback_label.configure(text="Author name cannot be completely blank.", text_color="#f85149")
            return

        res = db_update.update_author(author_id, new_first, new_last)
        if res == "success":
            self.load_authors_data(selected_id=author_id)
            self.author_feedback_label.configure(text=f"Author updated to '{new_first} {new_last}'!", text_color="#3fb950")
            self.refresh_stats(custom_status=f"Updated author: {new_first} {new_last}")

            # Notify / refresh application views
            if hasattr(self.app, "load_books"):
                self.app.load_books()
            if hasattr(self.app, "load_authors_into_filter"):
                self.app.load_authors_into_filter()
            if hasattr(self.app, "add_window") and self.app.add_window is not None and self.app.add_window.winfo_exists():
                if hasattr(self.app.add_window, "refresh_book_tab_authors"):
                    self.app.add_window.refresh_book_tab_authors()
                if hasattr(self.app.add_window, "refresh_series_tab_authors"):
                    self.app.add_window.refresh_series_tab_authors()
        else:
            self.author_feedback_label.configure(text=f"Error updating author: {res}", text_color="#f85149")

    def handle_merge_duplicate_authors(self):
        try:
            res = db_update.combine_duplicate_authors(DB_NAME)
            merged = res.get("merged_authors", 0)
            reassigned = res.get("reassigned_books", 0)
            if merged > 0:
                msg = f"Merged {merged} duplicate authors and combined {reassigned} books!"
            else:
                msg = "No duplicate author entries found. All authors are unified!"

            self.load_authors_data()
            self.refresh_stats(custom_status=msg)
            self.author_feedback_label.configure(text=msg, text_color="#3fb950")

            if hasattr(self.app, "load_books"):
                self.app.load_books()
            if hasattr(self.app, "load_authors_into_filter"):
                self.app.load_authors_into_filter()
            if hasattr(self.app, "add_window") and self.app.add_window is not None and self.app.add_window.winfo_exists():
                if hasattr(self.app.add_window, "refresh_book_tab_authors"):
                    self.app.add_window.refresh_book_tab_authors()
                if hasattr(self.app.add_window, "refresh_series_tab_authors"):
                    self.app.add_window.refresh_series_tab_authors()
        except Exception as e:
            self.author_feedback_label.configure(text=f"Error merging authors: {e}", text_color="#f85149")

    def load_series_data(self, selected_id=None):
        self.series_display_to_id = {}
        self.series_id_to_obj = {}
        self.series_id_to_display = {}

        # Also ensure author list for series_author_combo is updated
        authors = db_get.get_authors()
        author_display_values = []
        self.author_display_to_id = {}
        self.author_id_to_display = {}
        names_seen = set()
        duplicate_names = set()
        for aid, first, last in authors:
            full = f"{first} {last}".strip()
            if full in names_seen:
                duplicate_names.add(full)
            names_seen.add(full)
        for aid, first, last in authors:
            full = f"{first} {last}".strip()
            disp = f"{full} (ID: {aid})" if full in duplicate_names else full
            self.author_display_to_id[disp] = aid
            self.author_id_to_display[aid] = disp
            author_display_values.append(disp)

        self.series_author_combo.configure(values=author_display_values if author_display_values else ["(None)"])

        series_list = db_get.get_all_series()
        if not series_list:
            self.series_select_combo.configure(values=["(No series in database)"])
            self.series_select_var.set("(No series in database)")
            self.series_title_entry.delete(0, tk.END)
            self.series_author_var.set("(None)")
            self.series_books_badge.configure(text="0 Books in Series")
            self.series_feedback_label.configure(text="")
            return

        s_names_seen = set()
        s_duplicates = set()
        for sid, title, aid, afirst, alast in series_list:
            author_str = f" ({afirst} {alast})".strip() if afirst or alast else ""
            base = f"{title}{author_str}"
            if base in s_names_seen:
                s_duplicates.add(base)
            s_names_seen.add(base)

        display_values = []
        for sid, title, aid, afirst, alast in series_list:
            author_str = f" ({afirst} {alast})" if (afirst or alast) else ""
            base = f"{title}{author_str}"
            disp = f"{base} [ID: {sid}]" if base in s_duplicates else base
            self.series_display_to_id[disp] = sid
            self.series_id_to_obj[sid] = (title, aid, afirst, alast)
            self.series_id_to_display[sid] = disp
            display_values.append(disp)

        self.series_select_combo.configure(values=display_values)

        target_disp = None
        if selected_id is not None and selected_id in self.series_id_to_display:
            target_disp = self.series_id_to_display[selected_id]
        elif display_values:
            target_disp = display_values[0]

        if target_disp:
            self.series_select_var.set(target_disp)
            self.on_series_selected(target_disp)

    def on_series_selected(self, choice):
        self.series_feedback_label.configure(text="")
        series_id = self.series_display_to_id.get(choice)
        if series_id is None:
            return

        title, aid, afirst, alast = self.series_id_to_obj.get(series_id, ("", None, "", ""))
        self.series_title_entry.delete(0, tk.END)
        self.series_title_entry.insert(0, title if title is not None else "")

        if aid is not None and aid in self.author_id_to_display:
            self.series_author_var.set(self.author_id_to_display[aid])
        else:
            self.series_author_var.set("(None)")

        stats = db_get.get_series_stats(series_id)
        book_count = stats.get("books", 0)
        self.series_books_badge.configure(text=f"{book_count} {'Book' if book_count == 1 else 'Books'} in Series")

    def revert_series_changes(self):
        disp = self.series_select_var.get()
        if disp:
            self.on_series_selected(disp)
            self.series_feedback_label.configure(text="Reverted unsaved edits.", text_color="#8b949e")

    def save_series_changes(self):
        series_id = self.current_selected_series_id()
        if series_id is None:
            self.series_feedback_label.configure(text="Please select a series first.", text_color="#f85149")
            return

        new_title = self.series_title_entry.get().strip()
        if not new_title:
            self.series_feedback_label.configure(text="Series title cannot be blank.", text_color="#f85149")
            return

        author_disp = self.series_author_var.get()
        new_author_id = self.author_display_to_id.get(author_disp)

        res = db_update.update_series(series_id, new_title, new_author_id)
        if res == "success":
            self.load_series_data(selected_id=series_id)
            self.series_feedback_label.configure(text=f"Series updated to '{new_title}'!", text_color="#3fb950")
            self.refresh_stats(custom_status=f"Updated series: {new_title}")

            # Notify / refresh application views
            if hasattr(self.app, "load_books"):
                self.app.load_books()
        else:
            self.series_feedback_label.configure(text=f"Error updating series: {res}", text_color="#f85149")

    # =========================================================================
    # TAB 3: DATA IMPORT & COVERS
    # =========================================================================
    def build_import_tab(self):
        tab = self.import_tab

        # Card 1: Automatic ISBN Book Cover Retrieval
        cover_card = ctk.CTkFrame(tab, **self.card_style)
        cover_card.pack(fill="x", padx=4, pady=(6, 4))

        ctk.CTkLabel(
            cover_card,
            text="Automatic ISBN Book Cover Retrieval",
            font=("Arial", 14, "bold"),
            text_color="#f0f6fc"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            cover_card,
            text="Search online APIs (Open Library & Google Books) and download cover artwork for all books with an ISBN.",
            font=("Arial", 11),
            text_color="#8b949e"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Status & Count Row
        stat_box = ctk.CTkFrame(cover_card, fg_color="#161b22", corner_radius=6, border_width=1, border_color="#30363d")
        stat_box.pack(fill="x", padx=12, pady=4)

        stat_row = ctk.CTkFrame(stat_box, fg_color="transparent")
        stat_row.pack(fill="x", padx=10, pady=6)

        self.missing_covers_label = ctk.CTkLabel(
            stat_row,
            text="Checking books missing cover images...",
            font=("Arial", 11, "bold"),
            text_color="#58a6ff",
            anchor="w"
        )
        self.missing_covers_label.pack(side="left", fill="x", expand=True)

        self.refresh_covers_btn = ctk.CTkButton(
            stat_row,
            text="Check",
            width=55,
            height=22,
            font=("Arial", 11),
            fg_color="#21262d",
            hover_color="#30363d",
            border_width=1,
            border_color="#30363d",
            command=self.refresh_covers_stat
        )
        self.refresh_covers_btn.pack(side="right")

        # Progress elements
        self.cover_progress_bar = ctk.CTkProgressBar(cover_card, height=10, corner_radius=4)
        self.cover_progress_bar.pack(fill="x", padx=12, pady=(8, 2))
        self.cover_progress_bar.set(0)

        self.cover_progress_label = ctk.CTkLabel(
            cover_card,
            text="Ready to search and download missing covers.",
            font=("Arial", 10),
            text_color="#8b949e",
            anchor="w"
        )
        self.cover_progress_label.pack(anchor="w", padx=12, pady=(0, 6))

        # Cover Action Buttons
        c_btn_row = ctk.CTkFrame(cover_card, fg_color="transparent")
        c_btn_row.pack(fill="x", padx=12, pady=(0, 10))
        c_btn_row.columnconfigure(0, weight=3)
        c_btn_row.columnconfigure(1, weight=1)

        self.batch_fetch_covers_btn = ctk.CTkButton(
            c_btn_row,
            text="Fetch Missing Covers Online",
            font=("Arial", 12, "bold"),
            fg_color="#1f6feb",
            hover_color="#388bfd",
            height=32,
            command=self.handle_batch_cover_fetch
        )
        self.batch_fetch_covers_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.cancel_fetch_covers_btn = ctk.CTkButton(
            c_btn_row,
            text="Stop",
            font=("Arial", 12),
            fg_color="#cf222e",
            hover_color="#f85149",
            height=32,
            state="disabled",
            command=self.cancel_batch_cover_fetch
        )
        self.cancel_fetch_covers_btn.grid(row=0, column=1, sticky="ew")

        # Card 2: Excel Workbook Import (.xlsx, .xlsm)
        excel_card = ctk.CTkFrame(tab, **self.card_style)
        excel_card.pack(fill="both", expand=True, padx=4, pady=(4, 6))

        ctk.CTkLabel(
            excel_card,
            text="Excel Workbook Import (.xlsx, .xlsm)",
            font=("Arial", 14, "bold"),
            text_color="#f0f6fc"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            excel_card,
            text="Import books, authors, series, and genres in bulk from spreadsheet files.",
            font=("Arial", 11),
            text_color="#8b949e"
        ).pack(anchor="w", padx=12, pady=(0, 6))

        # Column Layout Specification Box
        spec_box = ctk.CTkFrame(excel_card, fg_color="#161b22", corner_radius=6, border_width=1, border_color="#30363d")
        spec_box.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            spec_box,
            text="Expected Spreadsheet Column Format:",
            font=("Arial", 11, "bold"),
            text_color="#58a6ff"
        ).pack(anchor="w", padx=10, pady=(6, 2))

        col_items = [
            ("Column A:", "Author Name (e.g. 'Brandon Sanderson')"),
            ("Column B:", "Series Title (optional, linked to author)"),
            ("Column C:", "Number in Series (optional, applied when Series is present)"),
            ("Column D:", "Book Title (required)"),
            ("Column F:", "NLS Order Code (optional)"),
            ("Column H:", "Genre Name (optional, defaults to 'None' if blank)"),
        ]

        for col_name, col_desc in col_items:
            row = ctk.CTkFrame(spec_box, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=1)

            ctk.CTkLabel(row, text=col_name, width=80, font=("Arial", 10, "bold"), text_color="#f0f6fc", anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=col_desc, font=("Arial", 10), text_color="#8b949e", anchor="w").pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            spec_box,
            text="* Note: The first row is treated as headers and automatically skipped. Relational multi-sheet workbooks are also supported.",
            font=("Arial", 9, "italic"),
            text_color="#8b949e"
        ).pack(anchor="w", padx=10, pady=(4, 6))

        # Import action button
        import_btn = ctk.CTkButton(
            excel_card,
            text="Choose Excel File and Import",
            font=("Arial", 12, "bold"),
            fg_color="#238636",
            hover_color="#2ea043",
            height=34,
            command=self.handle_excel_import
        )
        import_btn.pack(fill="x", padx=12, pady=(8, 10))

        self.refresh_covers_stat()

    # =========================================================================
    # TAB 3: APPEARANCE
    # =========================================================================
    def build_appearance_tab(self):
        tab = self.appearance_tab

        theme_card = ctk.CTkFrame(tab, **self.card_style)
        theme_card.pack(fill="x", padx=4, pady=6)

        ctk.CTkLabel(
            theme_card,
            text="Interface Appearance",
            font=("Arial", 13, "bold"),
            text_color="#f0f6fc"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            theme_card,
            text="Customize the visual theme and contrast mode of the application.",
            font=("Arial", 11),
            text_color="#8b949e"
        ).pack(anchor="w", padx=12, pady=(0, 10))

        mode_row = ctk.CTkFrame(theme_card, fg_color="transparent")
        mode_row.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(mode_row, text="Theme Mode:", font=("Arial", 12), text_color="#f0f6fc").pack(side="left", padx=(0, 10))

        current_mode = ctk.get_appearance_mode()
        self.mode_var = ctk.StringVar(value=current_mode)

        self.theme_segment = ctk.CTkSegmentedButton(
            mode_row,
            values=["Dark", "Light", "System"],
            variable=self.mode_var,
            command=self.change_appearance_mode
        )
        self.theme_segment.pack(side="left")

        # Shortcuts Guide Card
        tips_card = ctk.CTkFrame(tab, **self.card_style)
        tips_card.pack(fill="both", expand=True, padx=4, pady=6)

        ctk.CTkLabel(
            tips_card,
            text="Productivity & Navigation Tips",
            font=("Arial", 13, "bold"),
            text_color="#f0f6fc"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        tips = [
            ("Click Row", "View complete book details and description."),
            ("Ctrl+A / Cmd+A", "Select all visible books in the table."),
            ("Right-Click", "Open context menu to batch edit or delete rows."),
            ("Edit Selected", "Quickly update genres and topics for multiple books."),
            ("Filters", "Filter books by author, genre, topic, or combinations."),
        ]

        for shortcut, desc in tips:
            row = ctk.CTkFrame(tips_card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)

            ctk.CTkLabel(row, text=f"•  {shortcut}:", width=120, font=("Arial", 11, "bold"), text_color="#58a6ff", anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=desc, font=("Arial", 11), text_color="#8b949e", anchor="w").pack(side="left", fill="x", expand=True)

    # =========================================================================
    # TAB 4: ABOUT & INFORMATION
    # =========================================================================
    def build_about_tab(self):
        tab = self.about_tab

        about_card = ctk.CTkFrame(tab, **self.card_style)
        about_card.pack(fill="both", expand=True, padx=4, pady=6)

        ctk.CTkLabel(
            about_card,
            text="MyBook Manager",
            font=("Arial", 15, "bold"),
            text_color="#f0f6fc"
        ).pack(anchor="w", padx=12, pady=(12, 2))

        ctk.CTkLabel(
            about_card,
            text="Personal library and book cataloging management system.",
            font=("Arial", 11),
            text_color="#8b949e"
        ).pack(anchor="w", padx=12, pady=(0, 12))

        info_rows = [
            ("Application Version", "1.2.0"),
            ("Python Runtime", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"),
            ("SQLite Engine", sqlite3.sqlite_version),
            ("Database Path", str(DB_PATH)),
            ("GUI Framework", "CustomTkinter / Tkinter"),
        ]

        for label_text, value_text in info_rows:
            row = ctk.CTkFrame(about_card, fg_color="#161b22", corner_radius=6, border_width=1, border_color="#30363d")
            row.pack(fill="x", padx=12, pady=4)

            ctk.CTkLabel(row, text=label_text, width=140, font=("Arial", 11, "bold"), text_color="#8b949e", anchor="w").pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=value_text, font=("Arial", 11), text_color="#f0f6fc", anchor="w").pack(side="left", padx=10, pady=6, fill="x", expand=True)

    # =========================================================================
    # ACTIONS & HANDLERS
    # =========================================================================
    def refresh_stats(self, custom_status=None):
        try:
            stats = db_get.get_database_stats()
            self.stat_labels["books"].configure(text=str(stats.get("books", 0)))
            self.stat_labels["authors"].configure(text=str(stats.get("authors", 0)))
            self.stat_labels["series"].configure(text=str(stats.get("series", 0)))
            self.stat_labels["genres"].configure(text=str(stats.get("genres", 0)))
            self.stat_labels["topics"].configure(text=str(stats.get("topics", 0)))

            if DB_PATH.exists():
                size_bytes = os.path.getsize(DB_PATH)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                size_str = "0 KB"

            self.stat_labels["size"].configure(text=size_str)
            if hasattr(self, "missing_covers_label"):
                self.refresh_covers_stat()
            if custom_status:
                self.status_label.configure(text=custom_status)
            else:
                self.status_label.configure(text=f"Database statistics updated at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            self.status_label.configure(text=f"Error reading stats: {e}")

    def refresh_covers_stat(self):
        try:
            count = db_get.get_books_missing_covers_count()
            if hasattr(self, "missing_covers_label"):
                self.missing_covers_label.configure(
                    text=f"{count} {'book' if count == 1 else 'books'} with an ISBN currently {'lacks' if count == 1 else 'lack'} cover artwork."
                )
        except Exception as e:
            print("Error refreshing covers stat:", e)

    def handle_batch_cover_fetch(self):
        if self.batch_fetch_running:
            return

        missing_count = db_get.get_books_missing_covers_count()
        if missing_count == 0:
            messagebox.showinfo(
                "No Missing Covers",
                "All catalog books with an ISBN already have cover images saved in the database.",
                parent=self
            )
            return

        if not messagebox.askyesno(
            "Batch Cover Fetch",
            f"Found {missing_count} books with an ISBN missing cover artwork.\n\nWould you like to search online and download covers now?",
            parent=self
        ):
            return

        self.batch_fetch_running = True
        self.batch_fetch_cancelled = False
        self.batch_fetch_covers_btn.configure(state="disabled")
        self.cancel_fetch_covers_btn.configure(state="normal")
        self.cover_progress_bar.set(0)
        self.cover_progress_label.configure(text=f"Starting cover search (0/{missing_count})...", text_color="#58a6ff")

        def _progress(current, total, title, success, msg):
            def _ui_update():
                progress_val = current / total if total > 0 else 1.0
                self.cover_progress_bar.set(progress_val)
                status_icon = "✓" if success else "✗"
                self.cover_progress_label.configure(
                    text=f"[{current}/{total}] {status_icon} {title[:28]} ({msg})",
                    text_color="#3fb950" if success else "#8b949e"
                )
            self.after(0, _ui_update)

        def _cancel_check():
            return self.batch_fetch_cancelled

        def _worker():
            res = batch_fetch_covers_for_missing(progress_callback=_progress, cancel_check=_cancel_check)

            def _on_finish():
                self.batch_fetch_running = False
                self.batch_fetch_covers_btn.configure(state="normal")
                self.cancel_fetch_covers_btn.configure(state="disabled")
                self.cover_progress_bar.set(1.0 if not self.batch_fetch_cancelled else self.cover_progress_bar.get())
                self.refresh_covers_stat()
                self.refresh_stats(custom_status="Batch cover download finished.")
                if hasattr(self.app, "load_books"):
                    self.app.load_books()

                fetched = res.get("fetched", 0)
                failed = res.get("failed", 0)
                processed = res.get("processed", 0)
                total = res.get("total", 0)
                summary_msg = f"Processed {processed} of {total} books.\n\n• Successfully downloaded & saved: {fetched}\n• Not found or skipped: {failed}"
                if self.batch_fetch_cancelled:
                    summary_msg = f"Batch stopped by user.\n\n" + summary_msg
                self.cover_progress_label.configure(text=f"Done! {fetched} covers retrieved.", text_color="#3fb950")
                messagebox.showinfo("Batch Cover Retrieval Complete", summary_msg, parent=self)

            self.after(0, _on_finish)

        threading.Thread(target=_worker, daemon=True).start()

    def cancel_batch_cover_fetch(self):
        if self.batch_fetch_running:
            self.batch_fetch_cancelled = True
            self.cover_progress_label.configure(text="Stopping batch operation...", text_color="#f85149")
            self.cancel_fetch_covers_btn.configure(state="disabled")

    def handle_backup(self):
        res = backup_database(parent=self)
        if res:
            self.refresh_stats(custom_status="Backup saved successfully.")

    def handle_quick_backup(self):
        res = quick_backup_database(parent=self)
        if res:
            self.refresh_stats(custom_status=f"Snapshot saved: {Path(res).name}")

    def handle_restore(self):
        res = import_database(app=self.app, parent=self)
        if res:
            self.refresh_stats(custom_status="Database restored and reloaded.")

    def handle_optimize(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
            conn.close()
            messagebox.showinfo("Optimization Complete", "Database vacuumed and indexes rebuilt successfully.", parent=self)
            self.refresh_stats(custom_status="Database vacuumed and optimized.")
        except sqlite3.Error as e:
            messagebox.showerror("Optimization Failed", str(e), parent=self)
            self.status_label.configure(text="Optimization failed.")

    def handle_excel_import(self):
        import_excel_workbook(self.app, parent=self)
        self.refresh_stats(custom_status="Excel import completed.")

    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)
        self.status_label.configure(text=f"Appearance mode set to {new_mode}.")

    def on_close(self):
        self.app.settings_window = None
        self.destroy()

    def center_on_parent(self, parent, width, height):
        parent.update_idletasks()

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()

        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")

