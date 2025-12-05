"""
🚀 Lead-Tool V4.0 - Ultra Modern Edition
Powered by CustomTkinter - Material Design UI
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import os
import logging
from datetime import datetime, timezone
import pandas as pd

# Versuche dotenv zu laden (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Models
from models_v3 import DatabaseV3, CompanyV3
from sqlalchemy import or_, and_

# Modules
from compliment_generator import ComplimentGenerator, AIColumnProcessor
from impressum_scraper import ImpressumScraper
from prompt_manager import PromptManager
from email_scraper import EmailScraper

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ModernColors:
    """Ultra moderne Farbpalette"""

    # Background Gradients
    BG_PRIMARY = "#0f0f1e"
    BG_SECONDARY = "#1a1a2e"
    BG_TERTIARY = "#16213e"

    # Accent Colors (Material Design 3)
    ACCENT_PRIMARY = "#3b82f6"  # Blue
    ACCENT_SECONDARY = "#8b5cf6"  # Purple
    ACCENT_SUCCESS = "#10b981"  # Green
    ACCENT_WARNING = "#f59e0b"  # Orange
    ACCENT_DANGER = "#ef4444"  # Red

    # Text
    TEXT_PRIMARY = "#f1f5f9"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"

    # Cards & Surfaces
    CARD_BG = "#1e293b"
    CARD_HOVER = "#334155"
    BORDER = "#334155"


class ModernLeadTool(ctk.CTk):
    """Ultra moderne Lead-Tool Anwendung"""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Lead-Tool V4.0 - Modern Edition 🚀")
        self.geometry("1920x1080")

        # Database
        self.db = DatabaseV3()
        self.session = self.db.get_session()

        # Modules
        self.compliment_generator = ComplimentGenerator()
        self.ai_column_processor = AIColumnProcessor()  # KI-Spalten-Processor (Clay-Style)
        self.impressum_scraper = ImpressumScraper()
        self.prompt_manager = PromptManager()

        # Email Scraper mit optionalem LLM-Fallback (DeepSeek API Key optional)
        # Setze use_llm_fallback=False standardmäßig (kann in Settings aktiviert werden)
        self.email_scraper = EmailScraper(
            deepseek_api_key=None,  # Kann später aus config.json geladen werden
            use_llm_fallback=False   # LLM-Fallback standardmäßig deaktiviert
        )

        # State
        self.current_results = []
        self.selected_items = {}  # {company_id: checkbox_var}
        self.item_to_company = {}
        self.filter_timer = None
        self.current_view = "filter"
        self.card_widgets = {}  # {company_id: card_frame}

        # Pagination - REDUZIERT für Performance (25 statt 50 = 50% weniger Widgets)
        self.current_page = 1
        self.items_per_page = 25

        # Query Cache für Performance
        self._category_cache = None
        self._category_cache_time = 0
        self.CACHE_DURATION = 300  # 5 Minuten

        # Load configs
        self.load_configs()

        # Build UI
        self.setup_ui()

    def load_configs(self):
        """Load configuration files"""
        try:
            with open('category_hierarchy.json', 'r', encoding='utf-8') as f:
                self.category_hierarchy = json.load(f)
        except FileNotFoundError:
            logging.warning("category_hierarchy.json nicht gefunden")
            self.category_hierarchy = {}
        except json.JSONDecodeError as e:
            logging.warning(f"category_hierarchy.json ungültig: {e}")
            self.category_hierarchy = {}

        try:
            with open('api_config.json', 'r', encoding='utf-8') as f:
                self.api_config = json.load(f)
            # Lade API Keys aus Umgebungsvariablen
            self._load_api_keys_from_env()
        except FileNotFoundError:
            logging.warning("api_config.json nicht gefunden")
            self.api_config = {"apis": {}, "active_api": "deepseek"}
        except json.JSONDecodeError as e:
            logging.warning(f"api_config.json ungültig: {e}")
            self.api_config = {"apis": {}, "active_api": "deepseek"}

    def _load_api_keys_from_env(self):
        """Lädt API Keys aus Umgebungsvariablen"""
        for api_name, api_settings in self.api_config.get('apis', {}).items():
            env_var = api_settings.get('api_key_env')
            if env_var:
                env_value = os.environ.get(env_var, '')
                if env_value:
                    api_settings['api_key'] = env_value
                    logging.debug(f"API Key für {api_name} aus {env_var} geladen")

    def setup_ui(self):
        """Setup moderne UI mit Sidebar Navigation"""

        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === SIDEBAR ===
        self.setup_sidebar()

        # === MAIN CONTENT ===
        self.main_container = ctk.CTkFrame(self, fg_color=ModernColors.BG_PRIMARY)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Setup views
        self.setup_filter_view()

    def setup_sidebar(self):
        """Moderne Sidebar mit Navigation"""

        sidebar = ctk.CTkFrame(self, width=280, fg_color=ModernColors.BG_SECONDARY, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(7, weight=1)

        # Logo & Title
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=30, pady=(40, 30), sticky="ew")

        title = ctk.CTkLabel(
            logo_frame,
            text="🚀 Lead-Tool",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            logo_frame,
            text="Modern Edition v4.0",
            font=ctk.CTkFont(size=12),
            text_color=ModernColors.TEXT_SECONDARY
        )
        subtitle.pack()

        # Navigation Buttons
        nav_buttons = [
            ("🔍  Filter & Suche", "filter", ModernColors.ACCENT_PRIMARY),
            ("📤  CSV Upload", "upload", ModernColors.ACCENT_SECONDARY),
            ("💬  Prompts", "prompts", ModernColors.ACCENT_WARNING),
            ("🤖  API Config", "api", ModernColors.ACCENT_SUCCESS),
            ("⚙️  Einstellungen", "settings", ModernColors.TEXT_SECONDARY),
        ]

        self.nav_buttons = {}
        for idx, (text, view, color) in enumerate(nav_buttons):
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                font=ctk.CTkFont(size=15, weight="bold"),
                height=50,
                corner_radius=12,
                fg_color="transparent",
                hover_color=ModernColors.CARD_HOVER,
                text_color=ModernColors.TEXT_SECONDARY,
                anchor="w",
                command=lambda v=view: self.switch_view(v)
            )
            btn.grid(row=idx+1, column=0, padx=20, pady=8, sticky="ew")
            self.nav_buttons[view] = btn

        # Highlight first button
        self.highlight_nav_button("filter")

        # Stats Card
        stats_frame = ctk.CTkFrame(sidebar, fg_color=ModernColors.CARD_BG, corner_radius=15)
        stats_frame.grid(row=8, column=0, padx=20, pady=20, sticky="ew")

        stats_title = ctk.CTkLabel(
            stats_frame,
            text="📊 Datenbank",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        stats_title.pack(padx=20, pady=(15, 10))

        # Get total companies
        total_companies = self.session.query(CompanyV3).count()

        stats_value = ctk.CTkLabel(
            stats_frame,
            text=f"{total_companies:,}",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=ModernColors.ACCENT_PRIMARY
        )
        stats_value.pack(padx=20, pady=(0, 5))

        stats_label = ctk.CTkLabel(
            stats_frame,
            text="Total Leads",
            font=ctk.CTkFont(size=12),
            text_color=ModernColors.TEXT_SECONDARY
        )
        stats_label.pack(padx=20, pady=(0, 15))

    def highlight_nav_button(self, view):
        """Highlight aktiven Navigation Button"""
        for v, btn in self.nav_buttons.items():
            if v == view:
                btn.configure(
                    fg_color=ModernColors.ACCENT_PRIMARY,
                    text_color="white"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=ModernColors.TEXT_SECONDARY
                )

    def switch_view(self, view):
        """Switch zwischen verschiedenen Views"""
        self.current_view = view
        self.highlight_nav_button(view)

        # Clear main container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Show requested view
        if view == "filter":
            self.setup_filter_view()
        elif view == "upload":
            self.setup_upload_view()
        elif view == "prompts":
            self.setup_prompts_view()
        elif view == "api":
            self.setup_api_view()
        elif view == "settings":
            self.setup_settings_view()

    def setup_filter_view(self):
        """Moderne Filter & Suche View"""

        # Main container with grid
        container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(1, weight=1)

        # === HEADER ===
        header = ctk.CTkFrame(container, fg_color="transparent", height=80)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        header_title = ctk.CTkLabel(
            header,
            text="🔍 Smart Lead Filter",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        header_title.pack(side="left")

        # Result Counter
        self.result_badge = ctk.CTkLabel(
            header,
            text="0 Leads",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white",
            fg_color=ModernColors.ACCENT_PRIMARY,
            corner_radius=20,
            padx=25,
            pady=10
        )
        self.result_badge.pack(side="right")

        # === FILTER SIDEBAR ===
        filter_sidebar = ctk.CTkScrollableFrame(
            container,
            width=380,
            fg_color=ModernColors.BG_SECONDARY,
            corner_radius=20
        )
        filter_sidebar.grid(row=1, column=0, sticky="ns", padx=(0, 20))

        self.setup_filters(filter_sidebar)

        # === RESULTS AREA ===
        results_container = ctk.CTkFrame(container, fg_color="transparent")
        results_container.grid(row=1, column=1, sticky="nsew")
        results_container.grid_rowconfigure(1, weight=1)
        results_container.grid_columnconfigure(0, weight=1)

        # Control Bar
        control_bar = ctk.CTkFrame(results_container, fg_color=ModernColors.CARD_BG, corner_radius=15)
        control_bar.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        control_inner = ctk.CTkFrame(control_bar, fg_color="transparent")
        control_inner.pack(fill="both", expand=True, padx=20, pady=15)

        # Buttons
        btn_select_all = ctk.CTkButton(
            control_inner,
            text="☑️  Alle auswählen",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color="transparent",
            border_width=2,
            border_color=ModernColors.BORDER,
            hover_color=ModernColors.CARD_HOVER,
            command=self.select_all
        )
        btn_select_all.pack(side="left", padx=(0, 10))

        btn_deselect = ctk.CTkButton(
            control_inner,
            text="☐  Auswahl aufheben",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color="transparent",
            border_width=2,
            border_color=ModernColors.BORDER,
            hover_color=ModernColors.CARD_HOVER,
            command=self.deselect_all
        )
        btn_deselect.pack(side="left", padx=(0, 10))

        btn_refresh = ctk.CTkButton(
            control_inner,
            text="🔄  Aktualisieren",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.refresh_table
        )
        btn_refresh.pack(side="left", padx=(0, 10))

        # Right side buttons
        btn_delete = ctk.CTkButton(
            control_inner,
            text="🗑️  Löschen",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_DANGER,
            hover_color="#dc2626",
            command=self.delete_selected
        )
        btn_delete.pack(side="right")

        btn_export_excel = ctk.CTkButton(
            control_inner,
            text="📥  Excel",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color="#059669",
            command=self.export_to_excel
        )
        btn_export_excel.pack(side="right", padx=(0, 10))

        btn_export_csv = ctk.CTkButton(
            control_inner,
            text="📄  CSV",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color="#059669",
            command=self.export_to_csv
        )
        btn_export_csv.pack(side="right", padx=(0, 10))

        btn_bulk_compliment = ctk.CTkButton(
            control_inner,
            text="💬  Komplimente",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.bulk_generate_compliments
        )
        btn_bulk_compliment.pack(side="right", padx=(0, 10))

        btn_bulk_delete_compliments = ctk.CTkButton(
            control_inner,
            text="🗑️  Komplimente löschen",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.bulk_delete_compliments
        )
        btn_bulk_delete_compliments.pack(side="right", padx=(0, 10))

        # KI-SPALTEN Button (Clay-Style!) - WICHTIGSTES FEATURE
        btn_ai_column = ctk.CTkButton(
            control_inner,
            text="🤖  KI-Spalte",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color="#10B981",
            hover_color="#059669",
            command=self.show_ai_column_dialog
        )
        btn_ai_column.pack(side="right", padx=(0, 10))

        # Kombinierter Button für Kontaktdaten (Name + E-Mail in einem Durchgang)
        btn_bulk_contact = ctk.CTkButton(
            control_inner,
            text="📇  Kontaktdaten",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            command=self.bulk_scrape_contact_data
        )
        btn_bulk_contact.pack(side="right", padx=(0, 10))

        # Results Table
        self.setup_results_table(results_container)

        # Pagination Bar
        pagination_bar = ctk.CTkFrame(results_container, fg_color=ModernColors.CARD_BG, corner_radius=15, height=60)
        pagination_bar.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        pagination_bar.grid_propagate(False)

        pagination_inner = ctk.CTkFrame(pagination_bar, fg_color="transparent")
        pagination_inner.pack(expand=True)

        # Previous button
        self.btn_prev_page = ctk.CTkButton(
            pagination_inner,
            text="◀ Zurück",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            width=120,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.previous_page
        )
        self.btn_prev_page.pack(side="left", padx=(0, 15))

        # Page info
        self.page_info_label = ctk.CTkLabel(
            pagination_inner,
            text="Seite 1 / 1",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        self.page_info_label.pack(side="left", padx=20)

        # Next button
        self.btn_next_page = ctk.CTkButton(
            pagination_inner,
            text="Weiter ▶",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            width=120,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.next_page
        )
        self.btn_next_page.pack(side="left", padx=(15, 0))

    def setup_filters(self, parent):
        """Setup moderne Filter Controls"""

        # Quick Search
        search_label = ctk.CTkLabel(
            parent,
            text="🔎 Schnellsuche",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        search_label.pack(padx=25, pady=(25, 10), anchor="w")

        self.quick_search_var = ctk.StringVar()
        self.quick_search_var.trace('w', lambda *args: self.schedule_live_filter())

        search_entry = ctk.CTkEntry(
            parent,
            placeholder_text="Firmenname suchen...",
            height=50,
            corner_radius=12,
            font=ctk.CTkFont(size=14),
            textvariable=self.quick_search_var,
            border_width=0,
            fg_color=ModernColors.CARD_BG
        )
        search_entry.pack(padx=25, pady=(0, 20), fill="x")

        # Kategorien
        cat_label = ctk.CTkLabel(
            parent,
            text="🏢 Kategorien",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        cat_label.pack(padx=25, pady=(10, 10), anchor="w")

        self.main_cat_var = ctk.StringVar(value="Alle")
        main_categories = ["Alle"] + list(self.category_hierarchy.keys())

        main_cat_menu = ctk.CTkOptionMenu(
            parent,
            values=main_categories,
            variable=self.main_cat_var,
            height=45,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            fg_color=ModernColors.CARD_BG,
            button_color=ModernColors.ACCENT_PRIMARY,
            button_hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.on_main_category_change
        )
        main_cat_menu.pack(padx=25, pady=(0, 12), fill="x")

        self.sub_cat_var = ctk.StringVar(value="Alle")
        self.sub_cat_menu = ctk.CTkOptionMenu(
            parent,
            values=["Alle"],
            variable=self.sub_cat_var,
            height=45,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            fg_color=ModernColors.CARD_BG,
            button_color=ModernColors.ACCENT_PRIMARY,
            button_hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.on_sub_category_change
        )
        self.sub_cat_menu.pack(padx=25, pady=(0, 12), fill="x")

        self.specific_cat_var = ctk.StringVar(value="Alle")
        self.specific_cat_menu = ctk.CTkOptionMenu(
            parent,
            values=["Alle"],
            variable=self.specific_cat_var,
            height=45,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            fg_color=ModernColors.CARD_BG,
            button_color=ModernColors.ACCENT_PRIMARY,
            button_hover_color=ModernColors.ACCENT_SECONDARY
        )
        self.specific_cat_menu.pack(padx=25, pady=(0, 20), fill="x")

        # Rating
        rating_label = ctk.CTkLabel(
            parent,
            text="⭐ Mindest-Rating",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        rating_label.pack(padx=25, pady=(10, 10), anchor="w")

        rating_frame = ctk.CTkFrame(parent, fg_color="transparent")
        rating_frame.pack(padx=25, fill="x")

        self.rating_value_label = ctk.CTkLabel(
            rating_frame,
            text="0.0 ⭐",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.ACCENT_WARNING
        )
        self.rating_value_label.pack(side="right")

        self.rating_var = ctk.DoubleVar(value=0)
        rating_slider = ctk.CTkSlider(
            parent,
            from_=0,
            to=5,
            number_of_steps=50,
            variable=self.rating_var,
            height=20,
            corner_radius=10,
            button_color=ModernColors.ACCENT_WARNING,
            button_hover_color=ModernColors.ACCENT_DANGER,
            progress_color=ModernColors.ACCENT_WARNING,
            command=self.update_rating_label
        )
        rating_slider.pack(padx=25, pady=(10, 20), fill="x")

        # Reviews
        reviews_label = ctk.CTkLabel(
            parent,
            text="💬 Mindest-Reviews",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        reviews_label.pack(padx=25, pady=(10, 10), anchor="w")

        self.reviews_var = ctk.StringVar(value="0")
        reviews_entry = ctk.CTkEntry(
            parent,
            placeholder_text="Anzahl eingeben...",
            height=45,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            textvariable=self.reviews_var,
            border_width=0,
            fg_color=ModernColors.CARD_BG
        )
        reviews_entry.pack(padx=25, pady=(0, 20), fill="x")

        # Location
        loc_label = ctk.CTkLabel(
            parent,
            text="📍 Standort",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        loc_label.pack(padx=25, pady=(10, 10), anchor="w")

        self.location_var = ctk.StringVar()
        location_entry = ctk.CTkEntry(
            parent,
            placeholder_text="Stadt oder PLZ...",
            height=45,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            textvariable=self.location_var,
            border_width=0,
            fg_color=ModernColors.CARD_BG
        )
        location_entry.pack(padx=25, pady=(0, 20), fill="x")

        # Checkboxes
        self.has_phone_var = ctk.BooleanVar()
        phone_check = ctk.CTkCheckBox(
            parent,
            text="📱 Hat Telefonnummer",
            variable=self.has_phone_var,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            checkbox_width=24,
            checkbox_height=24,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color=ModernColors.ACCENT_PRIMARY
        )
        phone_check.pack(padx=25, pady=(0, 12), anchor="w")

        self.has_website_var = ctk.BooleanVar()
        website_check = ctk.CTkCheckBox(
            parent,
            text="🌐 Hat Website",
            variable=self.has_website_var,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            checkbox_width=24,
            checkbox_height=24,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color=ModernColors.ACCENT_PRIMARY
        )
        website_check.pack(padx=25, pady=(0, 20), anchor="w")

        # Limit
        limit_label = ctk.CTkLabel(
            parent,
            text="⚙️ Max. Ergebnisse",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        limit_label.pack(padx=25, pady=(10, 10), anchor="w")

        self.limit_var = ctk.StringVar(value="500")
        limit_entry = ctk.CTkEntry(
            parent,
            placeholder_text="Anzahl...",
            height=45,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            textvariable=self.limit_var,
            border_width=0,
            fg_color=ModernColors.CARD_BG
        )
        limit_entry.pack(padx=25, pady=(0, 20), fill="x")

        # Action Buttons
        btn_apply = ctk.CTkButton(
            parent,
            text="🔍  Filter anwenden",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            corner_radius=12,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.apply_filters
        )
        btn_apply.pack(padx=25, pady=(10, 12), fill="x")

        btn_reset = ctk.CTkButton(
            parent,
            text="🔄  Zurücksetzen",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            corner_radius=12,
            fg_color="transparent",
            border_width=2,
            border_color=ModernColors.BORDER,
            hover_color=ModernColors.CARD_HOVER,
            command=self.reset_filters
        )
        btn_reset.pack(padx=25, pady=(0, 20), fill="x")

        # Workflow Filters
        workflow_label = ctk.CTkLabel(
            parent,
            text="📊 Workflow-Filter",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        workflow_label.pack(padx=25, pady=(20, 10), anchor="w")

        btn_complete = ctk.CTkButton(
            parent,
            text="✅  Komplett-Workflow",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color="#059669",
            command=self.filter_complete_workflow
        )
        btn_complete.pack(padx=25, pady=(0, 10), fill="x")

        btn_no_names = ctk.CTkButton(
            parent,
            text="❌  Ohne Namen",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.CARD_BG,
            hover_color=ModernColors.CARD_HOVER,
            command=self.filter_no_names
        )
        btn_no_names.pack(padx=25, pady=(0, 10), fill="x")

        btn_no_compliment = ctk.CTkButton(
            parent,
            text="⚠️  Ohne Kompliment",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.CARD_BG,
            hover_color=ModernColors.CARD_HOVER,
            command=self.filter_no_compliment
        )
        btn_no_compliment.pack(padx=25, pady=(0, 20), fill="x")

        # Rating Filter Section
        rating_filter_label = ctk.CTkLabel(
            parent,
            text="⭐ Rating-Filter",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        rating_filter_label.pack(padx=25, pady=(20, 10), anchor="w")

        btn_top_rated = ctk.CTkButton(
            parent,
            text="⭐⭐⭐  Top (4.0-5.0)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color="#059669",
            command=lambda: self.filter_rating_range(4.0, 5.0)
        )
        btn_top_rated.pack(padx=25, pady=(0, 10), fill="x")

        btn_mid_rated = ctk.CTkButton(
            parent,
            text="⭐⭐  Mittel (3.0-3.9)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_WARNING,
            hover_color="#d97706",
            command=lambda: self.filter_rating_range(3.0, 3.9)
        )
        btn_mid_rated.pack(padx=25, pady=(0, 10), fill="x")

        btn_low_rated = ctk.CTkButton(
            parent,
            text="⭐  Schlecht (1.0-2.9)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_DANGER,
            hover_color="#dc2626",
            command=lambda: self.filter_rating_range(1.0, 2.9)
        )
        btn_low_rated.pack(padx=25, pady=(0, 30), fill="x")

    def setup_results_table(self, parent):
        """Setup moderne Results Table"""

        # Normal Frame for results (nicht scrollable - scrolling passiert in der Tabelle)
        results_frame = ctk.CTkFrame(
            parent,
            fg_color=ModernColors.BG_SECONDARY,
            corner_radius=20
        )
        results_frame.grid(row=1, column=0, sticky="nsew")

        self.results_container = results_frame

        # Initial load
        self.apply_filters()

    def display_results(self):
        """Display results as table with pagination"""

        # Clear existing
        for widget in self.results_container.winfo_children():
            widget.destroy()

        # Clear card widgets (but keep selection state for IDs that still exist)
        self.card_widgets.clear()

        # Remove selection states for companies not in current results
        current_ids = {c.id for c in self.current_results}
        ids_to_remove = [cid for cid in self.selected_items.keys() if cid not in current_ids]
        for cid in ids_to_remove:
            del self.selected_items[cid]

        if not self.current_results:
            # Empty state
            empty_frame = ctk.CTkFrame(self.results_container, fg_color="transparent")
            empty_frame.pack(expand=True, fill="both", pady=100)

            empty_label = ctk.CTkLabel(
                empty_frame,
                text="🔍",
                font=ctk.CTkFont(size=64)
            )
            empty_label.pack()

            empty_text = ctk.CTkLabel(
                empty_frame,
                text="Keine Leads gefunden",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=ModernColors.TEXT_SECONDARY
            )
            empty_text.pack(pady=(20, 0))

            # Update pagination
            self.update_pagination_controls()
            return

        # Calculate pagination
        total = len(self.current_results)
        total_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)

        # Ensure current page is valid
        if self.current_page > total_pages:
            self.current_page = total_pages
        if self.current_page < 1:
            self.current_page = 1

        # Get items for current page
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total)
        page_items = self.current_results[start_idx:end_idx]

        # Update badge
        self.result_badge.configure(text=f"{total} Leads (Seite {self.current_page}/{total_pages})")

        # Create table
        self.create_table(page_items, start_idx)

        # Update pagination controls
        self.update_pagination_controls()

    def create_table(self, companies, start_idx):
        """Create modern table view"""

        # Table container - nutzt komplette verfügbare Höhe
        table_frame = ctk.CTkFrame(self.results_container, fg_color=ModernColors.CARD_BG, corner_radius=15)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        header_frame = ctk.CTkFrame(table_frame, fg_color=ModernColors.BG_SECONDARY, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)

        # Define columns: (text, width)
        columns = [
            ("☐", 40),
            ("#", 50),
            ("Name", 180),
            ("Vorname", 120),
            ("Nachname", 120),
            ("E-Mail", 180),
            ("Telefon", 130),
            ("Website", 200),
            ("Kompliment", 250),
            ("Rating", 80),
            ("Reviews", 80),
            ("Status", 100),
            ("Aktionen", 100)
        ]

        # Create header
        for col_idx, (col_text, col_width) in enumerate(columns):
            header_label = ctk.CTkLabel(
                header_frame,
                text=col_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY,
                width=col_width,
                anchor="w" if col_idx > 1 else "center"
            )
            header_label.grid(row=0, column=col_idx, padx=8, pady=8, sticky="w")

        # Master checkbox for select all
        self.master_checkbox_var = ctk.BooleanVar()
        master_checkbox = ctk.CTkCheckBox(
            header_frame,
            text="",
            variable=self.master_checkbox_var,
            width=20,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=4,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.toggle_all_current_page
        )
        master_checkbox.grid(row=0, column=0, padx=10, pady=8)

        # Scrollable content - nimmt volle verfügbare Höhe
        content_frame = ctk.CTkScrollableFrame(
            table_frame,
            fg_color="transparent",
            scrollbar_button_color=ModernColors.ACCENT_PRIMARY,
            scrollbar_button_hover_color=ModernColors.ACCENT_SECONDARY,
            height=600  # Mindesthöhe für bessere Sichtbarkeit
        )
        content_frame.pack(fill="both", expand=True, padx=0, pady=(1, 0))

        # Create rows
        for idx, company in enumerate(companies):
            row_idx = start_idx + idx + 1
            self.create_table_row(content_frame, company, row_idx, idx)

    def create_table_row(self, parent, company, index, row_num):
        """Create a single table row"""

        # Row frame with alternating colors - KLEINERE HÖHE für mehr Zeilen
        row_bg = ModernColors.CARD_BG if row_num % 2 == 0 else ModernColors.BG_SECONDARY
        row_frame = ctk.CTkFrame(parent, fg_color=row_bg, corner_radius=0, height=35)
        row_frame.pack(fill="x", padx=0, pady=0)
        row_frame.pack_propagate(False)

        # Store reference
        self.card_widgets[company.id] = row_frame

        # Selection state
        if company.id not in self.selected_items:
            self.selected_items[company.id] = ctk.BooleanVar()

        checkbox_var = self.selected_items[company.id]

        # Grid layout for cells - REDUZIERTES PADDING
        # Checkbox
        checkbox = ctk.CTkCheckBox(
            row_frame,
            text="",
            variable=checkbox_var,
            width=20,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=4,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY
        )
        checkbox.grid(row=0, column=0, padx=10, pady=6)

        # Index - KOMPAKT
        index_label = ctk.CTkLabel(
            row_frame,
            text=f"{index}",
            font=ctk.CTkFont(size=10),
            text_color=ModernColors.TEXT_MUTED,
            width=50,
            anchor="center"
        )
        index_label.grid(row=0, column=1, padx=5, pady=6, sticky="w")

        # Name (clickable) - KOMPAKT
        name_text = (company.name or "N/A")[:25]
        name_label = ctk.CTkLabel(
            row_frame,
            text=name_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ModernColors.ACCENT_PRIMARY,
            width=180,
            anchor="w",
            cursor="hand2"
        )
        name_label.grid(row=0, column=2, padx=5, pady=6, sticky="w")
        name_label.bind("<Button-1>", lambda e: self.show_lead_details(company))

        # Vorname - KOMPAKT
        first_name_text = (company.first_name or "-")[:15]
        first_name_label = ctk.CTkLabel(
            row_frame,
            text=first_name_text,
            font=ctk.CTkFont(size=10),
            text_color=ModernColors.TEXT_SECONDARY,
            width=120,
            anchor="w"
        )
        first_name_label.grid(row=0, column=3, padx=5, pady=6, sticky="w")

        # Nachname - KOMPAKT
        last_name_text = (company.last_name or "-")[:15]
        last_name_label = ctk.CTkLabel(
            row_frame,
            text=last_name_text,
            font=ctk.CTkFont(size=10),
            text_color=ModernColors.TEXT_SECONDARY,
            width=120,
            anchor="w"
        )
        last_name_label.grid(row=0, column=4, padx=5, pady=6, sticky="w")

        # E-Mail - KOMPAKT
        email_text = (company.email or "-")[:25]
        email_label = ctk.CTkLabel(
            row_frame,
            text=email_text,
            font=ctk.CTkFont(size=10),
            text_color=ModernColors.TEXT_SECONDARY,
            width=180,
            anchor="w"
        )
        email_label.grid(row=0, column=5, padx=5, pady=6, sticky="w")

        # Telefon - KOMPAKT
        phone_text = (company.phone or "-")[:15]
        phone_label = ctk.CTkLabel(
            row_frame,
            text=phone_text,
            font=ctk.CTkFont(size=10),
            text_color=ModernColors.TEXT_SECONDARY,
            width=130,
            anchor="w"
        )
        phone_label.grid(row=0, column=6, padx=5, pady=6, sticky="w")

        # Website - KOMPAKT
        website_text = (company.website or "-")[:30]
        website_label = ctk.CTkLabel(
            row_frame,
            text=website_text,
            font=ctk.CTkFont(size=9),
            text_color=ModernColors.TEXT_MUTED,
            width=200,
            anchor="w"
        )
        website_label.grid(row=0, column=7, padx=5, pady=6, sticky="w")

        # Kompliment - KOMPAKT
        compliment_text = (company.compliment or "-")[:40] + "..." if company.compliment and len(company.compliment) > 40 else (company.compliment or "-")
        compliment_label = ctk.CTkLabel(
            row_frame,
            text=compliment_text,
            font=ctk.CTkFont(size=9),
            text_color=ModernColors.TEXT_SECONDARY,
            width=250,
            anchor="w"
        )
        compliment_label.grid(row=0, column=8, padx=5, pady=6, sticky="w")

        # Rating - KOMPAKT
        rating_text = f"{company.rating:.1f}" if company.rating else "-"
        rating_label = ctk.CTkLabel(
            row_frame,
            text=rating_text,
            font=ctk.CTkFont(size=10),
            text_color=ModernColors.ACCENT_WARNING,
            width=80,
            anchor="center"
        )
        rating_label.grid(row=0, column=9, padx=5, pady=6, sticky="w")

        # Reviews - KOMPAKT mit Info-Button
        reviews_container = ctk.CTkFrame(row_frame, fg_color="transparent", width=80)
        reviews_container.grid(row=0, column=10, padx=5, pady=6, sticky="ew")

        reviews_text = str(company.review_count) if company.review_count else "-"
        reviews_label = ctk.CTkLabel(
            reviews_container,
            text=reviews_text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY,
            width=35,
            anchor="center"
        )
        reviews_label.pack(side="left", padx=(5, 0))

        # Info-Button für Review-Keywords
        if company.review_keywords:
            info_btn = ctk.CTkButton(
                reviews_container,
                text="📋",
                font=ctk.CTkFont(size=9),
                width=22,
                height=18,
                corner_radius=4,
                fg_color=ModernColors.ACCENT_PRIMARY,
                hover_color=ModernColors.ACCENT_SECONDARY,
                command=lambda c=company: self.show_review_keywords_dialog(c)
            )
            info_btn.pack(side="left", padx=(2, 0))

        # Status - KOMPAKT
        has_names = company.first_name and company.last_name
        has_compliment = company.compliment

        if has_names and has_compliment:
            status_text = "✅"
            status_color = ModernColors.ACCENT_SUCCESS
        elif not has_names:
            status_text = "⚠️"
            status_color = ModernColors.ACCENT_WARNING
        elif not has_compliment:
            status_text = "⚠️"
            status_color = ModernColors.ACCENT_WARNING
        else:
            status_text = "-"
            status_color = ModernColors.TEXT_MUTED

        status_label = ctk.CTkLabel(
            row_frame,
            text=status_text,
            font=ctk.CTkFont(size=10),
            text_color=status_color,
            width=100,
            anchor="center"
        )
        status_label.grid(row=0, column=11, padx=5, pady=6, sticky="w")

        # Actions button - KOMPAKT
        btn_actions = ctk.CTkButton(
            row_frame,
            text="⋮",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=30,
            height=23,
            corner_radius=4,
            fg_color="transparent",
            hover_color=ModernColors.CARD_HOVER,
            command=lambda: self.show_lead_details(company)
        )
        btn_actions.grid(row=0, column=12, padx=5, pady=6)

    def toggle_all_current_page(self):
        """Toggle all checkboxes on current page"""
        state = self.master_checkbox_var.get()

        # Get current page companies
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.current_results))
        page_items = self.current_results[start_idx:end_idx]

        for company in page_items:
            if company.id in self.selected_items:
                self.selected_items[company.id].set(state)

    def create_lead_card(self, company, index):
        """Create optimized lead card - Simplified version for performance"""

        # Status
        has_names = company.first_name and company.last_name
        has_compliment = company.compliment

        if has_names and has_compliment:
            status_color = ModernColors.ACCENT_SUCCESS
            status_text = "✅"
        elif not has_names:
            status_color = ModernColors.ACCENT_WARNING
            status_text = "⚠️"
        elif not has_compliment:
            status_color = ModernColors.ACCENT_WARNING
            status_text = "⚠️"
        else:
            status_color = ModernColors.TEXT_MUTED
            status_text = "—"

        # Card - Single frame only
        card = ctk.CTkFrame(
            self.results_container,
            fg_color=ModernColors.CARD_BG,
            corner_radius=12,
            border_width=2,
            border_color=ModernColors.CARD_BG
        )
        card.pack(fill="x", padx=12, pady=6)

        # Store card reference
        self.card_widgets[company.id] = card

        # Selection state
        if company.id not in self.selected_items:
            self.selected_items[company.id] = ctk.BooleanVar()

        checkbox_var = self.selected_items[company.id]

        # Simple hover effect (no callbacks for better performance)
        def update_card_style(*args):
            if checkbox_var.get():
                card.configure(border_color=ModernColors.ACCENT_PRIMARY, border_width=2)
            else:
                card.configure(border_color=ModernColors.CARD_BG, border_width=2)

        checkbox_var.trace('w', update_card_style)

        # Content in one frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)

        # Single row layout
        # Checkbox
        checkbox = ctk.CTkCheckBox(
            content,
            text="",
            variable=checkbox_var,
            width=24,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=6,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY
        )
        checkbox.pack(side="left", padx=(0, 10))

        # Index
        index_label = ctk.CTkLabel(
            content,
            text=f"#{index}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ModernColors.TEXT_MUTED,
            width=35
        )
        index_label.pack(side="left", padx=(0, 8))

        # Name (clickable)
        name_text = (company.name or "N/A")[:40]
        name_label = ctk.CTkLabel(
            content,
            text=name_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY,
            cursor="hand2",
            anchor="w"
        )
        name_label.pack(side="left", padx=(0, 15))
        name_label.bind("<Button-1>", lambda e: self.show_lead_details(company))

        # Compact info
        info_parts = []
        if company.first_name or company.last_name:
            info_parts.append(f"👤 {company.first_name or ''} {company.last_name or ''}")
        if company.rating:
            info_parts.append(f"⭐{company.rating:.1f}")
        if company.phone:
            info_parts.append("📱")

        if info_parts:
            info_label = ctk.CTkLabel(
                content,
                text=" • ".join(info_parts)[:60],
                font=ctk.CTkFont(size=11),
                text_color=ModernColors.TEXT_SECONDARY,
                anchor="w"
            )
            info_label.pack(side="left", padx=(0, 10))

        # Status badge
        status_badge = ctk.CTkLabel(
            content,
            text=status_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white",
            fg_color=status_color,
            corner_radius=6,
            width=30,
            height=25
        )
        status_badge.pack(side="right")

    # ===========================
    # Filter Methods (same as before but adapted)
    # ===========================

    def update_rating_label(self, value):
        """Update rating label"""
        self.rating_value_label.configure(text=f"{float(value):.1f} ⭐")

    def on_main_category_change(self, choice):
        """Handle main category change"""
        if choice == "Alle" or choice not in self.category_hierarchy:
            self.sub_cat_menu.configure(values=["Alle"])
            self.sub_cat_var.set("Alle")
            self.specific_cat_menu.configure(values=["Alle"])
            self.specific_cat_var.set("Alle")
        else:
            sub_cats = ["Alle"] + list(self.category_hierarchy[choice].keys())
            self.sub_cat_menu.configure(values=sub_cats)
            self.sub_cat_var.set("Alle")
            self.specific_cat_menu.configure(values=["Alle"])
            self.specific_cat_var.set("Alle")

    def on_sub_category_change(self, choice):
        """Handle sub category change"""
        main_cat = self.main_cat_var.get()
        if choice == "Alle" or main_cat not in self.category_hierarchy:
            self.specific_cat_menu.configure(values=["Alle"])
            self.specific_cat_var.set("Alle")
        else:
            if choice in self.category_hierarchy[main_cat]:
                specific_cats = ["Alle"] + self.category_hierarchy[main_cat][choice]
                self.specific_cat_menu.configure(values=specific_cats)
                self.specific_cat_var.set("Alle")

    def schedule_live_filter(self):
        """Live search with debouncing"""
        if self.filter_timer:
            self.after_cancel(self.filter_timer)
        self.filter_timer = self.after(500, self.apply_filters)

    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.display_results()

    def next_page(self):
        """Go to next page"""
        total = len(self.current_results)
        total_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)

        if self.current_page < total_pages:
            self.current_page += 1
            self.display_results()

    def update_pagination_controls(self):
        """Update pagination button states"""
        if not self.current_results:
            self.btn_prev_page.configure(state="disabled")
            self.btn_next_page.configure(state="disabled")
            self.page_info_label.configure(text="Seite 0 / 0")
            return

        total = len(self.current_results)
        total_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)

        # Update label
        self.page_info_label.configure(text=f"Seite {self.current_page} / {total_pages}")

        # Update buttons
        if self.current_page <= 1:
            self.btn_prev_page.configure(state="disabled")
        else:
            self.btn_prev_page.configure(state="normal")

        if self.current_page >= total_pages:
            self.btn_next_page.configure(state="disabled")
        else:
            self.btn_next_page.configure(state="normal")

    def apply_filters(self):
        """Apply filters and update results"""
        try:
            # Reset to first page when applying new filters
            self.current_page = 1
            query = self.session.query(CompanyV3)

            # Quick search
            quick_search = self.quick_search_var.get().strip()
            if quick_search:
                search_pattern = f"%{quick_search}%"
                query = query.filter(
                    or_(
                        CompanyV3.name.like(search_pattern),
                        CompanyV3.website.like(search_pattern)
                    )
                )

            # Category
            specific_cat = self.specific_cat_var.get()
            if specific_cat and specific_cat != "Alle":
                query = query.filter(CompanyV3.main_category == specific_cat)

            # Rating
            min_rating = float(self.rating_var.get())
            if min_rating > 0:
                query = query.filter(CompanyV3.rating >= min_rating)

            # Reviews
            try:
                min_reviews = int(self.reviews_var.get())
                if min_reviews > 0:
                    query = query.filter(CompanyV3.review_count >= min_reviews)
            except ValueError:
                pass

            # Location
            location_text = self.location_var.get().strip()
            if location_text:
                query = query.filter(CompanyV3.address.ilike(f"%{location_text}%"))

            # Phone
            if self.has_phone_var.get():
                query = query.filter(
                    and_(
                        CompanyV3.phone.isnot(None),
                        CompanyV3.phone != ""
                    )
                )

            # Website
            if self.has_website_var.get():
                query = query.filter(
                    and_(
                        CompanyV3.website.isnot(None),
                        CompanyV3.website != ""
                    )
                )

            # Limit
            try:
                limit = int(self.limit_var.get())
                limit = max(1, min(limit, 1000))
            except ValueError:
                limit = 100

            # Execute
            query = query.order_by(CompanyV3.rating.desc(), CompanyV3.review_count.desc())
            query = query.limit(limit)

            self.current_results = query.all()
            self.display_results()

        except Exception as e:
            print(f"Filter error: {e}")
            import traceback
            traceback.print_exc()

    def reset_filters(self):
        """Reset all filters"""
        self.quick_search_var.set("")
        self.main_cat_var.set("Alle")
        self.sub_cat_var.set("Alle")
        self.specific_cat_var.set("Alle")
        self.rating_var.set(0)
        self.reviews_var.set("0")
        self.location_var.set("")
        self.has_phone_var.set(False)
        self.has_website_var.set(False)
        self.limit_var.set("100")
        self.apply_filters()

    def filter_complete_workflow(self):
        """Filter complete workflow - OPTIMIERT: SQL statt Python-Filter"""
        query = self.session.query(CompanyV3).filter(
            and_(
                CompanyV3.first_name.isnot(None),
                CompanyV3.first_name != "",
                CompanyV3.last_name.isnot(None),
                CompanyV3.last_name != "",
                CompanyV3.compliment.isnot(None),
                CompanyV3.compliment != ""
            )
        ).order_by(CompanyV3.rating.desc()).limit(1000)
        self.current_results = query.all()
        self.display_results()

    def filter_no_names(self):
        """Filter no names - OPTIMIERT: SQL statt Python-Filter"""
        query = self.session.query(CompanyV3).filter(
            or_(
                CompanyV3.first_name.is_(None),
                CompanyV3.first_name == "",
                CompanyV3.last_name.is_(None),
                CompanyV3.last_name == ""
            )
        ).order_by(CompanyV3.rating.desc()).limit(1000)
        self.current_results = query.all()
        self.display_results()

    def filter_no_compliment(self):
        """Filter no compliment - OPTIMIERT: SQL statt Python-Filter"""
        query = self.session.query(CompanyV3).filter(
            or_(
                CompanyV3.compliment.is_(None),
                CompanyV3.compliment == ""
            )
        ).order_by(CompanyV3.rating.desc()).limit(1000)
        self.current_results = query.all()
        self.display_results()

    def filter_rating_range(self, min_rating, max_rating):
        """Filter mit Rating-Range (Min-Max) - OPTIMIERT: SQL statt Python-Filter"""
        query = self.session.query(CompanyV3).filter(
            and_(
                CompanyV3.rating.isnot(None),
                CompanyV3.rating >= min_rating,
                CompanyV3.rating <= max_rating
            )
        ).order_by(CompanyV3.rating.desc(), CompanyV3.review_count.desc()).limit(1000)
        self.current_results = query.all()
        self.display_results()

    def select_all(self):
        """Select all items"""
        for company_id, checkbox_var in self.selected_items.items():
            checkbox_var.set(True)

    def deselect_all(self):
        """Deselect all items"""
        for company_id, checkbox_var in self.selected_items.items():
            checkbox_var.set(False)

    def refresh_table(self):
        """Refresh table by reapplying filters"""
        try:
            # Invalidiere Query-Cache
            self.category_cache_time = 0

            # Wende Filter neu an (lädt Daten aus DB)
            self.apply_filters()

            # Zeige kurze Bestätigung
            self.result_badge.configure(
                text=f"🔄 Aktualisiert - {len(self.current_results)} Leads"
            )

            # Nach 2 Sekunden normal anzeigen
            def reset_badge():
                total = len(self.current_results)
                total_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)
                self.result_badge.configure(
                    text=f"{total} Leads (Seite {self.current_page}/{total_pages})"
                )

            self.after(2000, reset_badge)

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Aktualisieren:\n{str(e)}")

    def delete_selected(self):
        """Delete selected items"""
        # Get selected company IDs
        selected_ids = [
            company_id for company_id, checkbox_var in self.selected_items.items()
            if checkbox_var.get()
        ]

        if not selected_ids:
            messagebox.showinfo("Keine Auswahl", "Bitte wähle mindestens einen Lead aus.")
            return

        # Confirm deletion
        count = len(selected_ids)
        result = messagebox.askyesno(
            "Löschen bestätigen",
            f"Möchtest du wirklich {count} Lead{'s' if count > 1 else ''} löschen?\n\nDiese Aktion kann nicht rückgängig gemacht werden!"
        )

        if not result:
            return

        try:
            # Delete from database
            for company_id in selected_ids:
                company = self.session.query(CompanyV3).filter_by(id=company_id).first()
                if company:
                    self.session.delete(company)

            self.session.commit()

            # Remove from UI state
            for company_id in selected_ids:
                if company_id in self.selected_items:
                    del self.selected_items[company_id]
                if company_id in self.card_widgets:
                    del self.card_widgets[company_id]

            # Refresh display
            self.apply_filters()

            messagebox.showinfo("Erfolg", f"{count} Lead{'s' if count > 1 else ''} erfolgreich gelöscht!")

        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Fehler", f"Fehler beim Löschen: {str(e)}")

    def show_lead_details(self, company):
        """Show detailed view of a lead in a popup"""
        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"Lead Details - {company.name or 'N/A'}")
        detail_window.geometry("900x700")
        detail_window.transient(self)
        detail_window.grab_set()

        # Make it modal and centered
        detail_window.update_idletasks()
        x = (detail_window.winfo_screenwidth() // 2) - (900 // 2)
        y = (detail_window.winfo_screenheight() // 2) - (700 // 2)
        detail_window.geometry(f"900x700+{x}+{y}")

        # Main container with scrolling
        main_frame = ctk.CTkScrollableFrame(
            detail_window,
            fg_color=ModernColors.BG_PRIMARY
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        title = ctk.CTkLabel(
            header,
            text=company.name or "N/A",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header,
            text=f"ID: {company.id} | {company.website or 'Keine Website'}",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY
        )
        subtitle.pack(anchor="w", pady=(5, 0))

        # Action buttons
        action_bar = ctk.CTkFrame(main_frame, fg_color=ModernColors.CARD_BG, corner_radius=12)
        action_bar.pack(fill="x", pady=(0, 20))

        btn_frame = ctk.CTkFrame(action_bar, fg_color="transparent")
        btn_frame.pack(padx=20, pady=15)

        btn_edit = ctk.CTkButton(
            btn_frame,
            text="✏️ Bearbeiten",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=lambda: self.edit_lead(company, detail_window)
        )
        btn_edit.pack(side="left", padx=(0, 10))

        btn_generate_compliment = ctk.CTkButton(
            btn_frame,
            text="💬 Kompliment generieren",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color="#059669",
            command=lambda: self.generate_compliment_for_lead(company, detail_window)
        )
        btn_generate_compliment.pack(side="left", padx=(0, 10))

        btn_scrape_contact = ctk.CTkButton(
            btn_frame,
            text="📇 Kontaktdaten",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_WARNING,
            hover_color="#d97706",
            command=lambda: self.scrape_contact_for_lead(company, detail_window)
        )
        btn_scrape_contact.pack(side="left", padx=(0, 10))

        # Nur anzeigen wenn Kompliment vorhanden
        if company.compliment:
            btn_delete_compliment = ctk.CTkButton(
                btn_frame,
                text="🗑️ Kompliment löschen",
                font=ctk.CTkFont(size=14, weight="bold"),
                height=40,
                corner_radius=10,
                fg_color="#ef4444",
                hover_color="#dc2626",
                command=lambda: self.delete_single_compliment(company, detail_window)
            )
            btn_delete_compliment.pack(side="left")

        # Details sections
        self.add_detail_section(main_frame, "📊 Basis-Informationen", {
            "Name": company.name,
            "Website": company.website,
            "Telefon": company.phone,
            "E-Mail": company.email,
            "Beschreibung": company.description
        })

        self.add_detail_section(main_frame, "👤 Kontaktperson", {
            "Vorname": company.first_name,
            "Nachname": company.last_name,
            "Vollständiger Name": f"{company.first_name or ''} {company.last_name or ''}".strip() or "N/A"
        })

        self.add_detail_section(main_frame, "🏢 Kategorien & Tags", {
            "Hauptkategorie": company.main_category,
            "Branchen": ", ".join(company.industries) if company.industries else "N/A",
            "Sub-Branchen": ", ".join(company.sub_industries) if company.sub_industries else "N/A",
            "Technologien": ", ".join(company.technologies) if company.technologies else "N/A",
            "Sprachen": ", ".join(company.languages) if company.languages else "N/A"
        })

        self.add_detail_section(main_frame, "📍 Standort", {
            "Land": company.country,
            "Stadt": company.city,
            "PLZ": company.zip_code,
            "Bundesland": company.state,
            "Adresse": company.address
        })

        self.add_detail_section(main_frame, "⭐ Bewertungen", {
            "Rating": f"{company.rating:.1f} ⭐" if company.rating else "N/A",
            "Anzahl Reviews": str(company.review_count) if company.review_count else "N/A"
        })

        # Review Keywords section - zeigt welche Rezensionen verwendet werden
        if company.review_keywords:
            keywords_frame = ctk.CTkFrame(main_frame, fg_color=ModernColors.CARD_BG, corner_radius=12)
            keywords_frame.pack(fill="x", pady=(0, 15))

            section_title = ctk.CTkLabel(
                keywords_frame,
                text="📝 Rezensions-Details (für Kompliment verwendet)",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
            section_title.pack(anchor="w", padx=20, pady=(15, 10))

            info_label = ctk.CTkLabel(
                keywords_frame,
                text="Diese Rezensions-Keywords werden verwendet um personalisierte Komplimente zu erstellen:",
                font=ctk.CTkFont(size=11),
                text_color=ModernColors.TEXT_SECONDARY,
                wraplength=800,
                justify="left"
            )
            info_label.pack(anchor="w", padx=20, pady=(0, 10))

            keywords_text = ctk.CTkTextbox(
                keywords_frame,
                height=120,
                font=ctk.CTkFont(size=12),
                fg_color=ModernColors.BG_SECONDARY,
                wrap="word"
            )
            keywords_text.pack(fill="x", padx=20, pady=(0, 15))
            keywords_text.insert("1.0", company.review_keywords)
            keywords_text.configure(state="disabled")

        # Compliment section
        if company.compliment:
            compliment_frame = ctk.CTkFrame(main_frame, fg_color=ModernColors.CARD_BG, corner_radius=12)
            compliment_frame.pack(fill="x", pady=(0, 15))

            section_title = ctk.CTkLabel(
                compliment_frame,
                text="💬 Generiertes Kompliment",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
            section_title.pack(anchor="w", padx=20, pady=(15, 10))

            compliment_text = ctk.CTkTextbox(
                compliment_frame,
                height=100,
                font=ctk.CTkFont(size=13),
                fg_color=ModernColors.BG_SECONDARY,
                wrap="word"
            )
            compliment_text.pack(fill="x", padx=20, pady=(0, 15))
            compliment_text.insert("1.0", company.compliment)
            compliment_text.configure(state="disabled")

        # Close button
        btn_close = ctk.CTkButton(
            main_frame,
            text="Schließen",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color="transparent",
            border_width=2,
            border_color=ModernColors.BORDER,
            hover_color=ModernColors.CARD_HOVER,
            command=detail_window.destroy
        )
        btn_close.pack(fill="x", pady=(10, 0))

    def add_detail_section(self, parent, title, data):
        """Add a detail section to the popup"""
        section = ctk.CTkFrame(parent, fg_color=ModernColors.CARD_BG, corner_radius=12)
        section.pack(fill="x", pady=(0, 15))

        section_title = ctk.CTkLabel(
            section,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        section_title.pack(anchor="w", padx=20, pady=(15, 10))

        for key, value in data.items():
            if value:
                row = ctk.CTkFrame(section, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=3)

                label = ctk.CTkLabel(
                    row,
                    text=f"{key}:",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=ModernColors.TEXT_SECONDARY,
                    width=150,
                    anchor="w"
                )
                label.pack(side="left")

                value_label = ctk.CTkLabel(
                    row,
                    text=str(value),
                    font=ctk.CTkFont(size=13),
                    text_color=ModernColors.TEXT_PRIMARY,
                    anchor="w"
                )
                value_label.pack(side="left", fill="x", expand=True)

        # Padding at bottom
        ctk.CTkLabel(section, text="", height=15).pack()

    def edit_lead(self, company, parent_window=None):
        """Open edit dialog for a lead"""
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Lead bearbeiten - {company.name or 'N/A'}")
        edit_window.geometry("800x600")
        if parent_window:
            edit_window.transient(parent_window)
        edit_window.grab_set()

        # Center window
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (edit_window.winfo_screenheight() // 2) - (600 // 2)
        edit_window.geometry(f"800x600+{x}+{y}")

        # Main frame
        main_frame = ctk.CTkScrollableFrame(edit_window, fg_color=ModernColors.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Lead bearbeiten",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        title.pack(pady=(0, 20))

        # Form fields
        fields = {}

        def add_field(label_text, field_name, current_value="", multiline=False):
            field_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=8)

            label = ctk.CTkLabel(
                field_frame,
                text=label_text,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=ModernColors.TEXT_SECONDARY,
                anchor="w"
            )
            label.pack(anchor="w", pady=(0, 5))

            if multiline:
                entry = ctk.CTkTextbox(
                    field_frame,
                    height=80,
                    font=ctk.CTkFont(size=13),
                    fg_color=ModernColors.CARD_BG
                )
                entry.pack(fill="x")
                if current_value:
                    entry.insert("1.0", str(current_value))
            else:
                entry = ctk.CTkEntry(
                    field_frame,
                    height=40,
                    font=ctk.CTkFont(size=13),
                    fg_color=ModernColors.CARD_BG
                )
                entry.pack(fill="x")
                if current_value:
                    entry.insert(0, str(current_value))

            fields[field_name] = entry

        # Add all fields
        add_field("Firmenname", "name", company.name)
        add_field("Website", "website", company.website)
        add_field("Telefon", "phone", company.phone)
        add_field("E-Mail", "email", company.email)
        add_field("Vorname", "first_name", company.first_name)
        add_field("Nachname", "last_name", company.last_name)
        add_field("Stadt", "city", company.city)
        add_field("PLZ", "zip_code", company.zip_code)
        add_field("Adresse", "address", company.address, multiline=True)
        add_field("Beschreibung", "description", company.description, multiline=True)

        # Save button
        def save_changes():
            try:
                # Update company object
                for field_name, entry in fields.items():
                    if isinstance(entry, ctk.CTkTextbox):
                        value = entry.get("1.0", "end-1c").strip()
                    else:
                        value = entry.get().strip()

                    if value:
                        setattr(company, field_name, value)
                    else:
                        setattr(company, field_name, None)

                # Save to database
                self.session.commit()

                messagebox.showinfo("Erfolg", "Lead erfolgreich aktualisiert!")
                edit_window.destroy()

                # Refresh parent window if exists
                if parent_window:
                    parent_window.destroy()
                    self.show_lead_details(company)

                # Refresh main view
                self.apply_filters()

            except Exception as e:
                self.session.rollback()
                messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 Speichern",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color="#059669",
            command=save_changes
        )
        btn_save.pack(side="left", expand=True, fill="x", padx=(0, 10))

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Abbrechen",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color="transparent",
            border_width=2,
            border_color=ModernColors.BORDER,
            hover_color=ModernColors.CARD_HOVER,
            command=edit_window.destroy
        )
        btn_cancel.pack(side="left", expand=True, fill="x")

    def show_prompt_selection_dialog_bulk(self, count):
        """Zeigt Dialog zur Prompt-Auswahl für Bulk-Generierung"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Prompt auswählen")
        dialog.geometry("800x700")
        dialog.grab_set()

        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (700 // 2)
        dialog.geometry(f"800x700+{x}+{y}")

        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text=f"🎯 Prompt für {count} Leads auswählen",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        title_label.pack(padx=20, pady=(20, 10))

        info_label = ctk.CTkLabel(
            dialog,
            text="Wähle einen vorhandenen Prompt oder schreibe einen eigenen Custom Prompt\nDieser wird für ALLE ausgewählten Leads verwendet.",
            font=ctk.CTkFont(size=12),
            text_color=ModernColors.TEXT_SECONDARY,
            justify="center"
        )
        info_label.pack(padx=20, pady=(0, 20))

        # Scrollable Frame für Prompts
        prompts_frame = ctk.CTkScrollableFrame(
            dialog,
            fg_color=ModernColors.BG_SECONDARY,
            corner_radius=15,
            height=300
        )
        prompts_frame.pack(padx=20, pady=(0, 10), fill="both", expand=True)

        # Lade verfügbare Prompts
        all_prompts = self.prompt_manager.prompts.get('prompts', [])

        selected_prompt = {"value": None}

        # Radio buttons für jeden Prompt
        prompt_var = ctk.StringVar(value="")

        for prompt in all_prompts:
            prompt_frame = ctk.CTkFrame(prompts_frame, fg_color=ModernColors.CARD_BG, corner_radius=10)
            prompt_frame.pack(padx=10, pady=5, fill="x")

            radio = ctk.CTkRadioButton(
                prompt_frame,
                text="",
                variable=prompt_var,
                value=prompt['id'],
                fg_color=ModernColors.ACCENT_PRIMARY,
                hover_color=ModernColors.ACCENT_SECONDARY
            )
            radio.pack(side="left", padx=10, pady=10)

            info_frame = ctk.CTkFrame(prompt_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)

            name_label = ctk.CTkLabel(
                info_frame,
                text=prompt['name'],
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY,
                anchor="w"
            )
            name_label.pack(anchor="w")

            desc_label = ctk.CTkLabel(
                info_frame,
                text=prompt.get('description', ''),
                font=ctk.CTkFont(size=11),
                text_color=ModernColors.TEXT_MUTED,
                anchor="w"
            )
            desc_label.pack(anchor="w")

        # Custom Prompt Option
        custom_frame = ctk.CTkFrame(prompts_frame, fg_color=ModernColors.CARD_BG, corner_radius=10)
        custom_frame.pack(padx=10, pady=5, fill="x")

        custom_radio = ctk.CTkRadioButton(
            custom_frame,
            text="",
            variable=prompt_var,
            value="CUSTOM",
            fg_color=ModernColors.ACCENT_WARNING,
            hover_color="#d97706"
        )
        custom_radio.pack(side="left", padx=10, pady=10)

        custom_info_frame = ctk.CTkFrame(custom_frame, fg_color="transparent")
        custom_info_frame.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)

        custom_name_label = ctk.CTkLabel(
            custom_info_frame,
            text="✏️ Custom Prompt (selbst schreiben)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.ACCENT_WARNING,
            anchor="w"
        )
        custom_name_label.pack(anchor="w")

        custom_desc_label = ctk.CTkLabel(
            custom_info_frame,
            text="Schreibe deinen eigenen personalisierten Prompt für maximale Personalisierung",
            font=ctk.CTkFont(size=11),
            text_color=ModernColors.TEXT_MUTED,
            anchor="w"
        )
        custom_desc_label.pack(anchor="w")

        # Custom Prompt Textfeld (nur sichtbar wenn custom gewählt)
        custom_textbox_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        custom_textbox_frame.pack(padx=20, pady=(10, 0), fill="both")
        custom_textbox_frame.pack_forget()  # Erstmal verstecken

        # System Prompt (optional)
        system_prompt_label = ctk.CTkLabel(
            custom_textbox_frame,
            text="🤖 System-Prompt (optional - definiert das KI-Verhalten):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=ModernColors.ACCENT_PRIMARY,
            justify="left"
        )
        system_prompt_label.pack(anchor="w", padx=5, pady=(0, 3))

        system_textbox = ctk.CTkTextbox(
            custom_textbox_frame,
            height=60,
            fg_color=ModernColors.CARD_BG,
            border_width=2,
            border_color=ModernColors.ACCENT_PRIMARY,
            font=ctk.CTkFont(size=11)
        )
        system_textbox.pack(fill="x", padx=5, pady=(0, 10))
        system_textbox.insert("1.0", "Du bist ein Experte für authentische, personalisierte B2B-Kommunikation.")

        # User Prompt
        custom_textbox_label = ctk.CTkLabel(
            custom_textbox_frame,
            text="📝 User-Prompt (DEIN Prompt - wird für jeden Lead ausgeführt):\n\nPlatzhalter: {name}, {rating}, {reviews}, {review_keywords}, {category}, {city}, {description}, {first_name}, {last_name}, {email}, {website}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY,
            justify="left"
        )
        custom_textbox_label.pack(anchor="w", padx=5, pady=(0, 3))

        custom_textbox = ctk.CTkTextbox(
            custom_textbox_frame,
            height=100,
            fg_color=ModernColors.CARD_BG,
            border_width=2,
            border_color=ModernColors.ACCENT_WARNING,
            font=ctk.CTkFont(size=11)
        )
        custom_textbox.pack(fill="both", expand=True, padx=5)

        # Beispiel-Text
        custom_textbox.insert("1.0", """Erstelle ein kurzes, authentisches Kompliment für {name}.

Verfügbare Informationen:
- Rating: {rating} Sterne ({reviews} Bewertungen)
- Stadt: {city}
- Rezensionen: {review_keywords}

Schreibe 2-3 Sätze, die sich auf KONKRETE Details aus den Rezensionen beziehen. Sei authentisch, nicht übertrieben.""")

        def on_prompt_change(*args):
            """Zeige Custom Textbox wenn CUSTOM gewählt"""
            if prompt_var.get() == "CUSTOM":
                custom_textbox_frame.pack(padx=20, pady=(10, 0), fill="both")
            else:
                custom_textbox_frame.pack_forget()

        prompt_var.trace('w', on_prompt_change)

        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(padx=20, pady=20, fill="x")

        def on_cancel():
            selected_prompt["value"] = None
            dialog.destroy()

        def on_ok():
            if not prompt_var.get():
                messagebox.showwarning("Keine Auswahl", "Bitte wähle einen Prompt aus!")
                return

            if prompt_var.get() == "CUSTOM":
                custom_text = custom_textbox.get("1.0", "end-1c").strip()
                system_text = system_textbox.get("1.0", "end-1c").strip()
                if not custom_text:
                    messagebox.showwarning("Kein Prompt", "Bitte schreibe einen Custom Prompt!")
                    return
                # Speichere Custom Prompt MIT System-Prompt
                selected_prompt["value"] = {
                    "type": "custom",
                    "prompt": custom_text,
                    "system_prompt": system_text  # NEU: System-Prompt
                }
            else:
                selected_prompt["value"] = {
                    "type": "predefined",
                    "prompt_id": prompt_var.get()
                }

            dialog.destroy()

        btn_cancel = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            font=ctk.CTkFont(size=14),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.CARD_BG,
            hover_color=ModernColors.CARD_HOVER,
            command=on_cancel
        )
        btn_cancel.pack(side="left", expand=True, fill="x", padx=(0, 10))

        btn_ok = ctk.CTkButton(
            button_frame,
            text="✅ Prompt verwenden",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color="#059669",
            command=on_ok
        )
        btn_ok.pack(side="left", expand=True, fill="x")

        dialog.wait_window()
        return selected_prompt["value"]

    def show_prompt_selection_dialog(self, company, parent_window=None):
        """Zeigt Dialog zur Prompt-Auswahl"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Prompt auswählen")
        dialog.geometry("700x600")
        if parent_window:
            dialog.transient(parent_window)
        dialog.grab_set()

        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"700x600+{x}+{y}")

        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text=f"🎯 Prompt für {company.name} auswählen",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        title_label.pack(padx=20, pady=(20, 10))

        info_label = ctk.CTkLabel(
            dialog,
            text="Wähle einen vorhandenen Prompt oder schreibe einen eigenen Custom Prompt",
            font=ctk.CTkFont(size=12),
            text_color=ModernColors.TEXT_SECONDARY
        )
        info_label.pack(padx=20, pady=(0, 20))

        # Scrollable Frame für Prompts
        prompts_frame = ctk.CTkScrollableFrame(
            dialog,
            fg_color=ModernColors.BG_SECONDARY,
            corner_radius=15,
            height=300
        )
        prompts_frame.pack(padx=20, pady=(0, 10), fill="both", expand=True)

        # Lade verfügbare Prompts
        all_prompts = self.prompt_manager.prompts.get('prompts', [])

        selected_prompt = {"value": None}

        # Radio buttons für jeden Prompt
        prompt_var = ctk.StringVar(value="")

        for prompt in all_prompts:
            prompt_frame = ctk.CTkFrame(prompts_frame, fg_color=ModernColors.CARD_BG, corner_radius=10)
            prompt_frame.pack(padx=10, pady=5, fill="x")

            radio = ctk.CTkRadioButton(
                prompt_frame,
                text="",
                variable=prompt_var,
                value=prompt['id'],
                fg_color=ModernColors.ACCENT_PRIMARY,
                hover_color=ModernColors.ACCENT_SECONDARY
            )
            radio.pack(side="left", padx=10, pady=10)

            info_frame = ctk.CTkFrame(prompt_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)

            name_label = ctk.CTkLabel(
                info_frame,
                text=prompt['name'],
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY,
                anchor="w"
            )
            name_label.pack(anchor="w")

            desc_label = ctk.CTkLabel(
                info_frame,
                text=prompt.get('description', ''),
                font=ctk.CTkFont(size=11),
                text_color=ModernColors.TEXT_MUTED,
                anchor="w"
            )
            desc_label.pack(anchor="w")

        # Custom Prompt Option
        custom_frame = ctk.CTkFrame(prompts_frame, fg_color=ModernColors.CARD_BG, corner_radius=10)
        custom_frame.pack(padx=10, pady=5, fill="x")

        custom_radio = ctk.CTkRadioButton(
            custom_frame,
            text="",
            variable=prompt_var,
            value="CUSTOM",
            fg_color=ModernColors.ACCENT_WARNING,
            hover_color="#d97706"
        )
        custom_radio.pack(side="left", padx=10, pady=10)

        custom_info_frame = ctk.CTkFrame(custom_frame, fg_color="transparent")
        custom_info_frame.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)

        custom_name_label = ctk.CTkLabel(
            custom_info_frame,
            text="✏️ Custom Prompt (selbst schreiben)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.ACCENT_WARNING,
            anchor="w"
        )
        custom_name_label.pack(anchor="w")

        custom_desc_label = ctk.CTkLabel(
            custom_info_frame,
            text="Schreibe deinen eigenen personalisierten Prompt",
            font=ctk.CTkFont(size=11),
            text_color=ModernColors.TEXT_MUTED,
            anchor="w"
        )
        custom_desc_label.pack(anchor="w")

        # Custom Prompt Textfeld (nur sichtbar wenn custom gewählt)
        custom_textbox_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        custom_textbox_frame.pack(padx=20, pady=(10, 0), fill="both")
        custom_textbox_frame.pack_forget()  # Erstmal verstecken

        custom_textbox_label = ctk.CTkLabel(
            custom_textbox_frame,
            text="📝 Dein Custom Prompt (verwende Platzhalter: {name}, {rating}, {reviews}, {category}):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        custom_textbox_label.pack(anchor="w", padx=5, pady=(0, 5))

        custom_textbox = ctk.CTkTextbox(
            custom_textbox_frame,
            height=100,
            fg_color=ModernColors.CARD_BG,
            border_width=2,
            border_color=ModernColors.ACCENT_WARNING,
            font=ctk.CTkFont(size=11)
        )
        custom_textbox.pack(fill="both", expand=True, padx=5)

        def on_prompt_change(*args):
            """Zeige Custom Textbox wenn CUSTOM gewählt"""
            if prompt_var.get() == "CUSTOM":
                custom_textbox_frame.pack(padx=20, pady=(10, 0), fill="both")
            else:
                custom_textbox_frame.pack_forget()

        prompt_var.trace('w', on_prompt_change)

        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(padx=20, pady=20, fill="x")

        def on_cancel():
            selected_prompt["value"] = None
            dialog.destroy()

        def on_ok():
            if not prompt_var.get():
                messagebox.showwarning("Keine Auswahl", "Bitte wähle einen Prompt aus!")
                return

            if prompt_var.get() == "CUSTOM":
                custom_text = custom_textbox.get("1.0", "end-1c").strip()
                if not custom_text:
                    messagebox.showwarning("Kein Prompt", "Bitte schreibe einen Custom Prompt!")
                    return
                # Speichere Custom Prompt temporär
                selected_prompt["value"] = {
                    "type": "custom",
                    "prompt": custom_text
                }
            else:
                selected_prompt["value"] = {
                    "type": "predefined",
                    "prompt_id": prompt_var.get()
                }

            dialog.destroy()

        btn_cancel = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            font=ctk.CTkFont(size=14),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.CARD_BG,
            hover_color=ModernColors.CARD_HOVER,
            command=on_cancel
        )
        btn_cancel.pack(side="left", expand=True, fill="x", padx=(0, 10))

        btn_ok = ctk.CTkButton(
            button_frame,
            text="Generieren",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color="#059669",
            command=on_ok
        )
        btn_ok.pack(side="left", expand=True, fill="x")

        dialog.wait_window()
        return selected_prompt["value"]

    def generate_compliment_for_lead(self, company, parent_window=None):
        """Generate compliment for a single lead"""
        if not company.website:
            messagebox.showwarning("Keine Website", "Lead hat keine Website. Kompliment-Generierung nicht möglich.")
            return

        # SCHRITT 1: Prompt-Auswahl Dialog zeigen
        selected_prompt = self.show_prompt_selection_dialog(company, parent_window)

        if not selected_prompt:
            # User hat abgebrochen
            return

        # SCHRITT 2: Generierung mit ausgewähltem Prompt
        self._execute_compliment_generation(company, selected_prompt, parent_window)

    def _execute_compliment_generation(self, company, prompt_selection, parent_window=None):
        """Execute compliment generation with selected prompt"""
        # Show loading dialog
        loading = ctk.CTkToplevel(self)
        loading.title("Kompliment wird generiert...")
        loading.geometry("400x150")
        if parent_window:
            loading.transient(parent_window)
        loading.grab_set()

        # Center window
        loading.update_idletasks()
        x = (loading.winfo_screenwidth() // 2) - (400 // 2)
        y = (loading.winfo_screenheight() // 2) - (150 // 2)
        loading.geometry(f"400x150+{x}+{y}")

        label = ctk.CTkLabel(
            loading,
            text="🤖 Generiere Kompliment...\nBitte warten...",
            font=ctk.CTkFont(size=16),
            text_color=ModernColors.TEXT_PRIMARY
        )
        label.pack(expand=True)

        progress = ctk.CTkProgressBar(loading, mode="indeterminate")
        progress.pack(padx=40, pady=(0, 20), fill="x")
        progress.start()

        def generate():
            try:
                # Generate compliment mit ausgewähltem Prompt
                if prompt_selection['type'] == 'custom':
                    # Custom Prompt - mit optionalem System-Prompt
                    custom_prompt = prompt_selection.get('prompt', '')
                    system_prompt = prompt_selection.get('system_prompt', '')
                    result = self._generate_with_custom_prompt(company, custom_prompt, system_prompt)
                else:
                    # Predefined Prompt
                    result = self.compliment_generator.generate_compliment(company, prompt_id=prompt_selection['prompt_id'])

                if result and result.get('compliment'):
                    company.compliment = result['compliment']
                    company.confidence_score = result.get('confidence_score', 0)
                    company.overstatement_score = result.get('overstatement_score', 0)
                    company.has_team = result.get('has_team', False)
                    company.compliment_generated_at = datetime.now()

                    self.session.commit()

                    loading.destroy()
                    messagebox.showinfo("Erfolg", "Kompliment erfolgreich generiert!")

                    # Refresh parent window
                    if parent_window:
                        parent_window.destroy()
                        self.show_lead_details(company)

                    self.apply_filters()
                else:
                    loading.destroy()
                    messagebox.showerror("Fehler", "Kompliment konnte nicht generiert werden.")

            except Exception as e:
                loading.destroy()
                messagebox.showerror("Fehler", f"Fehler bei der Generierung: {str(e)}")

        # Run in thread to avoid blocking UI
        import threading
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    def scrape_contact_for_lead(self, company, parent_window=None):
        """Scrape contact data (names + email) for a single lead - kombiniert in einem Durchlauf"""
        if not company.website:
            messagebox.showwarning("Keine Website", "Lead hat keine Website. Kontaktdaten-Scraping nicht möglich.")
            return

        # Show loading dialog
        loading = ctk.CTkToplevel(self)
        loading.title("Kontaktdaten werden gescraped...")
        loading.geometry("400x150")
        if parent_window:
            loading.transient(parent_window)
        loading.grab_set()

        # Center window
        loading.update_idletasks()
        x = (loading.winfo_screenwidth() // 2) - (400 // 2)
        y = (loading.winfo_screenheight() // 2) - (150 // 2)
        loading.geometry(f"400x150+{x}+{y}")

        label = ctk.CTkLabel(
            loading,
            text="📇 Scrape Kontaktdaten...\n(Namen + E-Mail in einem Durchlauf)",
            font=ctk.CTkFont(size=16),
            text_color=ModernColors.TEXT_PRIMARY
        )
        label.pack(expand=True)

        progress = ctk.CTkProgressBar(loading, mode="indeterminate")
        progress.pack(padx=40, pady=(0, 20), fill="x")
        progress.start()

        def scrape():
            try:
                # Kombinierte Methode - scrape Namen + E-Mail aus Impressum in einem Durchlauf
                result = self.impressum_scraper.scrape_all_contact_data(company.website)

                found_name = result.get('found_name', False)
                found_email = result.get('found_email', False)

                if found_name or found_email:
                    msg_parts = []

                    if found_name:
                        company.first_name = result.get('first_name')
                        company.last_name = result.get('last_name')
                        msg_parts.append(f"👤 Name: {result.get('first_name')} {result.get('last_name')}")

                    if found_email:
                        company.email = result.get('email')
                        msg_parts.append(f"📧 E-Mail: {result.get('email')}")

                    self.session.commit()

                    loading.destroy()
                    messagebox.showinfo(
                        "Erfolg",
                        f"Kontaktdaten erfolgreich gescraped:\n\n" + "\n".join(msg_parts)
                    )

                    # Refresh parent window
                    if parent_window:
                        parent_window.destroy()
                        self.show_lead_details(company)

                    self.apply_filters()
                else:
                    loading.destroy()
                    messagebox.showwarning("Keine Kontaktdaten gefunden", "Auf der Website wurden keine Kontaktdaten im Impressum gefunden.")

            except Exception as e:
                loading.destroy()
                messagebox.showerror("Fehler", f"Fehler beim Scraping: {str(e)}")

        # Run in thread to avoid blocking UI
        import threading
        thread = threading.Thread(target=scrape, daemon=True)
        thread.start()

    def show_review_keywords_dialog(self, company):
        """Zeigt Review-Keywords in einem Dialog an"""
        if not company.review_keywords:
            messagebox.showinfo("Keine Review-Keywords", "Für diesen Lead sind keine Review-Keywords vorhanden.")
            return

        # Dialog erstellen
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Rezensions-Details - {company.name or 'Lead'}")
        dialog.geometry("700x500")
        dialog.transient(self)
        dialog.grab_set()

        # Center window
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"700x500+{x}+{y}")

        # Main frame
        main_frame = ctk.CTkFrame(dialog, fg_color=ModernColors.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_label = ctk.CTkLabel(
            main_frame,
            text="📝 Rezensions-Details",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        header_label.pack(pady=(0, 10))

        # Company info
        info_frame = ctk.CTkFrame(main_frame, fg_color=ModernColors.CARD_BG, corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 15))

        company_label = ctk.CTkLabel(
            info_frame,
            text=f"🏢 {company.name or 'N/A'}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        company_label.pack(anchor="w", padx=15, pady=(10, 5))

        rating_label = ctk.CTkLabel(
            info_frame,
            text=f"⭐ {company.rating:.1f} | 📊 {company.review_count} Reviews" if company.rating and company.review_count else "Keine Bewertungen",
            font=ctk.CTkFont(size=13),
            text_color=ModernColors.TEXT_SECONDARY
        )
        rating_label.pack(anchor="w", padx=15, pady=(0, 10))

        # Description
        desc_label = ctk.CTkLabel(
            main_frame,
            text="Diese Rezensions-Keywords werden verwendet um personalisierte Komplimente zu erstellen.\nDie KI analysiert diese Details um authentische Komplimente zu formulieren.",
            font=ctk.CTkFont(size=12),
            text_color=ModernColors.TEXT_SECONDARY,
            wraplength=640,
            justify="left"
        )
        desc_label.pack(anchor="w", pady=(0, 15))

        # Keywords textbox
        keywords_label = ctk.CTkLabel(
            main_frame,
            text="📋 Review-Keywords:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        keywords_label.pack(anchor="w", pady=(0, 5))

        keywords_textbox = ctk.CTkTextbox(
            main_frame,
            height=220,
            font=ctk.CTkFont(size=12),
            fg_color=ModernColors.CARD_BG,
            wrap="word"
        )
        keywords_textbox.pack(fill="both", expand=True, pady=(0, 15))
        keywords_textbox.insert("1.0", company.review_keywords)
        keywords_textbox.configure(state="disabled")

        # Close button
        btn_close = ctk.CTkButton(
            main_frame,
            text="Schließen",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=dialog.destroy
        )
        btn_close.pack(fill="x")

    def delete_single_compliment(self, company, parent_window=None):
        """Delete compliment for a single lead"""
        if not company.compliment:
            messagebox.showinfo("Kein Kompliment", "Dieser Lead hat kein Kompliment zum Löschen.")
            return

        # Bestätigung
        result = messagebox.askyesno(
            "Kompliment löschen",
            f"⚠️ ACHTUNG ⚠️\n\n"
            f"Möchtest du wirklich das Kompliment von '{company.name or 'diesem Lead'}' löschen?\n\n"
            f"Diese Aktion kann NICHT rückgängig gemacht werden!"
        )

        if not result:
            return

        try:
            # Lösche Kompliment und alle zugehörigen Felder
            company.compliment = None
            company.confidence_score = None
            company.overstatement_score = None
            company.has_team = None
            company.compliment_generated_at = None

            self.session.commit()

            messagebox.showinfo(
                "Erfolgreich gelöscht",
                f"✅ Das Kompliment wurde erfolgreich gelöscht."
            )

            # Refresh parent window
            if parent_window:
                parent_window.destroy()
                self.show_lead_details(company)

            # Refresh main view
            self.apply_filters()

        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Fehler", f"Fehler beim Löschen:\n{str(e)}")

    def export_to_csv(self):
        """Export current results to CSV"""
        if not self.current_results:
            messagebox.showinfo("Keine Daten", "Keine Leads zum Exportieren vorhanden.")
            return

        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if not file_path:
            return

        try:
            # Prepare data
            data = []
            for company in self.current_results:
                data.append({
                    'ID': company.id,
                    'Name': company.name,
                    'E-Mail': company.email,
                    'Telefon': company.phone,
                    'Website': company.website,
                    'Vorname': company.first_name,
                    'Nachname': company.last_name,
                    'Hauptkategorie': company.main_category,
                    'Branchen': ', '.join(company.industries) if company.industries else '',
                    'Stadt': company.city,
                    'PLZ': company.zip_code,
                    'Adresse': company.address,
                    'Rating': company.rating,
                    'Anzahl_Reviews': company.review_count,
                    'Review_Keywords': company.review_keywords,
                    'Kompliment': company.compliment,
                    'Confidence_Score': company.confidence_score,
                    'Place_ID': company.place_id,
                    'Owner_Name': company.owner_name,
                    'Google_Maps_Link': company.link,
                    'Query': company.query,
                    'Competitors': company.competitors,
                    'Is_Spending_On_Ads': company.is_spending_on_ads,
                    'Beschreibung': company.description,
                    'LinkedIn': company.linkedin_url
                })

            # Create DataFrame and export
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')

            messagebox.showinfo("Erfolg", f"{len(data)} Leads erfolgreich exportiert nach:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Export: {str(e)}")

    def export_to_excel(self):
        """Export current results to Excel"""
        if not self.current_results:
            messagebox.showinfo("Keine Daten", "Keine Leads zum Exportieren vorhanden.")
            return

        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if not file_path:
            return

        try:
            # Prepare data
            data = []
            for company in self.current_results:
                data.append({
                    'ID': company.id,
                    'Name': company.name,
                    'E-Mail': company.email,
                    'Telefon': company.phone,
                    'Website': company.website,
                    'Vorname': company.first_name,
                    'Nachname': company.last_name,
                    'Hauptkategorie': company.main_category,
                    'Branchen': ', '.join(company.industries) if company.industries else '',
                    'Stadt': company.city,
                    'PLZ': company.zip_code,
                    'Adresse': company.address,
                    'Rating': company.rating,
                    'Anzahl_Reviews': company.review_count,
                    'Review_Keywords': company.review_keywords,
                    'Kompliment': company.compliment,
                    'Confidence_Score': company.confidence_score,
                    'Place_ID': company.place_id,
                    'Owner_Name': company.owner_name,
                    'Google_Maps_Link': company.link,
                    'Query': company.query,
                    'Competitors': company.competitors,
                    'Is_Spending_On_Ads': company.is_spending_on_ads,
                    'Beschreibung': company.description,
                    'LinkedIn': company.linkedin_url
                })

            # Create DataFrame and export to Excel
            df = pd.DataFrame(data)

            # Export with styling
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Leads')

                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Leads']

                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except (TypeError, AttributeError):
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            messagebox.showinfo("Erfolg", f"{len(data)} Leads erfolgreich exportiert nach:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Excel-Export: {str(e)}\n\nBitte installiere 'openpyxl': pip install openpyxl")

    # ===========================
    # Other Views (Placeholders)
    # ===========================

    def setup_upload_view(self):
        """Setup CSV upload view"""
        container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)

        # Header
        header = ctk.CTkLabel(
            container,
            text="📤 CSV Upload",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        header.pack(pady=(0, 30))

        # Info box
        info_frame = ctk.CTkFrame(container, fg_color=ModernColors.CARD_BG, corner_radius=15)
        info_frame.pack(fill="x", pady=(0, 30))

        info_label = ctk.CTkLabel(
            info_frame,
            text="💡 Tipp: Du kannst CSV-Dateien von Google Maps Scraper oder anderen Quellen hochladen.\n"
                 "Die CSV sollte mindestens eine 'website' Spalte enthalten.",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY,
            justify="left"
        )
        info_label.pack(padx=30, pady=20)

        # Upload area
        upload_frame = ctk.CTkFrame(
            container,
            fg_color=ModernColors.CARD_BG,
            corner_radius=20,
            border_width=3,
            border_color=ModernColors.BORDER
        )
        upload_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Drag & Drop area (visual only, actual upload via button)
        drop_area = ctk.CTkFrame(upload_frame, fg_color="transparent")
        drop_area.pack(expand=True, pady=80)

        icon_label = ctk.CTkLabel(
            drop_area,
            text="📁",
            font=ctk.CTkFont(size=80)
        )
        icon_label.pack()

        text_label = ctk.CTkLabel(
            drop_area,
            text="CSV-Datei auswählen",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        text_label.pack(pady=(20, 10))

        subtext_label = ctk.CTkLabel(
            drop_area,
            text="Klicke auf den Button unten, um eine CSV-Datei auszuwählen",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY
        )
        subtext_label.pack()

        # Upload button
        btn_upload = ctk.CTkButton(
            container,
            text="📁  CSV-Datei auswählen",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=12,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.upload_csv_file
        )
        btn_upload.pack(pady=(0, 10))

        # Recent uploads
        recent_frame = ctk.CTkFrame(container, fg_color=ModernColors.CARD_BG, corner_radius=15)
        recent_frame.pack(fill="x")

        recent_title = ctk.CTkLabel(
            recent_frame,
            text="📊 Datenbank-Status",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        recent_title.pack(anchor="w", padx=20, pady=(15, 10))

        total_count = self.session.query(CompanyV3).count()
        with_names_count = self.session.query(CompanyV3).filter(
            CompanyV3.first_name.isnot(None),
            CompanyV3.last_name.isnot(None)
        ).count()
        with_compliment_count = self.session.query(CompanyV3).filter(
            CompanyV3.compliment.isnot(None)
        ).count()

        stats_text = f"• Total Leads: {total_count}\n" \
                     f"• Mit Namen: {with_names_count}\n" \
                     f"• Mit Kompliment: {with_compliment_count}"

        stats_label = ctk.CTkLabel(
            recent_frame,
            text=stats_text,
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY,
            justify="left"
        )
        stats_label.pack(anchor="w", padx=20, pady=(0, 15))

    def upload_csv_file(self):
        """Upload and import CSV file"""
        file_path = filedialog.askopenfilename(
            title="CSV-Datei auswählen",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            # Read CSV
            df = pd.read_csv(file_path, encoding='utf-8-sig')

            # Check for required columns
            if 'website' not in df.columns:
                messagebox.showerror(
                    "Fehler",
                    "Die CSV-Datei muss mindestens eine 'website' Spalte enthalten!"
                )
                return

            # Show preview and confirmation
            preview_window = ctk.CTkToplevel(self)
            preview_window.title("CSV Import Vorschau")
            preview_window.geometry("800x600")
            preview_window.transient(self)
            preview_window.grab_set()

            # Center window
            preview_window.update_idletasks()
            x = (preview_window.winfo_screenwidth() // 2) - (800 // 2)
            y = (preview_window.winfo_screenheight() // 2) - (600 // 2)
            preview_window.geometry(f"800x600+{x}+{y}")

            # Main frame
            main_frame = ctk.CTkFrame(preview_window, fg_color=ModernColors.BG_PRIMARY)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Title
            title = ctk.CTkLabel(
                main_frame,
                text="CSV Import Vorschau",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
            title.pack(pady=(0, 20))

            # Info
            info_text = f"📊 {len(df)} Zeilen gefunden\n" \
                       f"📋 Spalten: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}"

            info_label = ctk.CTkLabel(
                main_frame,
                text=info_text,
                font=ctk.CTkFont(size=14),
                text_color=ModernColors.TEXT_SECONDARY,
                justify="left"
            )
            info_label.pack(pady=(0, 20))

            # Preview (first 5 rows)
            preview_text = ctk.CTkTextbox(
                main_frame,
                font=ctk.CTkFont(size=12, family="Courier"),
                fg_color=ModernColors.CARD_BG
            )
            preview_text.pack(fill="both", expand=True, pady=(0, 20))
            preview_text.insert("1.0", df.head(5).to_string())
            preview_text.configure(state="disabled")

            # Import button
            def do_import():
                preview_window.destroy()

                # Show progress
                progress_window = ctk.CTkToplevel(self)
                progress_window.title("Import läuft...")
                progress_window.geometry("400x150")
                progress_window.transient(self)
                progress_window.grab_set()

                # Center window
                progress_window.update_idletasks()
                x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
                y = (progress_window.winfo_screenheight() // 2) - (150 // 2)
                progress_window.geometry(f"400x150+{x}+{y}")

                label = ctk.CTkLabel(
                    progress_window,
                    text="📥 Importiere CSV...\nBitte warten...",
                    font=ctk.CTkFont(size=16),
                    text_color=ModernColors.TEXT_PRIMARY
                )
                label.pack(expand=True)

                progress = ctk.CTkProgressBar(progress_window, mode="indeterminate")
                progress.pack(padx=40, pady=(0, 20), fill="x")
                progress.start()

                def import_data():
                    try:
                        imported = 0
                        skipped = 0
                        imported_companies = []  # Track neu importierte Companies

                        for _, row in df.iterrows():
                            website = str(row.get('website', '')).strip()
                            if not website or website == 'nan':
                                skipped += 1
                                continue

                            # Check if exists
                            existing = self.session.query(CompanyV3).filter_by(website=website).first()
                            if existing:
                                skipped += 1
                                continue

                            # Parse categories
                            categories = []
                            categories_str = row.get('categories')
                            if pd.notna(categories_str) and categories_str:
                                categories = [c.strip() for c in str(categories_str).split(',')]

                            # Create new company - VOLLSTÄNDIGER IMPORT ALLER 22 FELDER!
                            company = CompanyV3(
                                # Basis
                                website=website,
                                name=row.get('name') if pd.notna(row.get('name')) else None,
                                description=row.get('description') if pd.notna(row.get('description')) else None,
                                phone=row.get('phone') if pd.notna(row.get('phone')) else None,

                                # Kontakt-Person (werden später gescraped)
                                first_name=None,
                                last_name=None,
                                email=None,

                                # Kategorien
                                main_category=row.get('main_category') if pd.notna(row.get('main_category')) else None,
                                industries=categories,

                                # Location
                                address=row.get('address') if pd.notna(row.get('address')) else None,
                                city=row.get('city') if pd.notna(row.get('city')) else None,
                                zip_code=row.get('zip_code') if pd.notna(row.get('zip_code')) else None,
                                state=row.get('state') if pd.notna(row.get('state')) else None,
                                country=row.get('country') if pd.notna(row.get('country')) else "Deutschland",

                                # Rating - WICHTIG: CSV hat 'reviews' nicht 'review_count'!
                                rating=float(row.get('rating')) if pd.notna(row.get('rating')) and row.get('rating') != '' else None,
                                review_count=int(row.get('reviews')) if pd.notna(row.get('reviews')) and str(row.get('reviews')).strip() != '' else None,

                                # CSV-spezifisch - ALLE FELDER!
                                place_id=row.get('place_id') if pd.notna(row.get('place_id')) else None,
                                owner_name=row.get('owner_name') if pd.notna(row.get('owner_name')) else None,
                                review_keywords=row.get('review_keywords') if pd.notna(row.get('review_keywords')) else None,
                                link=row.get('link') if pd.notna(row.get('link')) else None,
                                query=row.get('query') if pd.notna(row.get('query')) else None,
                                competitors=row.get('competitors') if pd.notna(row.get('competitors')) else None,
                                is_spending_on_ads=bool(row.get('is_spending_on_ads')) if pd.notna(row.get('is_spending_on_ads')) and str(row.get('is_spending_on_ads')).strip() != '' else None,
                                workday_timing=row.get('workday_timing') if pd.notna(row.get('workday_timing')) else None,
                                featured_image=row.get('featured_image') if pd.notna(row.get('featured_image')) else None,
                                can_claim=bool(row.get('can_claim')) if pd.notna(row.get('can_claim')) and str(row.get('can_claim')).strip() != '' else None,
                                is_temporarily_closed=bool(row.get('is_temporarily_closed')) if pd.notna(row.get('is_temporarily_closed')) and str(row.get('is_temporarily_closed')).strip() != '' else None,
                                closed_on=row.get('closed_on') if pd.notna(row.get('closed_on')) else None,
                                owner_profile_link=row.get('owner_profile_link') if pd.notna(row.get('owner_profile_link')) else None,

                                # Defaults
                                languages=[],
                                services=[],
                                custom_tags=[],
                                attributes={}
                            )

                            self.session.add(company)
                            imported_companies.append(company)  # Track für automatisches Scraping
                            imported += 1

                            # Batch commit alle 50 Zeilen
                            if imported % 50 == 0:
                                self.session.commit()

                        self.session.commit()

                        progress_window.destroy()

                        # Zeige Auswahl-Dialog für Scraping
                        if imported_companies:
                            self.show_scraping_choice_dialog(imported_companies, imported, skipped)
                        else:
                            messagebox.showinfo(
                                "Import erfolgreich",
                                f"✅ {imported} Leads erfolgreich importiert!\n"
                                f"⏭️ {skipped} Leads übersprungen (bereits vorhanden oder ungültig)"
                            )
                            self.switch_view("filter")
                            self.refresh_table()

                    except Exception as e:
                        self.session.rollback()
                        progress_window.destroy()
                        messagebox.showerror("Fehler", f"Fehler beim Import: {str(e)}")

                # Run in thread
                import threading
                thread = threading.Thread(target=import_data, daemon=True)
                thread.start()

            btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            btn_frame.pack(fill="x")

            btn_import = ctk.CTkButton(
                btn_frame,
                text="✅ Importieren",
                font=ctk.CTkFont(size=15, weight="bold"),
                height=45,
                corner_radius=10,
                fg_color=ModernColors.ACCENT_SUCCESS,
                hover_color="#059669",
                command=do_import
            )
            btn_import.pack(side="left", expand=True, fill="x", padx=(0, 10))

            btn_cancel = ctk.CTkButton(
                btn_frame,
                text="Abbrechen",
                font=ctk.CTkFont(size=15, weight="bold"),
                height=45,
                corner_radius=10,
                fg_color="transparent",
                border_width=2,
                border_color=ModernColors.BORDER,
                hover_color=ModernColors.CARD_HOVER,
                command=preview_window.destroy
            )
            btn_cancel.pack(side="left", expand=True, fill="x")

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Lesen der CSV-Datei:\n{str(e)}")

    def show_scraping_choice_dialog(self, imported_companies, imported_count, skipped_count):
        """Zeigt Dialog zur Auswahl was gescraped werden soll"""

        # Dialog erstellen
        choice_dialog = ctk.CTkToplevel(self)
        choice_dialog.title("Scraping-Optionen")
        choice_dialog.geometry("500x400")
        choice_dialog.transient(self)
        choice_dialog.grab_set()

        # Center window
        choice_dialog.update_idletasks()
        x = (choice_dialog.winfo_screenwidth() // 2) - (250)
        y = (choice_dialog.winfo_screenheight() // 2) - (200)
        choice_dialog.geometry(f"500x400+{x}+{y}")

        # Main frame
        main_frame = ctk.CTkFrame(choice_dialog, fg_color=ModernColors.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Import erfolgreich!",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ModernColors.ACCENT_SUCCESS
        )
        title.pack(pady=(0, 10))

        # Info
        info = ctk.CTkLabel(
            main_frame,
            text=f"✅ {imported_count} Leads importiert\n⏭️ {skipped_count} übersprungen\n\nWas möchtest du jetzt scrapen?",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY,
            justify="center"
        )
        info.pack(pady=(0, 20))

        # Buttons
        btn_nothing = ctk.CTkButton(
            main_frame,
            text="❌  Nichts scrapen - Nur importieren",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color="transparent",
            border_width=2,
            border_color=ModernColors.BORDER,
            hover_color=ModernColors.CARD_HOVER,
            command=lambda: self.start_scraping(choice_dialog, imported_companies, None)
        )
        btn_nothing.pack(fill="x", pady=(0, 10))

        btn_contact = ctk.CTkButton(
            main_frame,
            text="📇  Kontaktdaten scrapen (Namen + E-Mails in einem Durchlauf)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color="#059669",
            command=lambda: self.start_scraping(choice_dialog, imported_companies, "contact")
        )
        btn_contact.pack(fill="x", pady=(0, 10))

    def start_scraping(self, dialog, companies, scrape_type):
        """Startet das Scraping basierend auf der Auswahl"""
        dialog.destroy()

        if not scrape_type:
            # Nichts scrapen
            self.switch_view("filter")
            self.refresh_table()
            return

        # Progress window
        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Scraping läuft...")
        progress_window.geometry("500x200")
        progress_window.transient(self)
        progress_window.grab_set()

        # Center
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (250)
        y = (progress_window.winfo_screenheight() // 2) - (100)
        progress_window.geometry(f"500x200+{x}+{y}")

        # Progress label
        progress_label = ctk.CTkLabel(
            progress_window,
            text="🔍 Starte Scraping...",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        progress_label.pack(pady=(20, 10))

        # Counter label
        counter_label = ctk.CTkLabel(
            progress_window,
            text="0 / 0",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY
        )
        counter_label.pack(pady=(0, 10))

        # Progress bar
        progress_bar = ctk.CTkProgressBar(progress_window, mode="determinate", width=400)
        progress_bar.pack(padx=40, pady=(0, 20))
        progress_bar.set(0)

        def do_scraping():
            try:
                names_scraped = 0
                emails_scraped = 0
                total = len(companies)

                # Kontaktdaten scrapen (kombiniert - Namen + E-Mails in einem Durchlauf)
                if scrape_type == "contact":
                    progress_label.configure(text="📇 Scrape Kontaktdaten...")
                    impressum_scraper = ImpressumScraper()

                    for idx, company in enumerate(companies):
                        needs_name = not company.first_name or not company.last_name
                        needs_email = not company.email

                        if needs_name or needs_email:
                            try:
                                # Kombinierte Methode - scrape Impressum nur EINMAL
                                result = impressum_scraper.scrape_all_contact_data(company.website)

                                if result.get('found_name') and needs_name:
                                    company.first_name = result.get('first_name')
                                    company.last_name = result.get('last_name')
                                    names_scraped += 1

                                if result.get('found_email') and needs_email:
                                    company.email = result.get('email')
                                    emails_scraped += 1

                            except Exception as e:
                                print(f"Fehler bei {company.website}: {e}")

                        # Update progress
                        current = idx + 1
                        progress = current / total
                        progress_bar.set(progress)
                        counter_label.configure(text=f"Kontakte: {current} / {total}")
                        progress_window.update()

                        if current % 10 == 0:
                            self.session.commit()

                    self.session.commit()

                progress_window.destroy()

                # Success message
                msg = f"✅ Scraping abgeschlossen!\n\n"
                msg += f"📇 Kontaktdaten in einem Durchlauf gescraped:\n"
                msg += f"👤 {names_scraped} Namen gefunden\n"
                msg += f"📧 {emails_scraped} E-Mails gefunden"

                messagebox.showinfo("Scraping erfolgreich", msg)

                # Switch to filter view and refresh
                self.switch_view("filter")
                self.refresh_table()

            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Fehler", f"Fehler beim Scraping: {str(e)}")

        # Run in thread
        import threading
        thread = threading.Thread(target=do_scraping, daemon=True)
        thread.start()

    def setup_prompts_view(self):
        """Setup prompts view"""
        container = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)

        # Header
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 30))

        header = ctk.CTkLabel(
            header_frame,
            text="💬 Prompt Templates",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        header.pack(side="left")

        btn_new = ctk.CTkButton(
            header_frame,
            text="➕ Neuer Prompt",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.create_new_prompt
        )
        btn_new.pack(side="right")

        # Info
        info_frame = ctk.CTkFrame(container, fg_color=ModernColors.CARD_BG, corner_radius=15)
        info_frame.pack(fill="x", pady=(0, 30))

        info_label = ctk.CTkLabel(
            info_frame,
            text="💡 Hier kannst du Prompt-Templates für die Kompliment-Generierung verwalten.\n"
                 "Jeder Prompt kann individuell angepasst werden.",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY,
            justify="left"
        )
        info_label.pack(padx=30, pady=20)

        # Load prompts
        prompts_data = self.prompt_manager.prompts.get('prompts', [])

        for prompt in prompts_data:
            self.create_prompt_card(container, prompt)

    def create_prompt_card(self, parent, prompt):
        """Create a prompt card"""
        card = ctk.CTkFrame(parent, fg_color=ModernColors.CARD_BG, corner_radius=15)
        card.pack(fill="x", pady=(0, 15))

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text=prompt.get('name', 'Unnamed'),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        title.pack(side="left")

        # Edit button
        btn_edit = ctk.CTkButton(
            header,
            text="✏️ Bearbeiten",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=35,
            corner_radius=8,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=lambda: self.edit_prompt(prompt)
        )
        btn_edit.pack(side="right", padx=(0, 10))

        # Description
        if prompt.get('description'):
            desc = ctk.CTkLabel(
                card,
                text=prompt['description'],
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY,
                anchor="w"
            )
            desc.pack(anchor="w", padx=20, pady=(0, 10))

        # ID
        id_label = ctk.CTkLabel(
            card,
            text=f"ID: {prompt.get('id', 'N/A')}",
            font=ctk.CTkFont(size=12),
            text_color=ModernColors.TEXT_MUTED,
            anchor="w"
        )
        id_label.pack(anchor="w", padx=20, pady=(0, 15))

    def create_new_prompt(self):
        """Create a new prompt"""
        messagebox.showinfo("Feature", "Neuer Prompt erstellen - Feature coming soon!")

    def edit_prompt(self, prompt):
        """Edit a prompt"""
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Prompt bearbeiten - {prompt.get('name', 'N/A')}")
        edit_window.geometry("800x700")
        edit_window.transient(self)
        edit_window.grab_set()

        # Center window
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (edit_window.winfo_screenheight() // 2) - (700 // 2)
        edit_window.geometry(f"800x700+{x}+{y}")

        # Main frame
        main_frame = ctk.CTkScrollableFrame(edit_window, fg_color=ModernColors.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Prompt bearbeiten",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        title.pack(pady=(0, 20))

        # Fields
        fields = {}

        def add_field(label_text, field_name, current_value="", height=40):
            field_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=8)

            label = ctk.CTkLabel(
                field_frame,
                text=label_text,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=ModernColors.TEXT_SECONDARY,
                anchor="w"
            )
            label.pack(anchor="w", pady=(0, 5))

            if height > 40:
                entry = ctk.CTkTextbox(
                    field_frame,
                    height=height,
                    font=ctk.CTkFont(size=13),
                    fg_color=ModernColors.CARD_BG
                )
                entry.pack(fill="x")
                if current_value:
                    entry.insert("1.0", str(current_value))
            else:
                entry = ctk.CTkEntry(
                    field_frame,
                    height=height,
                    font=ctk.CTkFont(size=13),
                    fg_color=ModernColors.CARD_BG
                )
                entry.pack(fill="x")
                if current_value:
                    entry.insert(0, str(current_value))

            fields[field_name] = entry

        add_field("Name", "name", prompt.get('name', ''))
        add_field("Beschreibung", "description", prompt.get('description', ''))
        add_field("System Prompt", "system_prompt", prompt.get('system_prompt', ''), height=150)
        add_field("User Prompt Template", "user_prompt_template", prompt.get('user_prompt_template', ''), height=200)

        # Save button
        def save_changes():
            try:
                # Update prompt
                for field_name, entry in fields.items():
                    if isinstance(entry, ctk.CTkTextbox):
                        value = entry.get("1.0", "end-1c").strip()
                    else:
                        value = entry.get().strip()

                    prompt[field_name] = value

                # Save to file
                self.prompt_manager.save_prompts()

                messagebox.showinfo("Erfolg", "Prompt erfolgreich gespeichert!")
                edit_window.destroy()

                # Refresh view
                self.switch_view("prompts")

            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 Speichern",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_SUCCESS,
            hover_color="#059669",
            command=save_changes
        )
        btn_save.pack(side="left", expand=True, fill="x", padx=(0, 10))

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Abbrechen",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color="transparent",
            border_width=2,
            border_color=ModernColors.BORDER,
            hover_color=ModernColors.CARD_HOVER,
            command=edit_window.destroy
        )
        btn_cancel.pack(side="left", expand=True, fill="x")

    def setup_api_view(self):
        """Setup API configuration view"""
        container = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)

        # Header
        header = ctk.CTkLabel(
            container,
            text="🤖 API Konfiguration",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        header.pack(pady=(0, 30))

        # Info
        info_frame = ctk.CTkFrame(container, fg_color=ModernColors.CARD_BG, corner_radius=15)
        info_frame.pack(fill="x", pady=(0, 30))

        info_label = ctk.CTkLabel(
            info_frame,
            text="💡 Konfiguriere hier deine API-Keys für verschiedene LLM-Provider.\n"
                 "Unterstützt werden: DeepSeek, OpenAI, Anthropic und mehr.",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY,
            justify="left"
        )
        info_label.pack(padx=30, pady=20)

        # Current API
        current_api = self.api_config.get('active_api', 'deepseek')
        current_card = ctk.CTkFrame(container, fg_color=ModernColors.ACCENT_SUCCESS, corner_radius=15)
        current_card.pack(fill="x", pady=(0, 30))

        current_label = ctk.CTkLabel(
            current_card,
            text=f"✅ Aktuell aktiv: {current_api.upper()}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        current_label.pack(padx=20, pady=15)

        # API Cards
        apis = self.api_config.get('apis', {})
        api_providers = ['deepseek', 'openai', 'anthropic', 'groq']

        for provider in api_providers:
            self.create_api_card(container, provider, apis.get(provider, {}), provider == current_api)

        # Save button
        btn_save = ctk.CTkButton(
            container,
            text="💾 Konfiguration speichern",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            corner_radius=12,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.save_api_config
        )
        btn_save.pack(fill="x", pady=(20, 0))

    def create_api_card(self, parent, provider, config, is_active):
        """Create an API configuration card"""
        card = ctk.CTkFrame(parent, fg_color=ModernColors.CARD_BG, corner_radius=15)
        card.pack(fill="x", pady=(0, 15))

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        icon_map = {
            'deepseek': '🤖',
            'openai': '🟢',
            'anthropic': '🟣',
            'groq': '⚡'
        }

        title = ctk.CTkLabel(
            header,
            text=f"{icon_map.get(provider, '🔹')} {provider.upper()}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        title.pack(side="left")

        if is_active:
            badge = ctk.CTkLabel(
                header,
                text="AKTIV",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white",
                fg_color=ModernColors.ACCENT_SUCCESS,
                corner_radius=8,
                padx=15,
                pady=5
            )
            badge.pack(side="right")

        # API Key field
        key_frame = ctk.CTkFrame(card, fg_color="transparent")
        key_frame.pack(fill="x", padx=20, pady=(0, 10))

        key_label = ctk.CTkLabel(
            key_frame,
            text="API Key:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ModernColors.TEXT_SECONDARY,
            width=100,
            anchor="w"
        )
        key_label.pack(side="left", padx=(0, 10))

        key_entry = ctk.CTkEntry(
            key_frame,
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color=ModernColors.BG_SECONDARY,
            placeholder_text="API Key eingeben...",
            show="•"
        )
        key_entry.pack(side="left", fill="x", expand=True)

        # Load existing key
        if config.get('api_key'):
            key_entry.insert(0, config['api_key'])

        # Store reference
        if not hasattr(self, 'api_key_entries'):
            self.api_key_entries = {}
        self.api_key_entries[provider] = key_entry

        # Activate button
        btn_activate = ctk.CTkButton(
            card,
            text="🔄 Als aktiv setzen",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=35,
            corner_radius=8,
            fg_color=ModernColors.ACCENT_PRIMARY if not is_active else ModernColors.TEXT_MUTED,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=lambda p=provider: self.set_active_api(p)
        )
        btn_activate.pack(padx=20, pady=(0, 15))

    def set_active_api(self, provider):
        """Set active API provider"""
        self.api_config['active_api'] = provider
        self.save_api_config()
        self.switch_view("api")

    def save_api_config(self):
        """Save API configuration"""
        try:
            # Update API keys
            for provider, entry in self.api_key_entries.items():
                api_key = entry.get().strip()
                if api_key:
                    if provider not in self.api_config['apis']:
                        self.api_config['apis'][provider] = {}
                    self.api_config['apis'][provider]['api_key'] = api_key

            # Save to file
            with open('api_config.json', 'w', encoding='utf-8') as f:
                json.dump(self.api_config, f, indent=2)

            messagebox.showinfo("Erfolg", "API-Konfiguration erfolgreich gespeichert!")

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")

    def setup_settings_view(self):
        """Setup settings view"""
        container = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)

        # Header
        header = ctk.CTkLabel(
            container,
            text="⚙️ Einstellungen",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        header.pack(pady=(0, 30))

        # Database section
        db_section = ctk.CTkFrame(container, fg_color=ModernColors.CARD_BG, corner_radius=15)
        db_section.pack(fill="x", pady=(0, 20))

        db_title = ctk.CTkLabel(
            db_section,
            text="🗄️ Datenbank",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        db_title.pack(anchor="w", padx=20, pady=(15, 10))

        total_count = self.session.query(CompanyV3).count()

        db_info = ctk.CTkLabel(
            db_section,
            text=f"Total Leads in Datenbank: {total_count}",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY,
            anchor="w"
        )
        db_info.pack(anchor="w", padx=20, pady=(0, 15))

        btn_backup = ctk.CTkButton(
            db_section,
            text="💾 Backup erstellen",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_PRIMARY,
            hover_color=ModernColors.ACCENT_SECONDARY,
            command=self.create_database_backup
        )
        btn_backup.pack(padx=20, pady=(0, 10), fill="x")

        btn_clear_db = ctk.CTkButton(
            db_section,
            text="🗑️ Datenbank leeren",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=ModernColors.ACCENT_DANGER,
            hover_color="#dc2626",
            command=self.clear_database
        )
        btn_clear_db.pack(padx=20, pady=(0, 15), fill="x")

        # About section
        about_section = ctk.CTkFrame(container, fg_color=ModernColors.CARD_BG, corner_radius=15)
        about_section.pack(fill="x", pady=(0, 20))

        about_title = ctk.CTkLabel(
            about_section,
            text="ℹ️ Über",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        about_title.pack(anchor="w", padx=20, pady=(15, 10))

        about_text = "Lead-Tool V4.0 - Modern Edition\n" \
                    "Powered by CustomTkinter\n\n" \
                    "© 2025 - All rights reserved"

        about_label = ctk.CTkLabel(
            about_section,
            text=about_text,
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY,
            justify="left"
        )
        about_label.pack(anchor="w", padx=20, pady=(0, 15))

    def create_database_backup(self):
        """Create database backup"""
        try:
            import shutil
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"lead_enrichment_v3_backup_{timestamp}.db"

            shutil.copy2("lead_enrichment_v3.db", backup_name)

            messagebox.showinfo(
                "Backup erstellt",
                f"Backup erfolgreich erstellt:\n{backup_name}"
            )

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Erstellen des Backups:\n{str(e)}")

    def clear_database(self):
        """Clear all leads from database"""
        total_count = self.session.query(CompanyV3).count()

        if total_count == 0:
            messagebox.showinfo("Datenbank leer", "Die Datenbank ist bereits leer.")
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "⚠️ WARNUNG - Datenbank leeren",
            f"Möchtest du wirklich ALLE {total_count} Leads aus der Datenbank löschen?\n\n"
            f"⚠️ Diese Aktion kann NICHT rückgängig gemacht werden!\n\n"
            f"💡 Tipp: Erstelle vorher ein Backup!",
            icon='warning'
        )

        if not result:
            return

        # Double confirmation
        result2 = messagebox.askyesno(
            "Wirklich löschen?",
            f"Bist du dir SICHER?\n\n"
            f"Alle {total_count} Leads werden permanent gelöscht!",
            icon='warning'
        )

        if not result2:
            return

        try:
            # Delete all companies
            self.session.query(CompanyV3).delete()
            self.session.commit()

            # Reset selection
            self.selected_items.clear()
            self.card_widgets.clear()
            self.current_results = []

            messagebox.showinfo(
                "Datenbank geleert",
                f"✅ Alle {total_count} Leads wurden erfolgreich gelöscht.\n\n"
                f"Die Datenbank ist jetzt leer."
            )

            # Refresh view
            self.switch_view("filter")

        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Fehler", f"Fehler beim Leeren der Datenbank:\n{str(e)}")

    def bulk_generate_compliments(self):
        """Generate compliments for selected leads"""
        # Get selected companies
        selected_companies = [
            c for c in self.current_results
            if c.id in self.selected_items and self.selected_items[c.id].get()
        ]

        if not selected_companies:
            messagebox.showinfo("Keine Auswahl", "Bitte wähle mindestens einen Lead aus.")
            return

        # Filter companies with websites
        companies_with_website = [c for c in selected_companies if c.website]

        if not companies_with_website:
            messagebox.showwarning(
                "Keine Websites",
                "Keiner der ausgewählten Leads hat eine Website.\nKompliment-Generierung nicht möglich."
            )
            return

        count = len(companies_with_website)

        # SCHRITT 1: Prompt-Auswahl Dialog zeigen
        selected_prompt = self.show_prompt_selection_dialog_bulk(count)

        if not selected_prompt:
            # User hat abgebrochen
            return

        # Speichere ausgewählten Prompt für Bulk-Verarbeitung
        self.current_bulk_prompt = selected_prompt

        # SCHRITT 2: Bestätigung
        result = messagebox.askyesno(
            "Komplimente generieren",
            f"Möchtest du für {count} Lead{'s' if count > 1 else ''} Komplimente generieren?\n\n"
            f"Dies kann einige Minuten dauern."
        )

        if not result:
            return

        # Create progress window
        self.show_bulk_progress_window(
            title="Komplimente generieren",
            total=count,
            operation_func=self.process_bulk_compliments,
            companies=companies_with_website
        )

    def bulk_delete_compliments(self):
        """Delete compliments for selected leads"""
        # Get selected companies
        selected_companies = [
            c for c in self.current_results
            if c.id in self.selected_items and self.selected_items[c.id].get()
        ]

        if not selected_companies:
            messagebox.showinfo("Keine Auswahl", "Bitte wähle mindestens einen Lead aus.")
            return

        # Filter companies that have compliments
        companies_with_compliments = [c for c in selected_companies if c.compliment]

        if not companies_with_compliments:
            messagebox.showinfo(
                "Keine Komplimente",
                "Keiner der ausgewählten Leads hat ein Kompliment.\nNichts zu löschen."
            )
            return

        count = len(companies_with_compliments)
        result = messagebox.askyesno(
            "Komplimente löschen",
            f"⚠️ ACHTUNG ⚠️\n\n"
            f"Möchtest du wirklich die Komplimente von {count} Lead{'s' if count > 1 else ''} löschen?\n\n"
            f"Diese Aktion kann NICHT rückgängig gemacht werden!"
        )

        if not result:
            return

        # Delete compliments
        try:
            deleted_count = 0
            for company in companies_with_compliments:
                company.compliment = None
                company.confidence_score = None
                company.overstatement_score = None
                company.has_team = None
                company.compliment_generated_at = None
                deleted_count += 1

            self.session.commit()

            messagebox.showinfo(
                "Erfolgreich gelöscht",
                f"✅ Komplimente von {deleted_count} Lead{'s' if deleted_count > 1 else ''} wurden gelöscht."
            )

            # Refresh view
            self.apply_filters()

        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Fehler", f"Fehler beim Löschen:\n{str(e)}")

    def show_bulk_progress_window(self, title, total, operation_func, companies):
        """Show progress window for bulk operations"""
        progress_window = ctk.CTkToplevel(self)
        progress_window.title(title)
        progress_window.geometry("600x300")
        progress_window.transient(self)
        progress_window.grab_set()

        # Center window
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (300 // 2)
        progress_window.geometry(f"600x300+{x}+{y}")

        # Sichere Widget-Update Funktion
        def safe_widget_update(widget, update_func):
            """
            Führt Widget-Update nur aus wenn Widget noch existiert.
            Verhindert TclError bei geschlossenem Fenster.
            """
            try:
                if widget and widget.winfo_exists():
                    update_func()
            except Exception:
                pass  # Widget wurde zerstört, ignorieren

        # Main frame
        main_frame = ctk.CTkFrame(progress_window, fg_color=ModernColors.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        title_label.pack(pady=(0, 20))

        # Progress info
        progress_info = ctk.CTkLabel(
            main_frame,
            text=f"0 / {total} bearbeitet",
            font=ctk.CTkFont(size=16),
            text_color=ModernColors.TEXT_SECONDARY
        )
        progress_info.pack(pady=(0, 10))

        # Progress bar
        progress_bar = ctk.CTkProgressBar(
            main_frame,
            height=20,
            corner_radius=10,
            progress_color=ModernColors.ACCENT_PRIMARY
        )
        progress_bar.pack(fill="x", pady=(0, 20))
        progress_bar.set(0)

        # Status label
        status_label = ctk.CTkLabel(
            main_frame,
            text="Starte...",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_MUTED
        )
        status_label.pack(pady=(0, 20))

        # Stats
        stats_frame = ctk.CTkFrame(main_frame, fg_color=ModernColors.CARD_BG, corner_radius=10)
        stats_frame.pack(fill="x")

        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(padx=20, pady=15)

        success_label = ctk.CTkLabel(
            stats_grid,
            text="✅ Erfolg: 0",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.ACCENT_SUCCESS
        )
        success_label.grid(row=0, column=0, padx=20)

        error_label = ctk.CTkLabel(
            stats_grid,
            text="❌ Fehler: 0",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.ACCENT_DANGER
        )
        error_label.grid(row=0, column=1, padx=20)

        skipped_label = ctk.CTkLabel(
            stats_grid,
            text="⏭️ Übersprungen: 0",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_MUTED
        )
        skipped_label.grid(row=0, column=2, padx=20)

        # Cancel button (only shown during processing)
        cancel_button = ctk.CTkButton(
            main_frame,
            text="Abbrechen",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color="transparent",
            border_width=2,
            border_color=ModernColors.BORDER,
            hover_color=ModernColors.CARD_HOVER
        )

        # Processing state
        processing_state = {
            'cancelled': False,
            'completed': False,
            'success': 0,
            'error': 0,
            'skipped': 0
        }

        def cancel_operation():
            processing_state['cancelled'] = True
            cancel_button.configure(state="disabled", text="Abbrechen...")

        cancel_button.configure(command=cancel_operation)
        cancel_button.pack(pady=(20, 0))

        # Sicherer Close-Handler für das Progress-Fenster
        def on_progress_window_close():
            """Sicheres Schließen des Progress-Fensters"""
            processing_state['cancelled'] = True
            try:
                progress_window.destroy()
                self.apply_filters()  # Refresh nach Schließen
            except Exception:
                pass

        progress_window.protocol("WM_DELETE_WINDOW", on_progress_window_close)

        def process_operation():
            try:
                for idx, company in enumerate(companies):
                    if processing_state['cancelled']:
                        break

                    # Update UI - mit sicheren Callbacks
                    progress = (idx + 1) / total
                    progress_window.after(
                        0,
                        lambda p=progress: safe_widget_update(
                            progress_bar,
                            lambda: progress_bar.set(p)
                        )
                    )
                    progress_window.after(
                        0,
                        lambda i=idx+1: safe_widget_update(
                            progress_info,
                            lambda: progress_info.configure(text=f"{i} / {total} bearbeitet")
                        )
                    )
                    progress_window.after(
                        0,
                        lambda c=company: safe_widget_update(
                            status_label,
                            lambda: status_label.configure(
                                text=f"Bearbeite: {c.name or c.website[:30]+'...'}"
                            )
                        )
                    )

                    # Process operation
                    result = operation_func(company)

                    # Update stats
                    if result == 'success':
                        processing_state['success'] += 1
                    elif result == 'error':
                        processing_state['error'] += 1
                    elif result == 'skipped':
                        processing_state['skipped'] += 1

                    # Sichere Stats-Updates
                    progress_window.after(
                        0,
                        lambda: safe_widget_update(
                            success_label,
                            lambda: success_label.configure(text=f"✅ Erfolg: {processing_state['success']}")
                        )
                    )
                    progress_window.after(
                        0,
                        lambda: safe_widget_update(
                            error_label,
                            lambda: error_label.configure(text=f"❌ Fehler: {processing_state['error']}")
                        )
                    )
                    progress_window.after(
                        0,
                        lambda: safe_widget_update(
                            skipped_label,
                            lambda: skipped_label.configure(text=f"⏭️ Übersprungen: {processing_state['skipped']}")
                        )
                    )

                # Done
                processing_state['completed'] = True

                # Sichere Abschluss-Updates
                progress_window.after(
                    0,
                    lambda: safe_widget_update(
                        progress_bar,
                        lambda: progress_bar.set(1.0)
                    )
                )
                progress_window.after(
                    0,
                    lambda: safe_widget_update(
                        status_label,
                        lambda: status_label.configure(
                            text="✅ Fertig!" if not processing_state['cancelled'] else "⚠️ Abgebrochen"
                        )
                    )
                )
                progress_window.after(
                    0,
                    lambda: safe_widget_update(
                        cancel_button,
                        lambda: cancel_button.configure(text="Schließen", state="normal")
                    )
                )

                # Change cancel to close
                def close_window():
                    try:
                        progress_window.destroy()
                        self.apply_filters()
                    except Exception:
                        pass

                progress_window.after(
                    0,
                    lambda: safe_widget_update(
                        cancel_button,
                        lambda: cancel_button.configure(command=close_window)
                    )
                )

            except Exception as e:
                # Sichere Exception-Behandlung
                try:
                    progress_window.after(
                        0,
                        lambda: messagebox.showerror("Fehler", f"Fehler bei Bulk-Operation:\n{str(e)}")
                    )
                    progress_window.after(
                        0,
                        lambda: (progress_window.destroy() if progress_window.winfo_exists() else None)
                    )
                except Exception:
                    pass  # Fenster wurde bereits geschlossen

        # Run in thread
        import threading
        thread = threading.Thread(target=process_operation, daemon=True)
        thread.start()

    def _generate_with_custom_prompt(self, company, custom_prompt_text, system_prompt_text=None):
        """
        Generiert mit Custom Prompt - VOLLSTÄNDIGE Kontrolle für den User!
        KEINE JSON-Erzwingung - gibt zurück was die KI antwortet.
        """
        import requests

        # Ersetze Platzhalter mit echten Daten (beide Formate: {name} und {{name}})
        placeholders = {
            'name': company.name or "N/A",
            'rating': f"{company.rating:.1f}" if company.rating else "N/A",
            'reviews': str(company.review_count or 0),
            'category': company.main_category or "N/A",
            'website': company.website or "N/A",
            'review_keywords': company.review_keywords or "Keine Reviews verfügbar",
            'description': company.description or "Keine Beschreibung verfügbar",
            'first_name': company.first_name or "",
            'last_name': company.last_name or "",
            'email': company.email or "",
            'phone': company.phone or "",
            'city': company.city or "",
            'address': company.address or "",
            'owner_name': company.owner_name or "",
        }

        # Ersetze Platzhalter im Prompt
        prompt_filled = custom_prompt_text
        for key, value in placeholders.items():
            prompt_filled = prompt_filled.replace(f'{{{key}}}', str(value))

        # System-Prompt vorbereiten
        if not system_prompt_text:
            system_prompt_text = "Du bist ein hilfreicher Assistent. Antworte präzise und direkt."
        else:
            # Ersetze auch Platzhalter im System-Prompt
            for key, value in placeholders.items():
                system_prompt_text = system_prompt_text.replace(f'{{{key}}}', str(value))

        # Lade API Config
        with open('api_config.json', 'r', encoding='utf-8') as f:
            api_config = json.load(f)

        # Lade API Keys aus Umgebungsvariablen
        for api_name, api_settings in api_config.get('apis', {}).items():
            env_var = api_settings.get('api_key_env')
            if env_var:
                import os
                env_value = os.environ.get(env_var, '')
                if env_value:
                    api_settings['api_key'] = env_value

        active_api = api_config.get('active_api', 'deepseek')
        api_settings = api_config['apis'].get(active_api, {})

        if not api_settings.get('enabled') or not api_settings.get('api_key'):
            raise Exception("API nicht konfiguriert oder API Key fehlt")

        # API aufrufen - OHNE JSON-Erzwingung!
        headers = {
            'Authorization': f"Bearer {api_settings['api_key']}",
            'Content-Type': 'application/json'
        }

        data = {
            'model': api_settings['default_model'],
            'messages': [
                {
                    'role': 'system',
                    'content': system_prompt_text
                },
                {
                    'role': 'user',
                    'content': prompt_filled  # NUR der User-Prompt, KEIN JSON-Zwang!
                }
            ],
            'temperature': 0.7,
            'max_tokens': 500
        }

        response = requests.post(
            f"{api_settings['base_url']}/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

        result_json = response.json()
        content = result_json['choices'][0]['message']['content'].strip()

        # === KLARTEXT ZURÜCKGEBEN - KEIN JSON-PARSING! ===
        return {
            'compliment': content,  # Das ist der Text den die KI generiert hat
            'confidence_score': 100,
            'overstatement_score': 0,
            'has_team': False
        }

    def process_bulk_compliments(self, company):
        """Process single company for compliment generation"""
        try:
            if company.compliment:
                return 'skipped'

            # Nutze den ausgewählten Prompt aus self.current_bulk_prompt
            prompt_selection = getattr(self, 'current_bulk_prompt', None)

            if not prompt_selection:
                # Fallback: Standard-Generierung
                result = self.compliment_generator.generate_compliment(company)
            else:
                # Generiere mit ausgewähltem Prompt
                result = self.compliment_generator.generate_compliment_with_prompt(
                    company,
                    prompt_selection
                )

            if result and result.get('compliment'):
                company.compliment = result['compliment']
                company.confidence_score = result.get('confidence_score', 0)
                company.overstatement_score = result.get('overstatement_score', 0)
                company.has_team = result.get('has_team', False)
                company.compliment_generated_at = datetime.now()

                self.session.commit()
                return 'success'
            else:
                return 'error'

        except Exception as e:
            print(f"Error generating compliment for {company.website}: {e}")
            return 'error'

    def bulk_scrape_contact_data(self):
        """
        KOMBINIERTE METHODE: Scraped Namen UND E-Mail in einem Durchgang
        Spart Zeit, weil das Impressum nur einmal geladen wird
        """
        # Get selected companies
        selected_companies = [
            c for c in self.current_results
            if c.id in self.selected_items and self.selected_items[c.id].get()
        ]

        if not selected_companies:
            messagebox.showinfo("Keine Auswahl", "Bitte wähle mindestens einen Lead aus.")
            return

        # Filter companies with websites
        companies_with_website = [c for c in selected_companies if c.website]

        if not companies_with_website:
            messagebox.showwarning(
                "Keine Websites",
                "Keiner der ausgewählten Leads hat eine Website.\nKontaktdaten-Scraping nicht möglich."
            )
            return

        count = len(companies_with_website)
        result = messagebox.askyesno(
            "Kontaktdaten scrapen",
            f"Möchtest du für {count} Lead{'s' if count > 1 else ''} Kontaktdaten scrapen?\n\n"
            f"📇 Extrahiert in EINEM Durchgang:\n"
            f"   • Vorname & Nachname (aus Impressum)\n"
            f"   • E-Mail-Adresse (aus Impressum)\n\n"
            f"Dies kann einige Minuten dauern."
        )

        if not result:
            return

        # Create progress window
        self.show_bulk_progress_window(
            title="Kontaktdaten scrapen",
            total=count,
            operation_func=self.process_bulk_contact_data,
            companies=companies_with_website
        )

    def process_bulk_contact_data(self, company):
        """
        Process single company for combined contact data scraping
        Extrahiert Namen UND E-Mail aus dem Impressum in einem Durchgang
        """
        try:
            # Prüfe ob bereits vollständig
            has_name = company.first_name and company.last_name
            has_email = company.email

            if has_name and has_email:
                return 'skipped'

            # Nutze die kombinierte Methode aus dem Impressum-Scraper
            result = self.impressum_scraper.scrape_all_contact_data(company.website)

            found_something = False

            # Namen übernehmen (falls noch nicht vorhanden)
            if result.get('found_name') and not has_name:
                company.first_name = result['first_name']
                company.last_name = result['last_name']
                found_something = True

            # E-Mail übernehmen (falls noch nicht vorhanden)
            if result.get('found_email') and not has_email:
                company.email = result['email']
                found_something = True

            if found_something:
                self.session.commit()
                return 'success'
            else:
                return 'error'

        except Exception as e:
            logging.error(f"Error scraping contact data for {company.website}: {e}")
            return 'error'

    # ========================================
    # KI-SPALTEN-FEATURE (Clay.com Style!)
    # ========================================

    def show_ai_column_dialog(self):
        """
        Zeigt Dialog für KI-Spalten-Bearbeitung (Clay.com Style!)
        Hier kann der User:
        1. Einen Spaltennamen wählen
        2. Einen KI-Prompt eingeben
        3. Die KI führt den Prompt für alle ausgewählten Leads aus
        """
        # Get selected companies
        selected_companies = [
            c for c in self.current_results
            if c.id in self.selected_items and self.selected_items[c.id].get()
        ]

        if not selected_companies:
            messagebox.showinfo("Keine Auswahl", "Bitte wähle mindestens einen Lead aus.")
            return

        count = len(selected_companies)

        # Dialog erstellen
        dialog = ctk.CTkToplevel(self)
        dialog.title("🤖 KI-Spalte erstellen (Clay-Style)")
        dialog.geometry("900x750")
        dialog.grab_set()

        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (dialog.winfo_screenheight() // 2) - (750 // 2)
        dialog.geometry(f"900x750+{x}+{y}")

        # Main Frame
        main_frame = ctk.CTkScrollableFrame(dialog, fg_color=ModernColors.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"🤖 KI-Spalte für {count} Leads erstellen",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Erstelle eine neue Spalte mit KI-generierten Inhalten - wie bei Clay.com!",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.TEXT_SECONDARY
        )
        subtitle_label.pack(pady=(0, 20))

        # Spaltenname
        name_frame = ctk.CTkFrame(main_frame, fg_color=ModernColors.CARD_BG, corner_radius=12)
        name_frame.pack(fill="x", pady=(0, 15))

        name_label = ctk.CTkLabel(
            name_frame,
            text="📝 Spaltenname (wird als neue Spalte gespeichert):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        name_label.pack(anchor="w", padx=15, pady=(15, 5))

        column_name_entry = ctk.CTkEntry(
            name_frame,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color=ModernColors.BG_SECONDARY,
            placeholder_text="z.B. personalized_intro, sales_pitch, pain_points..."
        )
        column_name_entry.pack(fill="x", padx=15, pady=(0, 15))
        column_name_entry.insert(0, "custom_field")

        # Beispiel-Prompts (Quick Select)
        examples_frame = ctk.CTkFrame(main_frame, fg_color=ModernColors.CARD_BG, corner_radius=12)
        examples_frame.pack(fill="x", pady=(0, 15))

        examples_label = ctk.CTkLabel(
            examples_frame,
            text="⚡ Schnellauswahl (Beispiel-Prompts):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.ACCENT_PRIMARY
        )
        examples_label.pack(anchor="w", padx=15, pady=(15, 10))

        example_prompts = {
            "Personalisierte Intro": "Schreibe eine personalisierte Einleitung für eine Cold-Email an {name}. Nutze diese Infos: Bewertung: {rating}/5, Stadt: {city}. Max 2 Sätze.",
            "Pain Points": "Identifiziere 3 mögliche Pain Points für {name} basierend auf: Branche: {category}, Bewertungen: {review_keywords}. Liste sie als Bullet Points.",
            "Sales Pitch": "Erstelle einen kurzen Sales-Pitch (3 Sätze) für {name}. Betone den Mehrwert basierend auf: {description}",
            "Icebreaker": "Schreibe einen kreativen Icebreaker für {first_name} {last_name} bei {name}. Nutze: {review_keywords}",
            "Zusammenfassung": "Fasse das Unternehmen {name} in 2-3 Sätzen zusammen: Beschreibung: {description}, Rating: {rating}, Reviews: {reviews}",
        }

        examples_buttons = ctk.CTkFrame(examples_frame, fg_color="transparent")
        examples_buttons.pack(fill="x", padx=15, pady=(0, 15))

        def set_example_prompt(prompt_text, name):
            user_prompt_textbox.delete("1.0", "end")
            user_prompt_textbox.insert("1.0", prompt_text)
            column_name_entry.delete(0, "end")
            column_name_entry.insert(0, name.lower().replace(" ", "_"))

        for name, prompt in example_prompts.items():
            btn = ctk.CTkButton(
                examples_buttons,
                text=name,
                font=ctk.CTkFont(size=11),
                height=30,
                corner_radius=8,
                fg_color=ModernColors.BG_SECONDARY,
                hover_color=ModernColors.ACCENT_PRIMARY,
                command=lambda p=prompt, n=name: set_example_prompt(p, n)
            )
            btn.pack(side="left", padx=(0, 8))

        # System Prompt
        system_frame = ctk.CTkFrame(main_frame, fg_color=ModernColors.CARD_BG, corner_radius=12)
        system_frame.pack(fill="x", pady=(0, 15))

        system_label = ctk.CTkLabel(
            system_frame,
            text="🤖 System-Prompt (definiert das KI-Verhalten):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.ACCENT_PRIMARY
        )
        system_label.pack(anchor="w", padx=15, pady=(15, 5))

        system_prompt_textbox = ctk.CTkTextbox(
            system_frame,
            height=80,
            font=ctk.CTkFont(size=12),
            fg_color=ModernColors.BG_SECONDARY
        )
        system_prompt_textbox.pack(fill="x", padx=15, pady=(0, 15))
        system_prompt_textbox.insert("1.0", "Du bist ein erfahrener B2B-Sales-Experte. Antworte präzise, professionell und direkt. Gib NUR die Antwort zurück, keine Erklärungen oder Zusätze.")

        # User Prompt
        prompt_frame = ctk.CTkFrame(main_frame, fg_color=ModernColors.CARD_BG, corner_radius=12)
        prompt_frame.pack(fill="x", pady=(0, 15))

        prompt_label = ctk.CTkLabel(
            prompt_frame,
            text="📝 Dein Prompt (wird für JEDEN Lead ausgeführt):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.TEXT_PRIMARY
        )
        prompt_label.pack(anchor="w", padx=15, pady=(15, 5))

        placeholders_label = ctk.CTkLabel(
            prompt_frame,
            text="Verfügbare Platzhalter: {name}, {website}, {email}, {first_name}, {last_name}, {phone}, {description}, {rating}, {reviews}, {review_keywords}, {category}, {city}, {address}, {compliment}",
            font=ctk.CTkFont(size=11),
            text_color=ModernColors.TEXT_MUTED,
            wraplength=800
        )
        placeholders_label.pack(anchor="w", padx=15, pady=(0, 5))

        user_prompt_textbox = ctk.CTkTextbox(
            prompt_frame,
            height=150,
            font=ctk.CTkFont(size=12),
            fg_color=ModernColors.BG_SECONDARY
        )
        user_prompt_textbox.pack(fill="x", padx=15, pady=(0, 15))
        user_prompt_textbox.insert("1.0", """Analysiere das Unternehmen {name} und erstelle eine personalisierte Einleitung für eine Cold-Email.

