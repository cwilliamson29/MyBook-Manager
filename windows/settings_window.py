import sys
import os
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import customtkinter as ctk
from PIL import Image
from CTkColorPicker import AskColor

from db.config import DB_NAME
from db import db_get, db_update
from windows.settings_helpers.backup_database import backup_database, quick_backup_database
from windows.settings_helpers.import_database import import_database
from windows.settings_helpers.import_excel import import_excel_workbook
from windows.settings_helpers.cover_fetcher import batch_fetch_covers_for_missing, fetch_cover_by_isbn


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / DB_NAME if not Path(DB_NAME).is_absolute() else Path(DB_NAME)

# Theme Palette Constants (Light Mode, Dark Mode)
CARD_BG = ("#ffffff", "#21262d")
CARD_BORDER = ("#d0d7de", "#30363d")
INNER_BG = ("#f6f8fa", "#161b22")
INNER_BORDER = ("#d0d7de", "#30363d")
HEADER_BG = ("#f6f8fa", "#161b22")
TEXT_PRIMARY = ("#1f2328", "#f0f6fc")
TEXT_MUTED = ("#656d76", "#8b949e") #656d76
TEXT_ACCENT = ("#0969da", "#58a6ff")
BTN_SECONDARY_BG = ("#e1e4e8", "#21262d")
BTN_SECONDARY_HOVER = ("#d0d7de", "#30363d")
BTN_SECONDARY_BORDER = ("#d0d7de", "#30363d")
BTN_SECONDARY_TEXT = ("#1f2328", "#f0f6fc") #f0f6fc


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app.root)

        self.withdraw()
        self.app = app

        self.title("Settings & Preferences")
        self.center_on_parent(app.root, 640, 720)
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.batch_fetch_running = False
        self.batch_fetch_cancelled = False

        # Style dictionary
        self.card_style = {
            "fg_color": CARD_BG,
            "corner_radius": 8,
            "border_width": 1,
            "border_color": CARD_BORDER
        }

        # -------------------------------------------------------------
        # Header Banner
        # -------------------------------------------------------------
        header_frame = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=65)
        header_frame.pack(side="top", fill="x", anchor="n")
        header_frame.pack_propagate(False)

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=16, pady=10)

        title_label = ctk.CTkLabel(
            title_box,
            text="Application Settings",
            font=("Arial", 16, "bold"),
            text_color=TEXT_PRIMARY
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_box,
            text="Database management, author & series editing, and preferences",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        )
        subtitle_label.pack(anchor="w")

        # -------------------------------------------------------------
        # Footer Action Bar (built first so status_label is available)
        # -------------------------------------------------------------
        footer_frame = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=45)
        footer_frame.pack(side="bottom", fill="x")
        footer_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            footer_frame,
            text="Ready",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        )
        self.status_label.pack(side="left", padx=16, pady=8)

        close_btn = ctk.CTkButton(
            footer_frame,
            text="Close",
            width=80,
            height=28,
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_color=BTN_SECONDARY_BORDER,
            border_width=1,
            text_color=BTN_SECONDARY_TEXT,
            font=("Arial", 12),
            command=self.on_close
        )
        close_btn.pack(side="right", padx=16, pady=8)

        # -------------------------------------------------------------
        # Main Tabview
        # -------------------------------------------------------------
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=("#f0f2f5", "#0d1117"),
            segmented_button_fg_color=("#979DA2", "gray29"),
            segmented_button_selected_color=("#1f6feb", "#1f6feb"),
            segmented_button_selected_hover_color=("#388bfd", "#388bfd"),
            segmented_button_unselected_color=("#979DA2", "gray29"),
            segmented_button_unselected_hover_color=("gray70", "gray41"),
            corner_radius=8
        )
        self.tabview.pack(fill="both", expand=True, padx=14, pady=(6, 4))

        self.db_tab = self.tabview.add("Database")
        self.authors_series_tab = self.tabview.add("Authors & Series")
        self.genres_tab = self.tabview.add("Genres")
        self.import_tab = self.tabview.add("Import Data")
        self.appearance_tab = self.tabview.add("Appearance")
        self.about_tab = self.tabview.add("About")

        self.build_database_tab()
        self.build_authors_series_tab()
        self.build_genres_tab()
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
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        refresh_btn = ctk.CTkButton(
            header_row,
            text="Refresh",
            width=60,
            height=22,
            font=("Arial", 11),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
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
            tile = ctk.CTkFrame(self.stats_grid, fg_color=INNER_BG, corner_radius=6, border_width=1, border_color=INNER_BORDER)
            tile.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            val_lbl = ctk.CTkLabel(tile, text="--", font=("Arial", 14, "bold"), text_color=TEXT_ACCENT)
            val_lbl.pack(pady=(4, 0))

            sub_lbl = ctk.CTkLabel(tile, text=label_text, font=("Arial", 10), text_color=TEXT_MUTED)
            sub_lbl.pack(pady=(0, 4))

            self.stat_labels[key] = val_lbl

        # Card 2: Backup and Restore Operations
        ops_card = ctk.CTkFrame(tab, **self.card_style)
        ops_card.pack(fill="x", padx=4, pady=6)

        ctk.CTkLabel(
            ops_card,
            text="Backup & Restore",
            font=("Arial", 13, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            ops_card,
            text="Safely duplicate or restore your SQLite database records.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
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
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
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
            text_color=TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            maint_text_box,
            text="Defragment SQLite file, rebuild query indexes, and reclaim space.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
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
            text_color=TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_box,
            text="Edit existing author names and series titles across your library.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        ).pack(anchor="w")

        self.as_mode_var = ctk.StringVar(value="Authors")
        self.as_mode_segment = ctk.CTkSegmentedButton(
            top_row,
            values=["Authors", "Series"],
            variable=self.as_mode_var,
            command=self.switch_authors_series_view,
            fg_color=INNER_BG,
            selected_color="#1f6feb",
            selected_hover_color="#388bfd",
            unselected_color=CARD_BG,
            unselected_hover_color=BTN_SECONDARY_HOVER,
            text_color=TEXT_PRIMARY,
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
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        reload_btn = ctk.CTkButton(
            sel_header,
            text="Reload",
            width=60,
            height=22,
            font=("Arial", 11),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
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
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            edit_card,
            text="Changes will update author metadata across all associated books and series.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Fields Form Grid
        form_frame = ctk.CTkFrame(edit_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=12, pady=4)
        form_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="First Name:", font=("Arial", 12, "bold"), text_color=TEXT_PRIMARY, anchor="w").grid(row=0, column=0, padx=(0, 10), pady=6, sticky="w")
        self.author_first_entry = ctk.CTkEntry(form_frame, font=("Arial", 12), height=32, corner_radius=6)
        self.author_first_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(form_frame, text="Last Name:", font=("Arial", 12, "bold"), text_color=TEXT_PRIMARY, anchor="w").grid(row=1, column=0, padx=(0, 10), pady=6, sticky="w")
        self.author_last_entry = ctk.CTkEntry(form_frame, font=("Arial", 12), height=32, corner_radius=6)
        self.author_last_entry.grid(row=1, column=1, sticky="ew", pady=6)

        # Author Metrics Badges
        metrics_frame = ctk.CTkFrame(edit_card, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=12, pady=8)
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)

        b_tile = ctk.CTkFrame(metrics_frame, fg_color=INNER_BG, corner_radius=6, border_width=1, border_color=INNER_BORDER)
        b_tile.grid(row=0, column=0, padx=(0, 4), sticky="nsew")
        self.author_books_badge = ctk.CTkLabel(b_tile, text="0 Books", font=("Arial", 12, "bold"), text_color=TEXT_ACCENT)
        self.author_books_badge.pack(pady=6)

        s_tile = ctk.CTkFrame(metrics_frame, fg_color=INNER_BG, corner_radius=6, border_width=1, border_color=INNER_BORDER)
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
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
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
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        reload_btn = ctk.CTkButton(
            sel_header,
            text="Reload",
            width=60,
            height=22,
            font=("Arial", 11),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
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
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            edit_card,
            text="Update series title or reassign its primary author association.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Fields Form Grid
        form_frame = ctk.CTkFrame(edit_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=12, pady=4)
        form_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="Series Title:", font=("Arial", 12, "bold"), text_color=TEXT_PRIMARY, anchor="w").grid(row=0, column=0, padx=(0, 10), pady=6, sticky="w")
        self.series_title_entry = ctk.CTkEntry(form_frame, font=("Arial", 12), height=32, corner_radius=6)
        self.series_title_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(form_frame, text="Author:", font=("Arial", 12, "bold"), text_color=TEXT_PRIMARY, anchor="w").grid(row=1, column=0, padx=(0, 10), pady=6, sticky="w")
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

        b_tile = ctk.CTkFrame(metrics_frame, fg_color=INNER_BG, corner_radius=6, border_width=1, border_color=INNER_BORDER)
        b_tile.grid(row=0, column=0, padx=0, sticky="nsew")
        self.series_books_badge = ctk.CTkLabel(b_tile, text="0 Books in Series", font=("Arial", 12, "bold"), text_color=TEXT_ACCENT)
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
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
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
    # TAB 3: GENRES & COLOR SCHEMES
    # =========================================================================
    def build_genres_tab(self):
        tab = self.genres_tab

        self.genre_display_to_id = {}
        self.genre_id_to_obj = {}
        self.genre_id_to_display = {}

        # 1. Header / Selection Card
        sel_card = ctk.CTkFrame(tab, **self.card_style)
        sel_card.pack(fill="x", padx=4, pady=(6, 4))

        sel_header = ctk.CTkFrame(sel_card, fg_color="transparent")
        sel_header.pack(fill="x", padx=12, pady=(10, 4))

        title_box = ctk.CTkFrame(sel_header, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_box,
            text="Genre Color & Label Editor",
            font=("Arial", 13, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Customize the highlight color and display title for each genre.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        ).pack(anchor="w")

        reload_btn = ctk.CTkButton(
            sel_header,
            text="Reload",
            width=60,
            height=22,
            font=("Arial", 11),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            command=self.refresh_genres_dropdown
        )
        reload_btn.pack(side="right")

        sel_body = ctk.CTkFrame(sel_card, fg_color="transparent")
        sel_body.pack(fill="x", padx=12, pady=(4, 10))

        self.genre_select_var = ctk.StringVar()
        self.genre_select_combo = ctk.CTkComboBox(
            sel_body,
            variable=self.genre_select_var,
            values=["Loading..."],
            command=self.on_genre_selected,
            font=("Arial", 12),
            dropdown_font=("Arial", 12),
            height=32,
            corner_radius=6
        )
        self.genre_select_combo.pack(fill="x")

        # 2. Genre Details & Color Editor Card
        edit_card = ctk.CTkFrame(tab, **self.card_style)
        edit_card.pack(fill="x", padx=4, pady=4)

        ctk.CTkLabel(
            edit_card,
            text="Color & Label Settings",
            font=("Arial", 13, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 2))

        # Fields Form Grid
        form_frame = ctk.CTkFrame(edit_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=12, pady=4)
        form_frame.columnconfigure(1, weight=1)

        # Title Field
        ctk.CTkLabel(form_frame, text="Genre Title:", font=("Arial", 12, "bold"), text_color=TEXT_PRIMARY, anchor="w").grid(row=0, column=0, padx=(0, 10), pady=4, sticky="w")
        self.genre_title_entry = ctk.CTkEntry(form_frame, font=("Arial", 12), height=30, corner_radius=6)
        self.genre_title_entry.grid(row=0, column=1, sticky="ew", pady=4)
        self.genre_title_entry.bind("<KeyRelease>", lambda e: self.update_color_preview())

        # Color Hex Code Field + Pick Button
        ctk.CTkLabel(form_frame, text="Hex Color:", font=("Arial", 12, "bold"), text_color=TEXT_PRIMARY, anchor="w").grid(row=1, column=0, padx=(0, 10), pady=4, sticky="w")

        color_input_box = ctk.CTkFrame(form_frame, fg_color="transparent")
        color_input_box.grid(row=1, column=1, sticky="ew", pady=4)
        color_input_box.columnconfigure(0, weight=1)

        self.genre_color_entry = ctk.CTkEntry(color_input_box, placeholder_text="#RRGGBB (or blank for default)", font=("Arial", 12), height=30, corner_radius=6)
        self.genre_color_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.genre_color_entry.bind("<KeyRelease>", lambda e: self.update_color_preview())

        self.pick_color_btn = ctk.CTkButton(
            color_input_box,
            text="🎨 Pick Color...",
            width=110,
            height=30,
            font=("Arial", 11, "bold"),
            fg_color="#1f6feb",
            hover_color="#388bfd",
            command=self.pick_genre_color
        )
        self.pick_color_btn.grid(row=0, column=1, sticky="e")

        # Visual Table Row Highlight Preview Card
        self.genre_preview_frame = ctk.CTkFrame(
            edit_card,
            fg_color=INNER_BG,
            corner_radius=6,
            border_width=1,
            border_color=INNER_BORDER,
            height=34
        )
        self.genre_preview_frame.pack(fill="x", padx=12, pady=6)
        self.genre_preview_frame.pack_propagate(False)

        self.genre_preview_label = ctk.CTkLabel(
            self.genre_preview_frame,
            text="📖 Table Row Preview",
            font=("Arial", 12, "bold"),
            text_color=TEXT_MUTED
        )
        self.genre_preview_label.pack(expand=True)

        # Quick Preset Palette Chips
        palette_box = ctk.CTkFrame(edit_card, fg_color="transparent")
        palette_box.pack(fill="x", padx=12, pady=(2, 4))

        ctk.CTkLabel(
            palette_box,
            text="Quick Color Palette:",
            font=("Arial", 11, "bold"),
            text_color=TEXT_MUTED
        ).pack(anchor="w", pady=(0, 4))

        palette_grid = ctk.CTkFrame(palette_box, fg_color="transparent")
        palette_grid.pack(fill="x")

        presets = [
            ("Coral", "#FF6B6B"),
            ("Peach", "#FFA07A"),
            ("Amber", "#FFD166"),
            ("Sage", "#A7C957"),
            ("Mint", "#06D6A0"),
            ("Cyan", "#48CAE4"),
            ("Sky", "#4EA8DE"),
            ("Indigo", "#5390D9"),
            ("Lavender", "#B5838D"),
            ("Violet", "#9D4EDD"),
            ("Rose", "#E29578"),
            ("Slate", "#ADB5BD"),
        ]

        for idx, (p_name, p_hex) in enumerate(presets):
            col_i = idx % 6
            row_i = idx // 6
            palette_grid.columnconfigure(col_i, weight=1)
            p_btn = ctk.CTkButton(
                palette_grid,
                text=p_name,
                font=("Arial", 10, "bold"),
                fg_color=p_hex,
                text_color="#111111",
                hover_color=p_hex,
                height=22,
                corner_radius=4,
                command=lambda col=p_hex: self.set_selected_color(col)
            )
            p_btn.grid(row=row_i, column=col_i, padx=2, pady=2, sticky="ew")

        # Clear Color / Default row button
        clear_row = ctk.CTkFrame(edit_card, fg_color="transparent")
        clear_row.pack(fill="x", padx=12, pady=(4, 6))

        self.clear_color_btn = ctk.CTkButton(
            clear_row,
            text="✕ Clear Color (Reset to Alternating Rows)",
            font=("Arial", 11),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            height=24,
            command=lambda: self.set_selected_color("")
        )
        self.clear_color_btn.pack(side="left")

        self.genre_books_badge = ctk.CTkLabel(
            clear_row,
            text="0 Books Assigned",
            font=("Arial", 11, "bold"),
            text_color=TEXT_ACCENT
        )
        self.genre_books_badge.pack(side="right")

        # Feedback Label
        self.genre_feedback_label = ctk.CTkLabel(
            edit_card,
            text="",
            font=("Arial", 11),
            text_color="#3fb950"
        )
        self.genre_feedback_label.pack(anchor="w", padx=12, pady=(2, 4))

        # Save & Reset Actions
        action_row = ctk.CTkFrame(edit_card, fg_color="transparent")
        action_row.pack(fill="x", padx=12, pady=(2, 10))
        action_row.columnconfigure(0, weight=2)
        action_row.columnconfigure(1, weight=1)

        self.save_genre_btn = ctk.CTkButton(
            action_row,
            text="Save Changes",
            font=("Arial", 12, "bold"),
            fg_color="#238636",
            hover_color="#2ea043",
            height=32,
            command=self.handle_save_genre
        )
        self.save_genre_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.reset_genre_btn = ctk.CTkButton(
            action_row,
            text="Reset",
            font=("Arial", 12),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            height=32,
            command=self.reset_genre_form
        )
        self.reset_genre_btn.grid(row=0, column=1, sticky="ew")

        # 3. All Genres Catalog Overview Card
        list_card = ctk.CTkFrame(tab, **self.card_style)
        list_card.pack(fill="both", expand=True, padx=4, pady=(4, 6))

        list_header = ctk.CTkFrame(list_card, fg_color="transparent")
        list_header.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            list_header,
            text="All Genres & Color Badges",
            font=("Arial", 12, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            list_header,
            text="Click any genre to edit",
            font=("Arial", 10, "italic"),
            text_color=TEXT_MUTED
        ).pack(side="right")

        self.genres_list_scroll = ctk.CTkScrollableFrame(
            list_card,
            fg_color=INNER_BG,
            corner_radius=6,
            border_width=1,
            border_color=INNER_BORDER,
            height=120
        )
        self.genres_list_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Initial Load
        self.refresh_genres_dropdown()

    def refresh_genres_dropdown(self, selected_id=None):
        genres = db_get.get_genres_with_counts()

        self.genre_display_to_id.clear()
        self.genre_id_to_obj.clear()
        self.genre_id_to_display.clear()

        display_values = []
        for g_id, g_title, g_color, b_count in genres:
            col_mark = "● " if (g_color and str(g_color).strip()) else "○ "
            disp = f"{col_mark}{g_title} ({b_count} books)"
            self.genre_display_to_id[disp] = g_id
            self.genre_id_to_obj[g_id] = {
                "id": g_id,
                "title": g_title,
                "color_scheme": g_color,
                "book_count": b_count
            }
            self.genre_id_to_display[g_id] = disp
            display_values.append(disp)

        if not display_values:
            display_values = ["No Genres Found"]

        self.genre_select_combo.configure(values=display_values)

        target_disp = None
        if selected_id and selected_id in self.genre_id_to_display:
            target_disp = self.genre_id_to_display[selected_id]
        elif display_values and display_values[0] != "No Genres Found":
            target_disp = display_values[0]

        if target_disp:
            self.genre_select_var.set(target_disp)
            self.on_genre_selected(target_disp)
        else:
            self.genre_title_entry.delete(0, "end")
            self.genre_color_entry.delete(0, "end")
            self.genre_books_badge.configure(text="0 Books Assigned")
            self.update_color_preview("")

        self.render_genres_overview_list(genres)

    def render_genres_overview_list(self, genres=None):
        if genres is None:
            genres = db_get.get_genres_with_counts()

        for w in self.genres_list_scroll.winfo_children():
            w.destroy()

        if not genres:
            ctk.CTkLabel(
                self.genres_list_scroll,
                text="No genres available in the database.",
                font=("Arial", 11),
                text_color=TEXT_MUTED
            ).pack(pady=15)
            return

        for g_id, g_title, g_color, b_count in genres:
            has_color = bool(g_color and str(g_color).strip())
            color_hex = str(g_color).strip() if has_color else ""

            row_frame = ctk.CTkFrame(
                self.genres_list_scroll,
                fg_color=CARD_BG,
                corner_radius=4,
                height=28
            )
            row_frame.pack(fill="x", pady=2, padx=2)
            row_frame.pack_propagate(False)

            # Swatch badge
            swatch_bg = color_hex if has_color else ("#d0d7de", "#30363d")
            swatch = ctk.CTkFrame(
                row_frame,
                width=16,
                height=16,
                fg_color=swatch_bg,
                corner_radius=4,
                border_width=1 if not has_color else 0,
                border_color=INNER_BORDER
            )
            swatch.pack(side="left", padx=(8, 6), pady=6)

            title_lbl = ctk.CTkLabel(
                row_frame,
                text=g_title,
                font=("Arial", 11, "bold"),
                text_color=TEXT_PRIMARY,
                anchor="w",
                cursor="hand2"
            )
            title_lbl.pack(side="left", fill="x", expand=True, padx=4)

            count_lbl = ctk.CTkLabel(
                row_frame,
                text=f"{b_count} books" if b_count != 1 else "1 book",
                font=("Arial", 10),
                text_color=TEXT_MUTED,
                cursor="hand2"
            )
            count_lbl.pack(side="right", padx=8)

            # Make entire row clickable to select
            select_cmd = lambda gid=g_id: self.select_genre_by_id(gid)
            row_frame.bind("<Button-1>", lambda e, cmd=select_cmd: cmd())
            title_lbl.bind("<Button-1>", lambda e, cmd=select_cmd: cmd())
            count_lbl.bind("<Button-1>", lambda e, cmd=select_cmd: cmd())

    def select_genre_by_id(self, genre_id):
        if genre_id in self.genre_id_to_display:
            disp = self.genre_id_to_display[genre_id]
            self.genre_select_var.set(disp)
            self.on_genre_selected(disp)

    def on_genre_selected(self, choice=None):
        disp = self.genre_select_var.get()
        genre_id = self.genre_display_to_id.get(disp)
        if not genre_id or genre_id not in self.genre_id_to_obj:
            return

        obj = self.genre_id_to_obj[genre_id]
        self.genre_title_entry.delete(0, "end")
        self.genre_title_entry.insert(0, obj["title"])

        self.genre_color_entry.delete(0, "end")
        if obj["color_scheme"]:
            self.genre_color_entry.insert(0, str(obj["color_scheme"]))

        self.genre_books_badge.configure(text=f"{obj['book_count']} Books Assigned")
        self.genre_feedback_label.configure(text="")
        self.update_color_preview()

    def set_selected_color(self, hex_code):
        clean_code = str(hex_code).strip() if hex_code else ""
        self.genre_color_entry.delete(0, "end")
        if clean_code:
            self.genre_color_entry.insert(0, clean_code)
        self.update_color_preview(clean_code)

    def update_color_preview(self, hex_code=None):
        if hex_code is None:
            hex_code = self.genre_color_entry.get().strip() if hasattr(self, "genre_color_entry") else ""

        genre_name = self.genre_title_entry.get().strip() if hasattr(self, "genre_title_entry") else "Genre"
        if not genre_name:
            genre_name = "Genre"

        clean_hex = str(hex_code).strip()
        if clean_hex and not clean_hex.startswith("#") and len(clean_hex) in (3, 6):
            clean_hex = "#" + clean_hex

        is_valid_hex = False
        if clean_hex.startswith("#") and len(clean_hex) in (4, 7):
            try:
                int(clean_hex.lstrip("#"), 16)
                is_valid_hex = True
            except ValueError:
                is_valid_hex = False

        if is_valid_hex:
            bg_col = clean_hex
            text_col = "#000000"
            display_text = f"📖 Table Highlight Preview  •  {genre_name} ({clean_hex})"
        else:
            bg_col = "#21262d"
            text_col = "#8b949e"
            display_text = f"📖 Table Highlight Preview  •  {genre_name} (Default Alternating Rows)"

        try:
            self.genre_preview_frame.configure(fg_color=bg_col)
            self.genre_preview_label.configure(text=display_text, text_color=text_col)
        except Exception:
            pass

    def pick_genre_color(self):
        current_val = self.genre_color_entry.get().strip()
        if current_val and not current_val.startswith("#") and len(current_val) in (3, 6):
            current_val = "#" + current_val

        init_color = current_val if (current_val.startswith("#") and len(current_val) in (4, 7)) else "#4EA8DE"

        chosen_color = None
        try:
            picker = AskColor(title="Choose Genre Color", initial_color=init_color)
            color = picker.get()
            if color:
                chosen_color = color
        except Exception:
            try:
                rgb, hex_code = colorchooser.askcolor(color=init_color, title="Choose Genre Color")
                if hex_code:
                    chosen_color = hex_code
            except Exception as e:
                print("Color chooser error:", e)

        if chosen_color:
            self.set_selected_color(chosen_color)

    def reset_genre_form(self):
        disp = self.genre_select_var.get()
        self.on_genre_selected(disp)
        self.genre_feedback_label.configure(text="Form reset to saved values.", text_color="#8b949e")

    def handle_save_genre(self):
        disp = self.genre_select_var.get()
        genre_id = self.genre_display_to_id.get(disp)
        if not genre_id:
            self.genre_feedback_label.configure(text="Please select a genre to edit.", text_color="#f85149")
            return

        new_title = self.genre_title_entry.get().strip()
        if not new_title:
            self.genre_feedback_label.configure(text="Genre title cannot be blank.", text_color="#f85149")
            return

        raw_color = self.genre_color_entry.get().strip()
        new_color = None
        if raw_color:
            if not raw_color.startswith("#") and len(raw_color) in (3, 6):
                raw_color = "#" + raw_color
            if raw_color.startswith("#") and len(raw_color) in (4, 7):
                try:
                    int(raw_color.lstrip("#"), 16)
                    new_color = raw_color
                except ValueError:
                    self.genre_feedback_label.configure(text="Invalid hex color format (use #RRGGBB).", text_color="#f85149")
                    return
            else:
                self.genre_feedback_label.configure(text="Invalid hex color format (use #RRGGBB or leave blank).", text_color="#f85149")
                return

        res = db_update.update_genre(genre_id, new_title, new_color)
        if res == "success":
            self.genre_feedback_label.configure(
                text=f"✓ Genre '{new_title}' and color updated successfully!",
                text_color="#3fb950"
            )
            self.refresh_stats(custom_status=f"Updated genre: {new_title}")

            # Notify and refresh main application table and filters
            if hasattr(self.app, "load_books"):
                self.app.load_books()
            if hasattr(self.app, "load_genres_into_filter"):
                self.app.load_genres_into_filter()

            # Refresh local dropdown and list
            self.refresh_genres_dropdown(selected_id=genre_id)
        else:
            self.genre_feedback_label.configure(
                text=f"Error saving genre: {res}",
                text_color="#f85149"
            )

    # =========================================================================
    # TAB 4: DATA IMPORT & COVERS
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
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            cover_card,
            text="Search online APIs (Open Library & Google Books) and download cover artwork for all books with an ISBN.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Status & Count Row
        stat_box = ctk.CTkFrame(cover_card, fg_color=INNER_BG, corner_radius=6, border_width=1, border_color=INNER_BORDER)
        stat_box.pack(fill="x", padx=12, pady=4)

        stat_row = ctk.CTkFrame(stat_box, fg_color="transparent")
        stat_row.pack(fill="x", padx=10, pady=6)

        self.missing_covers_label = ctk.CTkLabel(
            stat_row,
            text="Checking books missing cover images...",
            font=("Arial", 11, "bold"),
            text_color=TEXT_ACCENT,
            anchor="w"
        )
        self.missing_covers_label.pack(side="left", fill="x", expand=True)

        self.refresh_covers_btn = ctk.CTkButton(
            stat_row,
            text="Check",
            width=55,
            height=22,
            font=("Arial", 11),
            fg_color=BTN_SECONDARY_BG,
            hover_color=BTN_SECONDARY_HOVER,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
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
            text_color=TEXT_MUTED,
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
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            excel_card,
            text="Import books, authors, series, and genres in bulk from spreadsheet files.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(0, 6))

        # Column Layout Specification Box
        spec_box = ctk.CTkFrame(excel_card, fg_color=INNER_BG, corner_radius=6, border_width=1, border_color=INNER_BORDER)
        spec_box.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            spec_box,
            text="Expected Spreadsheet Column Format:",
            font=("Arial", 11, "bold"),
            text_color=TEXT_ACCENT
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

            ctk.CTkLabel(row, text=col_name, width=80, font=("Arial", 10, "bold"), text_color=TEXT_PRIMARY, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=col_desc, font=("Arial", 10), text_color=TEXT_MUTED, anchor="w").pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            spec_box,
            text="* Note: The first row is treated as headers and automatically skipped. Relational multi-sheet workbooks are also supported.",
            font=("Arial", 9, "italic"),
            text_color=TEXT_MUTED
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
    # TAB 5: APPEARANCE
    # =========================================================================
    def build_appearance_tab(self):
        tab = self.appearance_tab

        theme_card = ctk.CTkFrame(tab, **self.card_style)
        theme_card.pack(fill="x", padx=4, pady=6)

        ctk.CTkLabel(
            theme_card,
            text="Interface Appearance",
            font=("Arial", 13, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            theme_card,
            text="Customize the visual theme and contrast mode of the application.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(0, 10))

        mode_row = ctk.CTkFrame(theme_card, fg_color="transparent")
        mode_row.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(mode_row, text="Theme Mode:", font=("Arial", 12), text_color=TEXT_PRIMARY).pack(side="left", padx=(0, 10))

        current_mode = ctk.get_appearance_mode()
        self.mode_var = ctk.StringVar(value=current_mode)

        self.theme_segment = ctk.CTkSegmentedButton(
            mode_row,
            values=["Dark", "Light", "System"],
            variable=self.mode_var,
            fg_color=INNER_BG,
            selected_color="#1f6feb",
            selected_hover_color="#388bfd",
            unselected_color=CARD_BG,
            unselected_hover_color=BTN_SECONDARY_HOVER,
            text_color=TEXT_PRIMARY,
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
            text_color=TEXT_PRIMARY
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

            ctk.CTkLabel(row, text=f"•  {shortcut}:", width=120, font=("Arial", 11, "bold"), text_color=TEXT_ACCENT, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=desc, font=("Arial", 11), text_color=TEXT_MUTED, anchor="w").pack(side="left", fill="x", expand=True)

    # =========================================================================
    # TAB 6: ABOUT & INFORMATION
    # =========================================================================
    def build_about_tab(self):
        tab = self.about_tab

        about_card = ctk.CTkFrame(tab, **self.card_style)
        about_card.pack(fill="both", expand=True, padx=4, pady=6)

        ctk.CTkLabel(
            about_card,
            text="MyBook Manager",
            font=("Arial", 15, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(12, 2))

        ctk.CTkLabel(
            about_card,
            text="Personal library and book cataloging management system.",
            font=("Arial", 11),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(0, 12))

        info_rows = [
            ("Application Version", "1.2.0"),
            ("Python Runtime", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"),
            ("SQLite Engine", sqlite3.sqlite_version),
            ("Database Path", str(DB_PATH)),
            ("GUI Framework", "CustomTkinter / Tkinter"),
        ]

        for label_text, value_text in info_rows:
            row = ctk.CTkFrame(about_card, fg_color=INNER_BG, corner_radius=6, border_width=1, border_color=INNER_BORDER)
            row.pack(fill="x", padx=12, pady=4)

            ctk.CTkLabel(row, text=label_text, width=140, font=("Arial", 11, "bold"), text_color=TEXT_MUTED, anchor="w").pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=value_text, font=("Arial", 11), text_color=TEXT_PRIMARY, anchor="w").pack(side="left", padx=10, pady=6, fill="x", expand=True)

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
        if hasattr(self.app, "on_appearance_mode_changed"):
            self.app.on_appearance_mode_changed(new_mode)
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

