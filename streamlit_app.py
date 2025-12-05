"""
LeadTool v4.0 - Web Edition
Streamlit Web App for Lead Enrichment
"""

import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from io import BytesIO

# Versuche dotenv zu laden
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Database
from models_v3 import DatabaseV3, CompanyV3, seed_standard_tags
from sqlalchemy import or_, and_

# Modules
from compliment_generator import ComplimentGenerator, AIColumnProcessor
from impressum_scraper import ImpressumScraper
from prompt_manager import PromptManager

# =====================
# Page Config
# =====================
st.set_page_config(
    page_title="LeadTool v4.0",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================
# Custom CSS - Modern Design
# =====================
st.markdown("""
<style>
    /* ===== IMPORTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ===== ROOT VARIABLES ===== */
    :root {
        --bg-dark: #0a0a0f;
        --bg-card: #12121a;
        --bg-card-hover: #1a1a25;
        --bg-gradient-start: #0a0a0f;
        --bg-gradient-end: #0f0f1a;
        --accent-primary: #6366f1;
        --accent-secondary: #8b5cf6;
        --accent-tertiary: #a855f7;
        --accent-success: #10b981;
        --accent-warning: #f59e0b;
        --accent-danger: #ef4444;
        --accent-info: #3b82f6;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --border-color: rgba(255, 255, 255, 0.08);
        --border-glow: rgba(99, 102, 241, 0.3);
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 8px 40px rgba(0, 0, 0, 0.5);
        --shadow-glow: 0 0 40px rgba(99, 102, 241, 0.15);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 24px;
        --transition-fast: 0.15s ease;
        --transition-normal: 0.25s ease;
        --transition-slow: 0.4s ease;
    }

    /* ===== GLOBAL STYLES ===== */
    .stApp {
        background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* ===== MAIN HEADER ===== */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.03em;
        text-shadow: 0 0 80px rgba(99, 102, 241, 0.5);
    }

    .sub-header {
        font-size: 1rem;
        color: var(--text-secondary);
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* ===== GLASSMORPHISM CARDS ===== */
    .glass-card {
        background: rgba(18, 18, 26, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all var(--transition-normal);
        box-shadow: var(--shadow-md);
    }

    .glass-card:hover {
        border-color: var(--border-glow);
        box-shadow: var(--shadow-glow);
        transform: translateY(-2px);
    }

    /* ===== STAT CARDS ===== */
    .stat-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: var(--radius-lg);
        padding: 1.25rem;
        text-align: center;
        transition: all var(--transition-normal);
    }

    .stat-card:hover {
        border-color: var(--accent-primary);
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.2);
        transform: translateY(-3px);
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }

    .stat-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 500;
    }

    /* ===== METRICS OVERRIDE ===== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.04) 100%);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        transition: all var(--transition-normal);
    }

    [data-testid="stMetric"]:hover {
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.15);
    }

    [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d14 0%, #12121a 100%);
        border-right: 1px solid var(--border-color);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }

    .sidebar-logo {
        font-size: 1.75rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }

    .sidebar-subtitle {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 1.5rem;
    }

    /* ===== NAVIGATION RADIO BUTTONS ===== */
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.5rem;
    }

    [data-testid="stSidebar"] .stRadio > div > label {
        background: transparent;
        border: 1px solid transparent;
        border-radius: var(--radius-md);
        padding: 0.75rem 1rem;
        margin: 0;
        cursor: pointer;
        transition: all var(--transition-fast);
        font-weight: 500;
        color: var(--text-secondary);
    }

    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(99, 102, 241, 0.1);
        border-color: rgba(99, 102, 241, 0.2);
        color: var(--text-primary);
    }

    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.1) 100%);
        border-color: var(--accent-primary);
        color: var(--text-primary);
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.625rem 1.25rem;
        font-weight: 600;
        font-size: 0.875rem;
        letter-spacing: 0.01em;
        transition: all var(--transition-normal);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(99, 102, 241, 0.4);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background: transparent;
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        box-shadow: none;
    }

    .stButton > button[kind="secondary"]:hover {
        border-color: var(--accent-primary);
        color: var(--text-primary);
        background: rgba(99, 102, 241, 0.1);
    }

    /* ===== DOWNLOAD BUTTON ===== */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }

    .stDownloadButton > button:hover {
        box-shadow: 0 6px 25px rgba(16, 185, 129, 0.4);
    }

    /* ===== INPUT FIELDS ===== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: rgba(18, 18, 26, 0.8) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        transition: all var(--transition-fast) !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }

    .stTextInput > label,
    .stNumberInput > label,
    .stSelectbox > label,
    .stMultiSelect > label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
    }

    /* ===== CHECKBOX ===== */
    .stCheckbox > label {
        color: var(--text-secondary);
        font-weight: 400;
    }

    .stCheckbox > label > span:first-child {
        background: var(--bg-card) !important;
        border-color: var(--border-color) !important;
    }

    /* ===== SLIDER ===== */
    .stSlider > div > div > div > div {
        background: var(--accent-primary) !important;
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background: rgba(18, 18, 26, 0.6) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        transition: all var(--transition-fast) !important;
    }

    .streamlit-expanderHeader:hover {
        border-color: var(--accent-primary) !important;
        background: rgba(99, 102, 241, 0.1) !important;
    }

    .streamlit-expanderContent {
        background: rgba(18, 18, 26, 0.4) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
    }

    /* ===== DATAFRAME / TABLE ===== */
    [data-testid="stDataFrame"] {
        background: rgba(18, 18, 26, 0.6);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        overflow: hidden;
    }

    [data-testid="stDataFrame"] table {
        font-size: 0.85rem;
    }

    [data-testid="stDataFrame"] th {
        background: rgba(99, 102, 241, 0.15) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.05em;
    }

    [data-testid="stDataFrame"] td {
        color: var(--text-secondary) !important;
        border-color: var(--border-color) !important;
    }

    [data-testid="stDataFrame"] tr:hover td {
        background: rgba(99, 102, 241, 0.08) !important;
        color: var(--text-primary) !important;
    }

    /* ===== ALERTS / INFO BOXES ===== */
    .stAlert {
        background: rgba(18, 18, 26, 0.8) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        border-left: 4px solid var(--accent-info) !important;
    }

    [data-testid="stAlert"][data-baseweb="notification"] {
        background: rgba(18, 18, 26, 0.8) !important;
    }

    .element-container div[data-testid="stAlert"] > div {
        color: var(--text-secondary) !important;
    }

    /* Success */
    div[data-baseweb="notification"][kind="positive"] {
        background: rgba(16, 185, 129, 0.1) !important;
        border-color: rgba(16, 185, 129, 0.3) !important;
        border-left-color: var(--accent-success) !important;
    }

    /* Warning */
    div[data-baseweb="notification"][kind="warning"] {
        background: rgba(245, 158, 11, 0.1) !important;
        border-color: rgba(245, 158, 11, 0.3) !important;
        border-left-color: var(--accent-warning) !important;
    }

    /* Error */
    div[data-baseweb="notification"][kind="negative"] {
        background: rgba(239, 68, 68, 0.1) !important;
        border-color: rgba(239, 68, 68, 0.3) !important;
        border-left-color: var(--accent-danger) !important;
    }

    /* ===== FILE UPLOADER ===== */
    [data-testid="stFileUploader"] {
        background: rgba(18, 18, 26, 0.6);
        border: 2px dashed var(--border-color);
        border-radius: var(--radius-lg);
        padding: 2rem;
        transition: all var(--transition-normal);
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent-primary);
        background: rgba(99, 102, 241, 0.05);
    }

    [data-testid="stFileUploader"] section {
        padding: 0 !important;
    }

    [data-testid="stFileUploader"] section > div {
        background: transparent !important;
    }

    /* ===== PROGRESS BAR ===== */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
        border-radius: var(--radius-sm);
    }

    .stProgress > div > div {
        background: var(--bg-card) !important;
        border-radius: var(--radius-sm);
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: all var(--transition-fast);
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.1);
        border-color: rgba(99, 102, 241, 0.3);
        color: var(--text-primary);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.1) 100%) !important;
        border-color: var(--accent-primary) !important;
        color: var(--text-primary) !important;
    }

    /* ===== DIVIDER ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, var(--border-color) 50%, transparent 100%);
        margin: 2rem 0;
    }

    /* ===== CUSTOM COMPONENTS ===== */
    .lead-card {
        background: linear-gradient(135deg, rgba(18, 18, 26, 0.9) 0%, rgba(18, 18, 26, 0.7) 100%);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all var(--transition-normal);
    }

    .lead-card:hover {
        border-color: var(--accent-primary);
        box-shadow: var(--shadow-glow);
        transform: translateY(-2px);
    }

    .lead-name {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }

    .lead-meta {
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .status-complete {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .status-pending {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .status-missing {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* ===== QUICK FILTER BUTTONS ===== */
    .quick-filter-btn {
        background: rgba(18, 18, 26, 0.8);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 0.75rem 1rem;
        color: var(--text-secondary);
        font-weight: 500;
        cursor: pointer;
        transition: all var(--transition-fast);
        text-align: center;
    }

    .quick-filter-btn:hover {
        background: rgba(99, 102, 241, 0.1);
        border-color: var(--accent-primary);
        color: var(--text-primary);
        transform: translateY(-2px);
    }

    /* ===== SECTION HEADERS ===== */
    .section-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, var(--border-color) 0%, transparent 100%);
        margin-left: 1rem;
    }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-dark);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-primary);
    }

    /* ===== ANIMATIONS ===== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    .animate-fade-in {
        animation: fadeIn 0.5s ease forwards;
    }

    .animate-pulse {
        animation: pulse 2s ease-in-out infinite;
    }

    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }

        .stat-value {
            font-size: 1.5rem;
        }

        .glass-card {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)


# =====================
# Initialize Session State
# =====================
def init_session_state():
    """Initialize session state variables"""
    if 'db' not in st.session_state:
        # Initialize database - use /app/db in Docker, otherwise local
        db_dir = "/app/db" if os.path.exists("/app/db") else "."
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "lead_enrichment_v3.db")
        if not os.path.exists(db_path):
            db = DatabaseV3(db_path)
            db.create_all()
            seed_standard_tags(db)
        else:
            db = DatabaseV3(db_path)
        st.session_state.db = db
        st.session_state.session = db.get_session()

    if 'compliment_generator' not in st.session_state:
        st.session_state.compliment_generator = ComplimentGenerator()

    if 'ai_processor' not in st.session_state:
        st.session_state.ai_processor = AIColumnProcessor()

    if 'impressum_scraper' not in st.session_state:
        st.session_state.impressum_scraper = ImpressumScraper()

    if 'prompt_manager' not in st.session_state:
        st.session_state.prompt_manager = PromptManager()

    if 'selected_leads' not in st.session_state:
        st.session_state.selected_leads = []

    if 'category_hierarchy' not in st.session_state:
        try:
            with open('category_hierarchy.json', 'r', encoding='utf-8') as f:
                st.session_state.category_hierarchy = json.load(f)
        except:
            st.session_state.category_hierarchy = {}


# =====================
# Helper Functions
# =====================
def get_leads_dataframe(leads):
    """Convert leads to DataFrame for display"""
    data = []
    for lead in leads:
        data.append({
            'ID': lead.id,
            'Name': lead.name or '-',
            'Vorname': lead.first_name or '-',
            'Nachname': lead.last_name or '-',
            'E-Mail': lead.email or '-',
            'Telefon': lead.phone or '-',
            'Website': lead.website or '-',
            'Stadt': lead.city or '-',
            'Rating': f"{lead.rating:.1f}" if lead.rating else '-',
            'Reviews': lead.review_count or '-',
            'Kompliment': (lead.compliment[:50] + '...') if lead.compliment and len(lead.compliment) > 50 else (lead.compliment or '-'),
            'Status': get_status_emoji(lead)
        })
    return pd.DataFrame(data)


def get_status_emoji(lead):
    """Get status emoji for lead"""
    has_names = lead.first_name and lead.last_name
    has_compliment = lead.compliment

    if has_names and has_compliment:
        return "✅ Komplett"
    elif not has_names:
        return "⚠️ Namen fehlen"
    elif not has_compliment:
        return "⚠️ Kompliment fehlt"
    return "-"


def export_leads_to_csv(leads):
    """Export leads to CSV"""
    data = []
    for company in leads:
        data.append({
            'Name': company.name,
            'Vorname': company.first_name,
            'Nachname': company.last_name,
            'E-Mail': company.email,
            'Telefon': company.phone,
            'Website': company.website,
            'Adresse': company.address,
            'Stadt': company.city,
            'PLZ': company.zip_code,
            'Rating': company.rating,
            'Reviews': company.review_count,
            'Kompliment': company.compliment,
            'Kategorie': company.main_category,
            'Beschreibung': company.description
        })

    df = pd.DataFrame(data)
    return df.to_csv(index=False, encoding='utf-8-sig')


# =====================
# Sidebar Navigation
# =====================
def render_sidebar():
    """Render sidebar with navigation"""
    with st.sidebar:
        # Logo & Branding
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 1.5rem 0;">
            <div style="font-size: 2.5rem; margin-bottom: 0.25rem;">⚡</div>
            <div class="sidebar-logo">LeadTool</div>
            <div class="sidebar-subtitle">Professional Edition</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["🔍 Filter & Suche", "📤 CSV Upload", "💬 Prompts", "🤖 API Config", "⚙️ Einstellungen"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Stats Section
        session = st.session_state.session
        total = session.query(CompanyV3).count()
        with_names = session.query(CompanyV3).filter(
            CompanyV3.first_name.isnot(None),
            CompanyV3.last_name.isnot(None)
        ).count()
        with_compliment = session.query(CompanyV3).filter(
            CompanyV3.compliment.isnot(None)
        ).count()

        # Calculate percentages
        names_pct = (with_names / total * 100) if total > 0 else 0
        compliment_pct = (with_compliment / total * 100) if total > 0 else 0

        st.markdown("""
        <div style="margin-bottom: 0.75rem;">
            <div style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; margin-bottom: 0.75rem;">
                📊 Database Overview
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Custom stat cards
        st.markdown(f"""
        <div class="stat-card" style="margin-bottom: 0.75rem;">
            <div class="stat-value">{total:,}</div>
            <div class="stat-label">Total Leads</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value" style="font-size: 1.5rem;">{with_names:,}</div>
                <div class="stat-label">Mit Namen</div>
                <div style="font-size: 0.7rem; color: #6366f1; margin-top: 0.25rem;">{names_pct:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value" style="font-size: 1.5rem;">{with_compliment:,}</div>
                <div class="stat-label">Komplimente</div>
                <div style="font-size: 0.7rem; color: #10b981; margin-top: 0.25rem;">{compliment_pct:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        # Footer
        st.markdown("""
        <div style="position: absolute; bottom: 1rem; left: 1rem; right: 1rem; text-align: center;">
            <div style="font-size: 0.7rem; color: #475569;">
                Made with 💜 by LeadTool
            </div>
        </div>
        """, unsafe_allow_html=True)

        return page


# =====================
# Filter & Search Page
# =====================
def render_filter_page():
    """Render filter and search page"""
    # Page Header
    st.markdown("""
    <div class="animate-fade-in">
        <h1 class="main-header">Filter & Suche</h1>
        <p class="sub-header">Finde und bearbeite deine Leads mit erweiterten Filteroptionen</p>
    </div>
    """, unsafe_allow_html=True)

    session = st.session_state.session

    # Filter Section in Glass Card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🎯 Filter-Optionen</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        search_text = st.text_input("🔎 Schnellsuche", placeholder="Name oder Website...")
        min_rating = st.slider("⭐ Min. Rating", 0.0, 5.0, 0.0, 0.5)

    with col2:
        min_reviews = st.number_input("📊 Min. Reviews", min_value=0, value=0)
        location = st.text_input("📍 Ort", placeholder="Stadt oder PLZ...")

    with col3:
        has_phone = st.checkbox("📱 Nur mit Telefon")
        has_website = st.checkbox("🌐 Nur mit Website")
        limit = st.number_input("📋 Max. Ergebnisse", min_value=10, max_value=1000, value=100)

    st.markdown('</div>', unsafe_allow_html=True)

    # Quick Filters Section
    st.markdown('<div class="section-header" style="margin-top: 1.5rem;">⚡ Schnellfilter</div>', unsafe_allow_html=True)

    qf_col1, qf_col2, qf_col3, qf_col4 = st.columns(4)

    quick_filter = None
    with qf_col1:
        if st.button("✅ Komplett", use_container_width=True, help="Leads mit Namen und Kompliment"):
            quick_filter = "complete"
    with qf_col2:
        if st.button("👤 Ohne Namen", use_container_width=True, help="Leads ohne Kontaktperson"):
            quick_filter = "no_names"
    with qf_col3:
        if st.button("💬 Ohne Kompliment", use_container_width=True, help="Leads ohne generiertes Kompliment"):
            quick_filter = "no_compliment"
    with qf_col4:
        if st.button("⭐ Top Rated", use_container_width=True, help="Leads mit Rating 4.0+"):
            quick_filter = "top_rated"

    # Build Query
    query = session.query(CompanyV3)

    # Apply Quick Filter
    if quick_filter == "complete":
        query = query.filter(
            and_(
                CompanyV3.first_name.isnot(None),
                CompanyV3.first_name != "",
                CompanyV3.last_name.isnot(None),
                CompanyV3.last_name != "",
                CompanyV3.compliment.isnot(None),
                CompanyV3.compliment != ""
            )
        )
    elif quick_filter == "no_names":
        query = query.filter(
            or_(
                CompanyV3.first_name.is_(None),
                CompanyV3.first_name == "",
                CompanyV3.last_name.is_(None),
                CompanyV3.last_name == ""
            )
        )
    elif quick_filter == "no_compliment":
        query = query.filter(
            or_(
                CompanyV3.compliment.is_(None),
                CompanyV3.compliment == ""
            )
        )
    elif quick_filter == "top_rated":
        query = query.filter(CompanyV3.rating >= 4.0)

    # Apply Standard Filters
    if search_text:
        search_pattern = f"%{search_text}%"
        query = query.filter(
            or_(
                CompanyV3.name.like(search_pattern),
                CompanyV3.website.like(search_pattern)
            )
        )

    if min_rating > 0:
        query = query.filter(CompanyV3.rating >= min_rating)

    if min_reviews > 0:
        query = query.filter(CompanyV3.review_count >= min_reviews)

    if location:
        query = query.filter(CompanyV3.address.ilike(f"%{location}%"))

    if has_phone:
        query = query.filter(
            and_(CompanyV3.phone.isnot(None), CompanyV3.phone != "")
        )

    if has_website:
        query = query.filter(
            and_(CompanyV3.website.isnot(None), CompanyV3.website != "")
        )

    # Execute Query
    query = query.order_by(CompanyV3.rating.desc(), CompanyV3.review_count.desc())
    query = query.limit(limit)
    leads = query.all()

    # Results Header
    st.markdown("---")

    # Results count with badge
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
        <div class="section-header" style="margin: 0;">📋 Ergebnisse</div>
        <span class="status-badge status-complete">{len(leads)} Leads</span>
    </div>
    """, unsafe_allow_html=True)

    # Action Buttons in glass card
    st.markdown('<div class="glass-card" style="padding: 1rem;">', unsafe_allow_html=True)
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)

    with action_col1:
        if st.button("📇 Kontakte scrapen", use_container_width=True, disabled=len(leads) == 0):
            scrape_contacts_bulk(leads)

    with action_col2:
        if st.button("💬 Komplimente generieren", use_container_width=True, disabled=len(leads) == 0):
            generate_compliments_bulk(leads)

    with action_col3:
        if st.button("🔄 Aktualisieren", use_container_width=True):
            st.rerun()

    with action_col4:
        if leads:
            csv_data = export_leads_to_csv(leads)
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name=f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    st.markdown('</div>', unsafe_allow_html=True)

    # Display Results
    if leads:
        df = get_leads_dataframe(leads)

        # Make table interactive with selection
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Website": st.column_config.LinkColumn("Website", width="medium"),
                "Rating": st.column_config.TextColumn("⭐", width="small"),
                "Reviews": st.column_config.NumberColumn("📊", width="small"),
                "Status": st.column_config.TextColumn("Status", width="medium")
            }
        )

        # Lead Details Section
        st.markdown('<div class="section-header" style="margin-top: 2rem;">🔎 Lead-Details</div>', unsafe_allow_html=True)
        selected_id = st.selectbox(
            "Lead auswählen",
            options=[lead.id for lead in leads],
            format_func=lambda x: next((f"{l.name} ({l.website})" for l in leads if l.id == x), str(x)),
            label_visibility="collapsed"
        )

        if selected_id:
            selected_lead = next((l for l in leads if l.id == selected_id), None)
            if selected_lead:
                render_lead_details(selected_lead)
    else:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
            <div style="font-size: 1.125rem; color: #f8fafc; margin-bottom: 0.5rem;">Keine Leads gefunden</div>
            <div style="color: #64748b;">Passe die Filter an oder importiere neue Leads über CSV Upload</div>
        </div>
        """, unsafe_allow_html=True)


def render_lead_details(lead):
    """Render lead details"""
    # Status badges
    has_names = lead.first_name and lead.last_name
    has_compliment = lead.compliment

    status_class = "status-complete" if (has_names and has_compliment) else "status-pending" if has_names or has_compliment else "status-missing"
    status_text = "Komplett" if (has_names and has_compliment) else "In Bearbeitung" if has_names or has_compliment else "Offen"

    st.markdown(f"""
    <div class="lead-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
            <div>
                <div class="lead-name">{lead.name or 'Unbekannt'}</div>
                <div class="lead-meta">{lead.website or 'Keine Website'}</div>
            </div>
            <span class="status-badge {status_class}">{status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("##### 🏢 Unternehmen")
        st.markdown(f"""
        <div style="display: grid; gap: 0.5rem; font-size: 0.9rem;">
            <div><span style="color: #64748b;">Name:</span> <span style="color: #f8fafc;">{lead.name or '-'}</span></div>
            <div><span style="color: #64748b;">Website:</span> <span style="color: #6366f1;">{lead.website or '-'}</span></div>
            <div><span style="color: #64748b;">Telefon:</span> <span style="color: #f8fafc;">{lead.phone or '-'}</span></div>
            <div><span style="color: #64748b;">Kategorie:</span> <span style="color: #f8fafc;">{lead.main_category or '-'}</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### 📍 Adresse")
        st.markdown(f"""
        <div style="font-size: 0.9rem; color: #94a3b8;">
            {lead.address or '-'}<br>
            {lead.zip_code or ''} {lead.city or ''}
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("##### 👤 Kontaktperson")
        st.markdown(f"""
        <div style="display: grid; gap: 0.5rem; font-size: 0.9rem;">
            <div><span style="color: #64748b;">Vorname:</span> <span style="color: #f8fafc;">{lead.first_name or '-'}</span></div>
            <div><span style="color: #64748b;">Nachname:</span> <span style="color: #f8fafc;">{lead.last_name or '-'}</span></div>
            <div><span style="color: #64748b;">E-Mail:</span> <span style="color: #6366f1;">{lead.email or '-'}</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### ⭐ Bewertung")
        rating_display = f"{lead.rating:.1f}" if lead.rating else "-"
        rating_stars = "⭐" * int(lead.rating) if lead.rating else ""
        st.markdown(f"""
        <div style="display: flex; gap: 1rem; align-items: center;">
            <div style="font-size: 2rem; font-weight: 700; color: #fbbf24;">{rating_display}</div>
            <div>
                <div style="color: #fbbf24;">{rating_stars}</div>
                <div style="font-size: 0.8rem; color: #64748b;">{lead.review_count or 0} Reviews</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Compliment Section
    if lead.compliment:
        st.markdown('<div class="glass-card" style="border-left: 3px solid #6366f1;">', unsafe_allow_html=True)
        st.markdown("##### 💬 Generiertes Kompliment")
        st.markdown(f"""
        <div style="font-style: italic; color: #e2e8f0; line-height: 1.6;">
            "{lead.compliment}"
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Review Keywords
    if lead.review_keywords:
        with st.expander("📝 Review-Keywords"):
            st.text_area("Keywords", lead.review_keywords, height=100, disabled=True, label_visibility="collapsed")

    # Actions
    st.markdown("---")
    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:
        if st.button("📇 Kontakte scrapen", key=f"scrape_{lead.id}", use_container_width=True):
            scrape_single_contact(lead)

    with action_col2:
        if st.button("💬 Kompliment generieren", key=f"gen_{lead.id}", use_container_width=True):
            generate_single_compliment(lead)

    with action_col3:
        if st.button("🗑️ Löschen", key=f"del_{lead.id}", use_container_width=True):
            delete_compliment(lead)


def scrape_single_contact(lead):
    """Scrape contact data for single lead"""
    if not lead.website:
        st.error("❌ Keine Website vorhanden!")
        return

    with st.spinner("📇 Scrape Kontaktdaten..."):
        try:
            result = st.session_state.impressum_scraper.scrape_all_contact_data(lead.website)

            if result.get('found_name') or result.get('found_email'):
                if result.get('found_name'):
                    lead.first_name = result.get('first_name')
                    lead.last_name = result.get('last_name')

                if result.get('found_email'):
                    lead.email = result.get('email')

                st.session_state.session.commit()
                st.success(f"✅ Kontaktdaten gefunden: {result.get('first_name', '')} {result.get('last_name', '')} - {result.get('email', '')}")
                st.rerun()
            else:
                st.warning("⚠️ Keine Kontaktdaten im Impressum gefunden.")
        except Exception as e:
            st.error(f"❌ Fehler beim Scraping: {str(e)}")


def generate_single_compliment(lead):
    """Generate compliment for single lead"""
    with st.spinner("💬 Generiere Kompliment..."):
        try:
            result = st.session_state.compliment_generator.generate_compliment(lead)

            if result and result.get('compliment'):
                lead.compliment = result['compliment']
                lead.confidence_score = result.get('confidence_score', 0)
                lead.compliment_generated_at = datetime.now()

                st.session_state.session.commit()
                st.success("✅ Kompliment erfolgreich generiert!")
                st.rerun()
            else:
                st.error("❌ Kompliment konnte nicht generiert werden.")
        except Exception as e:
            st.error(f"❌ Fehler bei der Generierung: {str(e)}")


def delete_compliment(lead):
    """Delete compliment from lead"""
    lead.compliment = None
    lead.confidence_score = None
    lead.compliment_generated_at = None
    st.session_state.session.commit()
    st.success("✅ Kompliment gelöscht!")
    st.rerun()


def scrape_contacts_bulk(leads):
    """Scrape contacts for multiple leads"""
    leads_with_website = [l for l in leads if l.website and (not l.first_name or not l.email)]

    if not leads_with_website:
        st.warning("⚠️ Keine Leads zum Scrapen (alle haben bereits Kontaktdaten oder keine Website)")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    names_found = 0
    emails_found = 0

    for idx, lead in enumerate(leads_with_website):
        status_text.text(f"📇 Scrape {lead.name}... ({idx+1}/{len(leads_with_website)})")

        try:
            result = st.session_state.impressum_scraper.scrape_all_contact_data(lead.website)

            if result.get('found_name'):
                lead.first_name = result.get('first_name')
                lead.last_name = result.get('last_name')
                names_found += 1

            if result.get('found_email'):
                lead.email = result.get('email')
                emails_found += 1

            if idx % 10 == 0:
                st.session_state.session.commit()

        except Exception as e:
            pass  # Continue with next

        progress_bar.progress((idx + 1) / len(leads_with_website))

    st.session_state.session.commit()
    progress_bar.empty()
    status_text.empty()

    st.success(f"✅ Scraping abgeschlossen! 👤 {names_found} Namen | 📧 {emails_found} E-Mails gefunden")
    st.rerun()


def generate_compliments_bulk(leads):
    """Generate compliments for multiple leads"""
    leads_without_compliment = [l for l in leads if not l.compliment and l.website]

    if not leads_without_compliment:
        st.warning("⚠️ Keine Leads ohne Kompliment gefunden")
        return

    # Custom prompt option
    with st.expander("✏️ Custom Prompt (optional)", expanded=False):
        custom_prompt = st.text_area(
            "Prompt",
            placeholder="Leer lassen für Standard-Prompt...",
            help="Platzhalter: {name}, {rating}, {reviews}, {review_keywords}, {category}, {city}"
        )

    progress_bar = st.progress(0)
    status_text = st.empty()

    generated = 0

    for idx, lead in enumerate(leads_without_compliment):
        status_text.text(f"💬 Generiere für {lead.name}... ({idx+1}/{len(leads_without_compliment)})")

        try:
            if custom_prompt:
                # Custom prompt generation
                result = st.session_state.ai_processor.process_with_custom_prompt(lead, custom_prompt)
            else:
                result = st.session_state.compliment_generator.generate_compliment(lead)

            if result and result.get('compliment'):
                lead.compliment = result['compliment']
                lead.compliment_generated_at = datetime.now()
                generated += 1

            if idx % 5 == 0:
                st.session_state.session.commit()

        except Exception as e:
            pass  # Continue with next

        progress_bar.progress((idx + 1) / len(leads_without_compliment))

    st.session_state.session.commit()
    progress_bar.empty()
    status_text.empty()

    st.success(f"✅ {generated} Komplimente erfolgreich generiert!")
    st.rerun()


# =====================
# CSV Upload Page
# =====================
def render_upload_page():
    """Render CSV upload page"""
    st.markdown("""
    <div class="animate-fade-in">
        <h1 class="main-header">CSV Upload</h1>
        <p class="sub-header">Importiere neue Leads aus CSV-Dateien in deine Datenbank</p>
    </div>
    """, unsafe_allow_html=True)

    # Info Card
    st.markdown("""
    <div class="glass-card" style="border-left: 3px solid #3b82f6;">
        <div style="display: flex; gap: 1rem; align-items: flex-start;">
            <div style="font-size: 1.5rem;">💡</div>
            <div>
                <div style="font-weight: 600; color: #f8fafc; margin-bottom: 0.25rem;">Tipp</div>
                <div style="color: #94a3b8; font-size: 0.9rem;">
                    Du kannst CSV-Dateien von Google Maps Scraper oder anderen Quellen hochladen.
                    Die CSV sollte mindestens eine <code style="background: rgba(99, 102, 241, 0.2); padding: 0.125rem 0.375rem; border-radius: 4px; color: #a5b4fc;">website</code> Spalte enthalten.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Upload area
    st.markdown('<div class="section-header" style="margin-top: 1.5rem;">📁 Datei auswählen</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "CSV-Datei auswählen",
        type=['csv'],
        help="Unterstützte Spalten: name, website, phone, address, city, rating, reviews, review_keywords, etc.",
        label_visibility="collapsed"
    )

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

            st.markdown(f"""
            <div class="glass-card" style="border-left: 3px solid #10b981;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="font-size: 1.25rem;">✅</span>
                    <span style="color: #10b981; font-weight: 600;">{len(df)} Zeilen gefunden</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Check for website column
            if 'website' not in df.columns:
                st.error("Die CSV-Datei muss eine 'website' Spalte enthalten!")
                return

            # Preview
            st.markdown('<div class="section-header">📋 Vorschau</div>', unsafe_allow_html=True)
            st.dataframe(df.head(10), use_container_width=True, height=300)

            # Column tags
            st.markdown(f"""
            <div style="margin: 1rem 0;">
                <span style="color: #64748b; font-size: 0.8rem;">Spalten:</span>
                {''.join([f'<span style="background: rgba(99, 102, 241, 0.2); color: #a5b4fc; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin: 0.25rem;">{col}</span>' for col in df.columns])}
            </div>
            """, unsafe_allow_html=True)

            # Import options in glass card
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("##### ⚙️ Import-Optionen")

            col1, col2 = st.columns(2)

            with col1:
                auto_scrape = st.checkbox("📇 Nach Import automatisch Kontakte scrapen", value=False)

            with col2:
                skip_existing = st.checkbox("⏭️ Existierende überspringen", value=True)

            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("🚀 Importieren", type="primary", use_container_width=True):
                import_csv(df, auto_scrape, skip_existing)

        except Exception as e:
            st.error(f"Fehler beim Lesen der CSV: {str(e)}")

    # Database Stats Section
    st.markdown("---")
    st.markdown('<div class="section-header">📊 Datenbank-Status</div>', unsafe_allow_html=True)

    session = st.session_state.session
    total = session.query(CompanyV3).count()
    with_names = session.query(CompanyV3).filter(
        CompanyV3.first_name.isnot(None),
        CompanyV3.last_name.isnot(None)
    ).count()
    with_compliment = session.query(CompanyV3).filter(
        CompanyV3.compliment.isnot(None)
    ).count()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Leads", f"{total:,}")
    col2.metric("Mit Namen", f"{with_names:,}")
    col3.metric("Mit Kompliment", f"{with_compliment:,}")


def import_csv(df, auto_scrape=False, skip_existing=True):
    """Import CSV data to database"""
    session = st.session_state.session

    progress_bar = st.progress(0)
    status_text = st.empty()

    imported = 0
    skipped = 0
    imported_companies = []

    for idx, row in df.iterrows():
        website = str(row.get('website', '')).strip()
        if not website or website == 'nan':
            skipped += 1
            continue

        # Check if exists
        if skip_existing:
            existing = session.query(CompanyV3).filter_by(website=website).first()
            if existing:
                skipped += 1
                continue

        # Parse categories
        categories = []
        categories_str = row.get('categories')
        if pd.notna(categories_str) and categories_str:
            categories = [c.strip() for c in str(categories_str).split(',')]

        # Create company
        company = CompanyV3(
            website=website,
            name=row.get('name') if pd.notna(row.get('name')) else None,
            description=row.get('description') if pd.notna(row.get('description')) else None,
            phone=row.get('phone') if pd.notna(row.get('phone')) else None,
            main_category=row.get('main_category') if pd.notna(row.get('main_category')) else None,
            industries=categories,
            address=row.get('address') if pd.notna(row.get('address')) else None,
            city=row.get('city') if pd.notna(row.get('city')) else None,
            zip_code=row.get('zip_code') if pd.notna(row.get('zip_code')) else None,
            state=row.get('state') if pd.notna(row.get('state')) else None,
            country=row.get('country') if pd.notna(row.get('country')) else "Deutschland",
            rating=float(row.get('rating')) if pd.notna(row.get('rating')) and row.get('rating') != '' else None,
            review_count=int(row.get('reviews')) if pd.notna(row.get('reviews')) and str(row.get('reviews')).strip() != '' else None,
            place_id=row.get('place_id') if pd.notna(row.get('place_id')) else None,
            review_keywords=row.get('review_keywords') if pd.notna(row.get('review_keywords')) else None,
            link=row.get('link') if pd.notna(row.get('link')) else None,
            query=row.get('query') if pd.notna(row.get('query')) else None,
            languages=[],
            services=[],
            custom_tags=[],
            attributes={}
        )

        session.add(company)
        imported_companies.append(company)
        imported += 1

        if imported % 50 == 0:
            session.commit()

        progress_bar.progress((idx + 1) / len(df))
        status_text.text(f"Importiere... {idx + 1}/{len(df)}")

    session.commit()
    progress_bar.empty()
    status_text.empty()

    st.success(f"✅ {imported} Leads importiert | ⏭️ {skipped} übersprungen")

    # Auto scrape if enabled
    if auto_scrape and imported_companies:
        st.info("📇 Starte automatisches Scraping...")
        scrape_contacts_bulk(imported_companies)


# =====================
# Prompts Page
# =====================
def render_prompts_page():
    """Render prompts management page"""
    st.markdown("""
    <div class="animate-fade-in">
        <h1 class="main-header">Prompt Templates</h1>
        <p class="sub-header">Verwalte und passe deine Prompt-Templates für die KI-Generierung an</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card" style="border-left: 3px solid #8b5cf6;">
        <div style="display: flex; gap: 1rem; align-items: flex-start;">
            <div style="font-size: 1.5rem;">🎨</div>
            <div>
                <div style="font-weight: 600; color: #f8fafc; margin-bottom: 0.25rem;">Prompt-Vorlagen</div>
                <div style="color: #94a3b8; font-size: 0.9rem;">
                    Hier kannst du Prompt-Templates für die Kompliment-Generierung verwalten.
                    Jeder Prompt kann individuell für verschiedene Anwendungsfälle angepasst werden.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load prompts
    prompts_data = st.session_state.prompt_manager.prompts.get('prompts', [])

    st.markdown('<div class="section-header" style="margin-top: 1.5rem;">📝 Gespeicherte Prompts</div>', unsafe_allow_html=True)

    for prompt in prompts_data:
        with st.expander(f"📝 {prompt.get('name', 'Unnamed')}", expanded=False):
            st.markdown(f"""
            <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
                <span style="background: rgba(99, 102, 241, 0.2); color: #a5b4fc; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">ID: {prompt.get('id', 'N/A')}</span>
            </div>
            <div style="color: #94a3b8; margin-bottom: 1rem;">{prompt.get('description', '-')}</div>
            """, unsafe_allow_html=True)

            st.markdown("**System Prompt:**")
            st.text_area(
                "System",
                prompt.get('system_prompt', ''),
                height=100,
                key=f"sys_{prompt.get('id')}",
                disabled=True,
                label_visibility="collapsed"
            )

            st.markdown("**User Prompt Template:**")
            st.text_area(
                "User",
                prompt.get('user_prompt_template', ''),
                height=150,
                key=f"user_{prompt.get('id')}",
                disabled=True,
                label_visibility="collapsed"
            )

    # Placeholder info
    st.markdown("---")
    st.markdown('<div class="section-header">✏️ Custom Prompt erstellen</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card">
        <div style="font-weight: 600; color: #f8fafc; margin-bottom: 1rem;">📌 Verfügbare Platzhalter</div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem;">
            <div style="background: rgba(99, 102, 241, 0.1); padding: 0.5rem; border-radius: 8px; text-align: center;">
                <code style="color: #a5b4fc;">{name}</code>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">Firmenname</div>
            </div>
            <div style="background: rgba(99, 102, 241, 0.1); padding: 0.5rem; border-radius: 8px; text-align: center;">
                <code style="color: #a5b4fc;">{rating}</code>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">Google Rating</div>
            </div>
            <div style="background: rgba(99, 102, 241, 0.1); padding: 0.5rem; border-radius: 8px; text-align: center;">
                <code style="color: #a5b4fc;">{reviews}</code>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">Anzahl Reviews</div>
            </div>
            <div style="background: rgba(99, 102, 241, 0.1); padding: 0.5rem; border-radius: 8px; text-align: center;">
                <code style="color: #a5b4fc;">{review_keywords}</code>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">Keywords</div>
            </div>
            <div style="background: rgba(99, 102, 241, 0.1); padding: 0.5rem; border-radius: 8px; text-align: center;">
                <code style="color: #a5b4fc;">{category}</code>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">Hauptkategorie</div>
            </div>
            <div style="background: rgba(99, 102, 241, 0.1); padding: 0.5rem; border-radius: 8px; text-align: center;">
                <code style="color: #a5b4fc;">{city}</code>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">Stadt</div>
            </div>
            <div style="background: rgba(99, 102, 241, 0.1); padding: 0.5rem; border-radius: 8px; text-align: center;">
                <code style="color: #a5b4fc;">{first_name}</code>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">Vorname</div>
            </div>
            <div style="background: rgba(99, 102, 241, 0.1); padding: 0.5rem; border-radius: 8px; text-align: center;">
                <code style="color: #a5b4fc;">{last_name}</code>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">Nachname</div>
            </div>
            <div style="background: rgba(99, 102, 241, 0.1); padding: 0.5rem; border-radius: 8px; text-align: center;">
                <code style="color: #a5b4fc;">{description}</code>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">Beschreibung</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =====================
# API Config Page
# =====================
def render_api_page():
    """Render API configuration page"""
    st.markdown("""
    <div class="animate-fade-in">
        <h1 class="main-header">API Konfiguration</h1>
        <p class="sub-header">Verwalte deine API-Keys für KI-gestützte Funktionen</p>
    </div>
    """, unsafe_allow_html=True)

    # Load config
    try:
        with open('api_config.json', 'r', encoding='utf-8') as f:
            api_config = json.load(f)
    except:
        api_config = {"apis": {}, "active_api": "deepseek"}

    current_api = api_config.get('active_api', 'deepseek')

    # Current API Status Card
    st.markdown(f"""
    <div class="glass-card" style="border-left: 3px solid #10b981;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; margin-bottom: 0.25rem;">Aktiver Provider</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc;">{current_api.upper()}</div>
            </div>
            <div style="font-size: 2.5rem;">🤖</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # API Selection
    st.markdown('<div class="section-header" style="margin-top: 1.5rem;">🔌 Provider auswählen</div>', unsafe_allow_html=True)

    api_providers = ['deepseek', 'openai', 'anthropic', 'groq']
    api_icons = {'deepseek': '🔮', 'openai': '🧠', 'anthropic': '🎭', 'groq': '⚡'}

    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]

    for i, provider in enumerate(api_providers):
        with cols[i]:
            is_active = provider == current_api
            border_color = "#10b981" if is_active else "rgba(255,255,255,0.08)"
            bg_color = "rgba(16, 185, 129, 0.1)" if is_active else "rgba(18, 18, 26, 0.6)"

            st.markdown(f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 1rem; text-align: center; cursor: pointer;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{api_icons[provider]}</div>
                <div style="font-weight: 600; color: #f8fafc;">{provider.upper()}</div>
                {'<div style="font-size: 0.7rem; color: #10b981; margin-top: 0.25rem;">✓ Aktiv</div>' if is_active else ''}
            </div>
            """, unsafe_allow_html=True)

    selected_api = st.selectbox(
        "API Provider",
        api_providers,
        index=api_providers.index(current_api) if current_api in api_providers else 0,
        label_visibility="collapsed"
    )

    # Environment variable info
    st.markdown("---")
    st.markdown('<div class="section-header">🔑 API Key Status</div>', unsafe_allow_html=True)

    env_vars = {
        'deepseek': 'DEEPSEEK_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'groq': 'GROQ_API_KEY'
    }

    env_var = env_vars.get(selected_api, 'API_KEY')
    current_key = os.environ.get(env_var, '')

    if current_key:
        st.markdown(f"""
        <div class="glass-card" style="border-left: 3px solid #10b981;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="font-size: 1.5rem;">✅</div>
                <div>
                    <div style="font-weight: 600; color: #10b981;">API Key konfiguriert</div>
                    <div style="font-size: 0.85rem; color: #64748b;"><code>{env_var}</code></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="glass-card" style="border-left: 3px solid #f59e0b;">
            <div style="display: flex; align-items: flex-start; gap: 1rem;">
                <div style="font-size: 1.5rem;">⚠️</div>
                <div>
                    <div style="font-weight: 600; color: #f59e0b; margin-bottom: 0.5rem;">API Key nicht gefunden</div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.75rem;">
                        Füge folgende Zeile zu deiner <code style="background: rgba(99, 102, 241, 0.2); padding: 0.125rem 0.375rem; border-radius: 4px;">.env</code> Datei hinzu:
                    </div>
                    <div style="background: rgba(0,0,0,0.3); padding: 0.75rem; border-radius: 8px; font-family: monospace; color: #a5b4fc;">
                        {env_var}=dein-api-key-hier
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Save button
    if st.button("💾 Als aktiv setzen", type="primary", use_container_width=True):
        api_config['active_api'] = selected_api
        with open('api_config.json', 'w', encoding='utf-8') as f:
            json.dump(api_config, f, indent=2)
        st.success(f"{selected_api.upper()} als aktiv gesetzt!")
        st.rerun()


# =====================
# Settings Page
# =====================
def render_settings_page():
    """Render settings page"""
    st.markdown("""
    <div class="animate-fade-in">
        <h1 class="main-header">Einstellungen</h1>
        <p class="sub-header">Verwalte deine Datenbank und Systemeinstellungen</p>
    </div>
    """, unsafe_allow_html=True)

    session = st.session_state.session

    # Database Stats Section
    st.markdown('<div class="section-header">🗄️ Datenbank-Übersicht</div>', unsafe_allow_html=True)

    total = session.query(CompanyV3).count()
    with_names = session.query(CompanyV3).filter(
        CompanyV3.first_name.isnot(None)
    ).count()
    with_compliment = session.query(CompanyV3).filter(
        CompanyV3.compliment.isnot(None)
    ).count()
    with_website = session.query(CompanyV3).filter(
        CompanyV3.website.isnot(None)
    ).count()

    # Stat cards in a row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{total:,}</div>
            <div class="stat-label">Total Leads</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{with_names:,}</div>
            <div class="stat-label">Mit Namen</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{with_compliment:,}</div>
            <div class="stat-label">Mit Kompliment</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{with_website:,}</div>
            <div class="stat-label">Mit Website</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Export Section
    st.markdown('<div class="section-header">📥 Daten-Export</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <div style="font-size: 2rem;">💾</div>
            <div>
                <div style="font-weight: 600; color: #f8fafc;">Komplett-Export</div>
                <div style="font-size: 0.85rem; color: #64748b;">Exportiere alle Leads als CSV-Datei</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📥 Alle Leads als CSV exportieren", use_container_width=True):
        all_leads = session.query(CompanyV3).all()
        if all_leads:
            csv_data = export_leads_to_csv(all_leads)
            st.download_button(
                label="💾 Download starten",
                data=csv_data,
                file_name=f"all_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("Keine Leads zum Exportieren vorhanden.")

    st.markdown("---")

    # Danger Zone
    st.markdown('<div class="section-header" style="color: #ef4444;">⚠️ Gefahrenzone</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card" style="border: 1px solid rgba(239, 68, 68, 0.3); background: rgba(239, 68, 68, 0.05);">
        <div style="font-size: 0.85rem; color: #f87171; margin-bottom: 1rem;">
            ⚠️ Diese Aktionen können nicht rückgängig gemacht werden. Bitte mit Vorsicht verwenden.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem;">
            <div style="font-weight: 600; color: #f8fafc; margin-bottom: 0.25rem;">🗑️ Komplimente löschen</div>
            <div style="font-size: 0.8rem; color: #64748b;">Entfernt alle generierten Komplimente</div>
        </div>
        """, unsafe_allow_html=True)

        confirm_compliments = st.checkbox("Ja, ich bin sicher", key="confirm_delete_compliments")
        if st.button("🗑️ Alle Komplimente löschen", use_container_width=True, disabled=not confirm_compliments):
            session.query(CompanyV3).update({
                CompanyV3.compliment: None,
                CompanyV3.confidence_score: None,
                CompanyV3.compliment_generated_at: None
            })
            session.commit()
            st.success("Alle Komplimente gelöscht!")
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem;">
            <div style="font-weight: 600; color: #f8fafc; margin-bottom: 0.25rem;">💀 Alle Leads löschen</div>
            <div style="font-size: 0.8rem; color: #64748b;">Löscht die gesamte Datenbank</div>
        </div>
        """, unsafe_allow_html=True)

        confirm_all = st.checkbox("Ja, ich bin sicher (ALLE DATEN)", key="confirm_delete_all")
        if st.button("💀 Alle Leads löschen", use_container_width=True, disabled=not confirm_all):
            session.query(CompanyV3).delete()
            session.commit()
            st.success("Alle Leads gelöscht!")
            st.rerun()


# =====================
# Main App
# =====================
def main():
    """Main app entry point"""
    init_session_state()

    # Render sidebar and get selected page
    page = render_sidebar()

    # Render selected page
    if page == "🔍 Filter & Suche":
        render_filter_page()
    elif page == "📤 CSV Upload":
        render_upload_page()
    elif page == "💬 Prompts":
        render_prompts_page()
    elif page == "🤖 API Config":
        render_api_page()
    elif page == "⚙️ Einstellungen":
        render_settings_page()


if __name__ == "__main__":
    main()