Verfügbare Daten:
- Website: {website}
- Bewertung: {rating}/5 ({reviews} Reviews)
- Stadt: {city}
- Beschreibung: {description}
- Review-Keywords: {review_keywords}

Schreibe 2-3 Sätze, die zeigen, dass du dich mit dem Unternehmen beschäftigt hast.""")

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        result_var = {"value": None}

        def on_cancel():
            result_var["value"] = None
            dialog.destroy()

        def on_execute():
            column_name = column_name_entry.get().strip()
            if not column_name:
                messagebox.showwarning("Kein Name", "Bitte gib einen Spaltennamen ein!")
                return

            # Validiere Spaltenname (keine Leerzeichen, nur alphanumerisch + underscore)
            import re
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name):
                messagebox.showwarning(
                    "Ungültiger Name",
                    "Der Spaltenname darf nur Buchstaben, Zahlen und Unterstriche enthalten.\n"
                    "Er muss mit einem Buchstaben oder Unterstrich beginnen."
                )
                return

            user_prompt = user_prompt_textbox.get("1.0", "end-1c").strip()
            if not user_prompt:
                messagebox.showwarning("Kein Prompt", "Bitte gib einen Prompt ein!")
                return

            system_prompt = system_prompt_textbox.get("1.0", "end-1c").strip()

            result_var["value"] = {
                "column_name": column_name,
                "user_prompt": user_prompt,
                "system_prompt": system_prompt
            }
            dialog.destroy()

        btn_cancel = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            font=ctk.CTkFont(size=14),
            height=50,
            corner_radius=10,
            fg_color=ModernColors.CARD_BG,
            hover_color=ModernColors.CARD_HOVER,
            command=on_cancel
        )
        btn_cancel.pack(side="left", expand=True, fill="x", padx=(0, 10))

        btn_execute = ctk.CTkButton(
            button_frame,
            text=f"🚀 KI-Spalte für {count} Leads erstellen",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color="#10B981",
            hover_color="#059669",
            command=on_execute
        )
        btn_execute.pack(side="left", expand=True, fill="x")

        dialog.wait_window()

        if result_var["value"]:
            # Starte Verarbeitung
            self.execute_ai_column(
                selected_companies,
                result_var["value"]["column_name"],
                result_var["value"]["user_prompt"],
                result_var["value"]["system_prompt"]
            )

    def execute_ai_column(self, companies, column_name, user_prompt, system_prompt):
        """Führt die KI-Spalten-Verarbeitung aus"""
        count = len(companies)

        # Bestätigung
        result = messagebox.askyesno(
            "KI-Spalte erstellen",
            f"Möchtest du die Spalte '{column_name}' für {count} Leads erstellen?\n\n"
            f"Die KI wird für jeden Lead den Prompt ausführen.\n"
            f"Dies kann einige Minuten dauern."
        )

        if not result:
            return

        # Speichere für Bulk-Verarbeitung
        self.current_ai_column_config = {
            "column_name": column_name,
            "user_prompt": user_prompt,
            "system_prompt": system_prompt
        }

        # Progress Window
        self.show_bulk_progress_window(
            title=f"KI-Spalte '{column_name}' erstellen",
            total=count,
            operation_func=self.process_ai_column_single,
            companies=companies
        )

    def process_ai_column_single(self, company):
        """Verarbeitet eine einzelne Company für KI-Spalte"""
        try:
            config = getattr(self, 'current_ai_column_config', None)
            if not config:
                return 'error'

            column_name = config['column_name']
            user_prompt = config['user_prompt']
            system_prompt = config['system_prompt']

            # Führe KI-Prompt aus
            result = self.ai_column_processor.process_prompt(
                user_prompt,
                company,
                system_prompt
            )

            if result:
                # Speichere in attributes (JSON-Feld)
                if company.attributes is None:
                    company.attributes = {}

                # SQLAlchemy braucht eine Kopie für JSON-Updates
                new_attributes = dict(company.attributes)
                new_attributes[column_name] = result
                company.attributes = new_attributes

                self.session.commit()
                return 'success'
            else:
                return 'error'

        except Exception as e:
            logging.error(f"Error processing AI column for {company.website}: {e}")
            self.session.rollback()
            return 'error'

    def get_custom_column_names(self):
        """Gibt alle verfügbaren Custom-Spalten aus der Datenbank zurück"""
        column_names = set()
        try:
            # Hole alle Companies mit attributes
            companies = self.session.query(CompanyV3).filter(
                CompanyV3.attributes.isnot(None)
            ).all()

            for company in companies:
                if company.attributes:
                    for key in company.attributes.keys():
                        column_names.add(key)

        except Exception as e:
            logging.error(f"Fehler beim Laden der Custom-Spalten: {e}")

        return sorted(list(column_names))


def main():
    """Start the application"""
    import os
    import sys

    # Ermittle App-Verzeichnis (für PyInstaller)
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))

    # Wechsle ins App-Verzeichnis
    os.chdir(app_dir)

    # First Run Setup - erstellt DB falls nicht vorhanden
    db_path = os.path.join(app_dir, "lead_enrichment_v3.db")
    if not os.path.exists(db_path):
        print("🚀 Erster Start - Initialisiere Anwendung...")
        try:
            from first_run_setup import run_first_time_setup
            run_first_time_setup()
        except ImportError:
            # Fallback: Direkt DB erstellen
            from models_v3 import DatabaseV3, seed_standard_tags
            db = DatabaseV3(db_path)
            db.create_all()
            seed_standard_tags(db)
            print("✅ Datenbank erstellt!")

    # Starte GUI
    app = ModernLeadTool()
    app.mainloop()


if __name__ == "__main__":
    main()
