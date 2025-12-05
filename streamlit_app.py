"""
LeadTool v4.0 - Web Edition (Complete)
Streamlit Web App for Lead Enrichment
All Desktop Features Included
"""

import streamlit as st
import pandas as pd
import json
import os
import time
import re
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
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================
# Modern CSS
# =====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #111118;
        --bg-card: #16161d;
        --accent: #6366f1;
        --accent-hover: #818cf8;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --border: rgba(255,255,255,0.06);
    }

    .stApp {
        background: var(--bg-primary);
        font-family: 'Inter', sans-serif;
    }

    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border);
    }

    /* Headers */
    .page-title {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }

    .page-subtitle {
        font-size: 0.9rem;
        color: var(--text-muted);
        margin-bottom: 1.5rem;
    }

    /* Cards */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    .card-header {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    /* Stats */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .stat-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }

    .stat-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .stat-label {
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border: none;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }

    /* Action Bar */
    .action-bar {
        display: flex;
        gap: 0.5rem;
        padding: 1rem;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }

    /* Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .badge-success { background: rgba(16,185,129,0.15); color: #34d399; }
    .badge-warning { background: rgba(245,158,11,0.15); color: #fbbf24; }
    .badge-danger { background: rgba(239,68,68,0.15); color: #f87171; }
    .badge-info { background: rgba(99,102,241,0.15); color: #a5b4fc; }

    /* Tables */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border-radius: 8px !important;
    }

    /* Progress */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
    }

    /* Sidebar Logo */
    .logo-container {
        text-align: center;
        padding: 1.5rem 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1rem;
    }

    .logo-icon { font-size: 2.5rem; }

    .logo-text {
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .logo-subtitle {
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.15em;
    }

    /* Filter Section */
    .filter-section {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }

    .filter-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }

    /* Quick Filters */
    .quick-filter {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px;
        color: var(--text-secondary);
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s;
    }

    .quick-filter:hover {
        border-color: var(--accent);
        color: var(--text-primary);
    }

    /* Lead Card */
    .lead-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.2s;
    }

    .lead-card:hover {
        border-color: var(--accent);
    }

    .lead-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .lead-website {
        font-size: 0.85rem;
        color: var(--accent);
    }

    /* Section Headers */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 1.5rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent); }
</style>
""", unsafe_allow_html=True)


# =====================
# Session State Init
# =====================
def init_session_state():
    """Initialize all session state variables"""
    if 'db' not in st.session_state:
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
        st.session_state.selected_leads = set()

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    if 'items_per_page' not in st.session_state:
        st.session_state.items_per_page = 50

    if 'category_hierarchy' not in st.session_state:
        try:
            with open('category_hierarchy.json', 'r', encoding='utf-8') as f:
                st.session_state.category_hierarchy = json.load(f)
        except:
            st.session_state.category_hierarchy = {}


# =====================
# Sidebar
# =====================
def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        # Logo
        st.markdown("""
        <div class="logo-container">
            <div class="logo-icon">⚡</div>
            <div class="logo-text">LeadTool</div>
            <div class="logo-subtitle">Professional Edition</div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        page = st.radio(
            "Navigation",
            ["🔍 Leads", "📤 Import", "🤖 KI-Spalten", "💬 Prompts", "⚙️ Settings"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Quick Stats
        session = st.session_state.session
        total = session.query(CompanyV3).count()
        with_names = session.query(CompanyV3).filter(
            and_(CompanyV3.first_name.isnot(None), CompanyV3.first_name != "")
        ).count()
        with_compliment = session.query(CompanyV3).filter(
            and_(CompanyV3.compliment.isnot(None), CompanyV3.compliment != "")
        ).count()
        with_email = session.query(CompanyV3).filter(
            and_(CompanyV3.email.isnot(None), CompanyV3.email != "")
        ).count()

        st.markdown("##### 📊 Database")

        col1, col2 = st.columns(2)
        col1.metric("Total", f"{total:,}")
        col2.metric("Namen", f"{with_names:,}")

        col3, col4 = st.columns(2)
        col3.metric("E-Mails", f"{with_email:,}")
        col4.metric("Komplimente", f"{with_compliment:,}")

        return page


# =====================
# Main Leads Page
# =====================
def render_leads_page():
    """Main leads management page"""

    # Header
    st.markdown('<div class="page-title">Lead Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Filtere, bearbeite und exportiere deine Leads</div>', unsafe_allow_html=True)

    session = st.session_state.session

    # Filter Bar
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        search = st.text_input("🔍 Suche", placeholder="Name oder Website...", label_visibility="collapsed")

    with col2:
        min_rating = st.selectbox("⭐ Min Rating", [0, 3.0, 3.5, 4.0, 4.5], format_func=lambda x: f"{x}+" if x > 0 else "Alle")

    with col3:
        workflow_filter = st.selectbox("📋 Status", ["Alle", "Komplett", "Ohne Namen", "Ohne Kompliment", "Ohne E-Mail"])

    with col4:
        limit = st.selectbox("📊 Limit", [50, 100, 250, 500, 1000])

    # Build Query
    query = session.query(CompanyV3)

    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(
            CompanyV3.name.ilike(pattern),
            CompanyV3.website.ilike(pattern)
        ))

    if min_rating > 0:
        query = query.filter(CompanyV3.rating >= min_rating)

    if workflow_filter == "Komplett":
        query = query.filter(
            and_(
                CompanyV3.first_name.isnot(None), CompanyV3.first_name != "",
                CompanyV3.compliment.isnot(None), CompanyV3.compliment != ""
            )
        )
    elif workflow_filter == "Ohne Namen":
        query = query.filter(or_(CompanyV3.first_name.is_(None), CompanyV3.first_name == ""))
    elif workflow_filter == "Ohne Kompliment":
        query = query.filter(or_(CompanyV3.compliment.is_(None), CompanyV3.compliment == ""))
    elif workflow_filter == "Ohne E-Mail":
        query = query.filter(or_(CompanyV3.email.is_(None), CompanyV3.email == ""))

    total_count = query.count()
    leads = query.order_by(CompanyV3.rating.desc().nullslast()).limit(limit).all()

    # Stats Row
    st.markdown(f"""
    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-value">{total_count:,}</div>
            <div class="stat-label">Gefiltert</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len([l for l in leads if l.first_name]):,}</div>
            <div class="stat-label">Mit Namen</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len([l for l in leads if l.email]):,}</div>
            <div class="stat-label">Mit E-Mail</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len([l for l in leads if l.compliment]):,}</div>
            <div class="stat-label">Mit Kompliment</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action Buttons
    st.markdown('<div class="section-title">⚡ Aktionen</div>', unsafe_allow_html=True)

    action_cols = st.columns(7)

    with action_cols[0]:
        if st.button("📇 Kontakte scrapen", use_container_width=True):
            scrape_contacts_bulk(leads)

    with action_cols[1]:
        if st.button("💬 Komplimente", use_container_width=True):
            generate_compliments_bulk(leads)

    with action_cols[2]:
        if st.button("🗑️ Komplimente löschen", use_container_width=True):
            delete_compliments_bulk(leads)

    with action_cols[3]:
        if st.button("📄 CSV Export", use_container_width=True):
            export_csv(leads)

    with action_cols[4]:
        if st.button("📊 Excel Export", use_container_width=True):
            export_excel(leads)

    with action_cols[5]:
        if st.button("🗑️ Leads löschen", use_container_width=True):
            if st.session_state.get('confirm_delete'):
                delete_leads_bulk(leads)
            else:
                st.session_state.confirm_delete = True
                st.warning("Klicke erneut zum Bestätigen!")

    with action_cols[6]:
        if st.button("🔄 Aktualisieren", use_container_width=True):
            st.rerun()

    # Results Table
    st.markdown('<div class="section-title">📋 Ergebnisse</div>', unsafe_allow_html=True)

    if leads:
        # Create DataFrame for display
        df_data = []
        for lead in leads:
            status = "✅" if (lead.first_name and lead.compliment) else "⚠️" if lead.first_name or lead.compliment else "❌"
            df_data.append({
                "ID": lead.id,
                "Status": status,
                "Name": lead.name or "-",
                "Kontakt": f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "-",
                "E-Mail": lead.email or "-",
                "Website": lead.website or "-",
                "Rating": f"⭐ {lead.rating:.1f}" if lead.rating else "-",
                "Stadt": lead.city or "-"
            })

        df = pd.DataFrame(df_data)

        st.dataframe(
            df,
            use_container_width=True,
            height=400,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Status": st.column_config.TextColumn("", width="small"),
                "Website": st.column_config.LinkColumn("Website")
            }
        )

        # Lead Detail Section
        st.markdown('<div class="section-title">🔎 Lead Details</div>', unsafe_allow_html=True)

        selected_id = st.selectbox(
            "Lead auswählen",
            options=[l.id for l in leads],
            format_func=lambda x: next((f"{l.name} - {l.website}" for l in leads if l.id == x), str(x)),
            label_visibility="collapsed"
        )

        if selected_id:
            lead = next((l for l in leads if l.id == selected_id), None)
            if lead:
                render_lead_detail(lead)
    else:
        st.info("🔍 Keine Leads gefunden. Passe die Filter an oder importiere neue Leads.")


def render_lead_detail(lead):
    """Render detailed lead view"""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 🏢 Unternehmen")
        st.write(f"**Name:** {lead.name or '-'}")
        st.write(f"**Website:** {lead.website or '-'}")
        st.write(f"**Telefon:** {lead.phone or '-'}")
        st.write(f"**Kategorie:** {lead.main_category or '-'}")
        st.write(f"**Adresse:** {lead.address or '-'}")
        st.write(f"**Stadt:** {lead.city or '-'}")

    with col2:
        st.markdown("##### 👤 Kontakt")
        st.write(f"**Vorname:** {lead.first_name or '-'}")
        st.write(f"**Nachname:** {lead.last_name or '-'}")
        st.write(f"**E-Mail:** {lead.email or '-'}")
        st.markdown("##### ⭐ Bewertung")
        st.write(f"**Rating:** {lead.rating:.1f if lead.rating else '-'}")
        st.write(f"**Reviews:** {lead.review_count or '-'}")

    if lead.compliment:
        st.markdown("##### 💬 Kompliment")
        st.info(lead.compliment)

    if lead.review_keywords:
        with st.expander("📝 Review Keywords"):
            st.text(lead.review_keywords)

    # Custom Attributes
    if lead.attributes:
        with st.expander("🤖 KI-Spalten"):
            for key, value in lead.attributes.items():
                st.write(f"**{key}:** {value}")

    # Actions
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📇 Kontakt scrapen", key=f"scrape_{lead.id}"):
            scrape_single_contact(lead)

    with col2:
        if st.button("💬 Kompliment generieren", key=f"comp_{lead.id}"):
            generate_single_compliment(lead)

    with col3:
        if st.button("🗑️ Kompliment löschen", key=f"del_{lead.id}"):
            lead.compliment = None
            st.session_state.session.commit()
            st.success("Kompliment gelöscht!")
            st.rerun()

    with col4:
        if st.button("💀 Lead löschen", key=f"delete_{lead.id}"):
            st.session_state.session.delete(lead)
            st.session_state.session.commit()
            st.success("Lead gelöscht!")
            st.rerun()


# =====================
# Import Page
# =====================
def render_import_page():
    """CSV Import page"""

    st.markdown('<div class="page-title">CSV Import</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Importiere Leads aus CSV-Dateien</div>', unsafe_allow_html=True)

    st.info("💡 Die CSV sollte mindestens eine **website** Spalte enthalten. Unterstützt werden: name, website, phone, address, city, rating, reviews, review_keywords, etc.")

    uploaded_file = st.file_uploader("CSV auswählen", type=['csv'])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

            st.success(f"✅ {len(df)} Zeilen gefunden")

            if 'website' not in df.columns:
                st.error("❌ Die CSV muss eine 'website' Spalte enthalten!")
                return

            st.markdown("##### Vorschau")
            st.dataframe(df.head(10), use_container_width=True)

            st.markdown(f"**Spalten:** {', '.join(df.columns)}")

            col1, col2 = st.columns(2)
            with col1:
                skip_existing = st.checkbox("Existierende überspringen", value=True)
            with col2:
                auto_scrape = st.checkbox("Nach Import Kontakte scrapen", value=False)

            if st.button("🚀 Importieren", type="primary", use_container_width=True):
                import_csv_data(df, skip_existing, auto_scrape)

        except Exception as e:
            st.error(f"Fehler: {str(e)}")

    # Current Stats
    st.markdown("---")
    st.markdown("##### 📊 Datenbank")

    session = st.session_state.session
    total = session.query(CompanyV3).count()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Leads", f"{total:,}")
    col2.metric("Mit Namen", f"{session.query(CompanyV3).filter(CompanyV3.first_name.isnot(None)).count():,}")
    col3.metric("Mit Kompliment", f"{session.query(CompanyV3).filter(CompanyV3.compliment.isnot(None)).count():,}")


def import_csv_data(df, skip_existing=True, auto_scrape=False):
    """Import CSV data to database"""
    session = st.session_state.session

    progress = st.progress(0)
    status = st.empty()

    imported = 0
    skipped = 0
    imported_leads = []

    for idx, row in df.iterrows():
        website = str(row.get('website', '')).strip()
        if not website or website == 'nan':
            skipped += 1
            continue

        if skip_existing:
            existing = session.query(CompanyV3).filter_by(website=website).first()
            if existing:
                skipped += 1
                continue

        categories = []
        if pd.notna(row.get('categories')):
            categories = [c.strip() for c in str(row.get('categories')).split(',')]

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
        imported_leads.append(company)
        imported += 1

        if imported % 50 == 0:
            session.commit()

        progress.progress((idx + 1) / len(df))
        status.text(f"Importiere... {idx + 1}/{len(df)}")

    session.commit()
    progress.empty()
    status.empty()

    st.success(f"✅ {imported} importiert | ⏭️ {skipped} übersprungen")

    if auto_scrape and imported_leads:
        st.info("📇 Starte Kontakt-Scraping...")
        scrape_contacts_bulk(imported_leads)


# =====================
# AI Column Page (Clay-Style)
# =====================
def render_ai_column_page():
    """AI Column feature - Clay.com style"""

    st.markdown('<div class="page-title">KI-Spalten</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Erstelle neue Spalten mit KI-generierten Inhalten (wie Clay.com)</div>', unsafe_allow_html=True)

    session = st.session_state.session

    # Select leads
    st.markdown("##### 1️⃣ Leads auswählen")

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("Suche", placeholder="Filter nach Name/Website...", key="ai_search")
    with col2:
        limit = st.number_input("Limit", min_value=10, max_value=500, value=100, key="ai_limit")

    query = session.query(CompanyV3)
    if search:
        query = query.filter(or_(
            CompanyV3.name.ilike(f"%{search}%"),
            CompanyV3.website.ilike(f"%{search}%")
        ))

    leads = query.limit(limit).all()

    st.info(f"📊 {len(leads)} Leads verfügbar")

    st.markdown("---")

    # Column Configuration
    st.markdown("##### 2️⃣ Spalte konfigurieren")

    col1, col2 = st.columns(2)

    with col1:
        column_name = st.text_input(
            "Spaltenname",
            value="custom_field",
            help="Nur Buchstaben, Zahlen und Unterstriche"
        )

    with col2:
        # Example prompts
        example = st.selectbox(
            "Beispiel-Prompt",
            ["Eigener Prompt", "Personalisierte Intro", "Pain Points", "Sales Pitch", "Icebreaker", "Zusammenfassung"]
        )

    example_prompts = {
        "Personalisierte Intro": "Schreibe eine personalisierte Einleitung für eine Cold-Email an {name}. Nutze: Bewertung: {rating}/5, Stadt: {city}. Max 2 Sätze.",
        "Pain Points": "Identifiziere 3 mögliche Pain Points für {name} basierend auf: Branche: {category}, Bewertungen: {review_keywords}. Liste als Bullet Points.",
        "Sales Pitch": "Erstelle einen kurzen Sales-Pitch (3 Sätze) für {name}. Betone den Mehrwert basierend auf: {description}",
        "Icebreaker": "Schreibe einen kreativen Icebreaker für {first_name} {last_name} bei {name}. Nutze: {review_keywords}",
        "Zusammenfassung": "Fasse das Unternehmen {name} in 2-3 Sätzen zusammen: Beschreibung: {description}, Rating: {rating}, Reviews: {reviews}"
    }

    default_prompt = example_prompts.get(example, "") if example != "Eigener Prompt" else ""

    st.markdown("**System Prompt:**")
    system_prompt = st.text_area(
        "System",
        value="Du bist ein erfahrener B2B-Sales-Experte. Antworte präzise und professionell. Gib NUR die Antwort zurück.",
        height=80,
        label_visibility="collapsed"
    )

    st.markdown("**User Prompt:**")
    st.caption("Platzhalter: {name}, {website}, {email}, {first_name}, {last_name}, {phone}, {description}, {rating}, {reviews}, {review_keywords}, {category}, {city}, {compliment}")

    user_prompt = st.text_area(
        "Prompt",
        value=default_prompt,
        height=150,
        placeholder="Dein KI-Prompt hier...",
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Execute
    st.markdown("##### 3️⃣ Ausführen")

    if st.button(f"🚀 KI-Spalte für {len(leads)} Leads erstellen", type="primary", use_container_width=True):
        if not column_name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name):
            st.error("Ungültiger Spaltenname!")
            return

        if not user_prompt:
            st.error("Bitte gib einen Prompt ein!")
            return

        execute_ai_column(leads, column_name, user_prompt, system_prompt)

    # Show existing custom columns
    st.markdown("---")
    st.markdown("##### 📊 Vorhandene KI-Spalten")

    custom_columns = get_custom_columns()
    if custom_columns:
        st.write(", ".join([f"`{c}`" for c in custom_columns]))
    else:
        st.caption("Noch keine KI-Spalten erstellt")


def execute_ai_column(leads, column_name, user_prompt, system_prompt):
    """Execute AI column generation for all leads"""

    progress = st.progress(0)
    status = st.empty()

    success = 0
    errors = 0

    for idx, lead in enumerate(leads):
        status.text(f"Verarbeite {lead.name}... ({idx+1}/{len(leads)})")

        try:
            result = st.session_state.ai_processor.process_prompt(
                user_prompt,
                lead,
                system_prompt
            )

            if result:
                if lead.attributes is None:
                    lead.attributes = {}

                new_attrs = dict(lead.attributes)
                new_attrs[column_name] = result
                lead.attributes = new_attrs

                st.session_state.session.commit()
                success += 1
            else:
                errors += 1

        except Exception as e:
            errors += 1
            st.session_state.session.rollback()

        progress.progress((idx + 1) / len(leads))

    progress.empty()
    status.empty()

    st.success(f"✅ {success} erfolgreich | ❌ {errors} Fehler")


def get_custom_columns():
    """Get all custom column names from database"""
    columns = set()
    try:
        companies = st.session_state.session.query(CompanyV3).filter(
            CompanyV3.attributes.isnot(None)
        ).limit(1000).all()

        for company in companies:
            if company.attributes:
                columns.update(company.attributes.keys())
    except:
        pass

    return sorted(list(columns))


# =====================
# Prompts Page
# =====================
def render_prompts_page():
    """Prompt templates management"""

    st.markdown('<div class="page-title">Prompt Templates</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Verwalte Kompliment-Templates</div>', unsafe_allow_html=True)

    prompts = st.session_state.prompt_manager.prompts.get('prompts', [])

    for prompt in prompts:
        with st.expander(f"📝 {prompt.get('name', 'Unnamed')}"):
            st.caption(f"ID: {prompt.get('id')}")
            st.write(prompt.get('description', '-'))

            st.markdown("**System:**")
            st.code(prompt.get('system_prompt', ''), language=None)

            st.markdown("**Template:**")
            st.code(prompt.get('user_prompt_template', ''), language=None)

    st.markdown("---")
    st.markdown("##### Platzhalter")

    placeholders = ["{name}", "{rating}", "{reviews}", "{review_keywords}", "{category}", "{city}", "{first_name}", "{last_name}", "{description}"]
    st.write(" | ".join([f"`{p}`" for p in placeholders]))


# =====================
# Settings Page
# =====================
def render_settings_page():
    """Settings and configuration"""

    st.markdown('<div class="page-title">Einstellungen</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Konfiguration und Datenbank-Management</div>', unsafe_allow_html=True)

    session = st.session_state.session

    # API Config
    st.markdown("##### 🤖 API Konfiguration")

    try:
        with open('api_config.json', 'r') as f:
            api_config = json.load(f)
    except:
        api_config = {"active_api": "deepseek"}

    current_api = api_config.get('active_api', 'deepseek')

    api_providers = ['deepseek', 'openai', 'anthropic', 'groq']
    selected = st.selectbox("Aktiver Provider", api_providers, index=api_providers.index(current_api) if current_api in api_providers else 0)

    env_vars = {
        'deepseek': 'DEEPSEEK_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'groq': 'GROQ_API_KEY'
    }

    env_var = env_vars.get(selected)
    has_key = bool(os.environ.get(env_var, ''))

    if has_key:
        st.success(f"✅ {env_var} konfiguriert")
    else:
        st.warning(f"⚠️ {env_var} nicht gefunden")

    if st.button("💾 Speichern"):
        api_config['active_api'] = selected
        with open('api_config.json', 'w') as f:
            json.dump(api_config, f, indent=2)
        st.success("Gespeichert!")

    st.markdown("---")

    # Database Stats
    st.markdown("##### 📊 Datenbank")

    total = session.query(CompanyV3).count()
    with_names = session.query(CompanyV3).filter(CompanyV3.first_name.isnot(None)).count()
    with_email = session.query(CompanyV3).filter(CompanyV3.email.isnot(None)).count()
    with_compliment = session.query(CompanyV3).filter(CompanyV3.compliment.isnot(None)).count()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", f"{total:,}")
    col2.metric("Mit Namen", f"{with_names:,}")
    col3.metric("Mit E-Mail", f"{with_email:,}")
    col4.metric("Mit Kompliment", f"{with_compliment:,}")

    st.markdown("---")

    # Danger Zone
    st.markdown("##### ⚠️ Gefahrenzone")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Alle Komplimente löschen", use_container_width=True):
            if st.checkbox("Bestätigen", key="confirm_del_comp"):
                session.query(CompanyV3).update({CompanyV3.compliment: None})
                session.commit()
                st.success("Alle Komplimente gelöscht!")
                st.rerun()

    with col2:
        if st.button("💀 Alle Leads löschen", use_container_width=True):
            if st.checkbox("Bestätigen (ALLE DATEN!)", key="confirm_del_all"):
                session.query(CompanyV3).delete()
                session.commit()
                st.success("Alle Leads gelöscht!")
                st.rerun()


# =====================
# Bulk Operations
# =====================
def scrape_contacts_bulk(leads):
    """Scrape contacts for multiple leads"""
    leads_to_scrape = [l for l in leads if l.website and (not l.first_name or not l.email)]

    if not leads_to_scrape:
        st.warning("Keine Leads zum Scrapen")
        return

    progress = st.progress(0)
    status = st.empty()

    names_found = 0
    emails_found = 0

    for idx, lead in enumerate(leads_to_scrape):
        status.text(f"Scrape {lead.name}... ({idx+1}/{len(leads_to_scrape)})")

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

        except:
            pass

        progress.progress((idx + 1) / len(leads_to_scrape))

    st.session_state.session.commit()
    progress.empty()
    status.empty()

    st.success(f"✅ {names_found} Namen | {emails_found} E-Mails gefunden")
    st.rerun()


def generate_compliments_bulk(leads):
    """Generate compliments for multiple leads"""
    leads_to_process = [l for l in leads if not l.compliment and l.website]

    if not leads_to_process:
        st.warning("Keine Leads ohne Kompliment")
        return

    progress = st.progress(0)
    status = st.empty()

    generated = 0

    for idx, lead in enumerate(leads_to_process):
        status.text(f"Generiere für {lead.name}... ({idx+1}/{len(leads_to_process)})")

        try:
            result = st.session_state.compliment_generator.generate_compliment(lead)

            if result and result.get('compliment'):
                lead.compliment = result['compliment']
                lead.compliment_generated_at = datetime.now()
                generated += 1

            if idx % 5 == 0:
                st.session_state.session.commit()

        except:
            pass

        progress.progress((idx + 1) / len(leads_to_process))

    st.session_state.session.commit()
    progress.empty()
    status.empty()

    st.success(f"✅ {generated} Komplimente generiert")
    st.rerun()


def delete_compliments_bulk(leads):
    """Delete compliments for all leads"""
    count = 0
    for lead in leads:
        if lead.compliment:
            lead.compliment = None
            count += 1

    st.session_state.session.commit()
    st.success(f"✅ {count} Komplimente gelöscht")
    st.rerun()


def delete_leads_bulk(leads):
    """Delete all leads"""
    for lead in leads:
        st.session_state.session.delete(lead)

    st.session_state.session.commit()
    st.session_state.confirm_delete = False
    st.success(f"✅ {len(leads)} Leads gelöscht")
    st.rerun()


def scrape_single_contact(lead):
    """Scrape contact for single lead"""
    if not lead.website:
        st.error("Keine Website!")
        return

    with st.spinner("Scrape..."):
        try:
            result = st.session_state.impressum_scraper.scrape_all_contact_data(lead.website)

            if result.get('found_name'):
                lead.first_name = result.get('first_name')
                lead.last_name = result.get('last_name')

            if result.get('found_email'):
                lead.email = result.get('email')

            st.session_state.session.commit()
            st.success(f"✅ {result.get('first_name', '')} {result.get('last_name', '')} - {result.get('email', '')}")
            st.rerun()
        except Exception as e:
            st.error(f"Fehler: {e}")


def generate_single_compliment(lead):
    """Generate compliment for single lead"""
    with st.spinner("Generiere..."):
        try:
            result = st.session_state.compliment_generator.generate_compliment(lead)

            if result and result.get('compliment'):
                lead.compliment = result['compliment']
                lead.compliment_generated_at = datetime.now()
                st.session_state.session.commit()
                st.success("✅ Kompliment generiert!")
                st.rerun()
            else:
                st.error("Konnte kein Kompliment generieren")
        except Exception as e:
            st.error(f"Fehler: {e}")


# =====================
# Export Functions
# =====================
def export_csv(leads):
    """Export leads to CSV"""
    data = []
    for c in leads:
        row = {
            'Name': c.name,
            'Vorname': c.first_name,
            'Nachname': c.last_name,
            'E-Mail': c.email,
            'Telefon': c.phone,
            'Website': c.website,
            'Adresse': c.address,
            'Stadt': c.city,
            'PLZ': c.zip_code,
            'Rating': c.rating,
            'Reviews': c.review_count,
            'Kompliment': c.compliment,
            'Kategorie': c.main_category
        }
        # Add custom attributes
        if c.attributes:
            for key, value in c.attributes.items():
                row[f"KI_{key}"] = value
        data.append(row)

    df = pd.DataFrame(data)
    csv = df.to_csv(index=False, encoding='utf-8-sig')

    st.download_button(
        "💾 CSV herunterladen",
        csv,
        f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        "text/csv"
    )


def export_excel(leads):
    """Export leads to Excel"""
    data = []
    for c in leads:
        row = {
            'Name': c.name,
            'Vorname': c.first_name,
            'Nachname': c.last_name,
            'E-Mail': c.email,
            'Telefon': c.phone,
            'Website': c.website,
            'Adresse': c.address,
            'Stadt': c.city,
            'PLZ': c.zip_code,
            'Rating': c.rating,
            'Reviews': c.review_count,
            'Kompliment': c.compliment,
            'Kategorie': c.main_category
        }
        if c.attributes:
            for key, value in c.attributes.items():
                row[f"KI_{key}"] = value
        data.append(row)

    df = pd.DataFrame(data)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')

    st.download_button(
        "💾 Excel herunterladen",
        buffer.getvalue(),
        f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =====================
# Main App
# =====================
def main():
    init_session_state()

    page = render_sidebar()

    if page == "🔍 Leads":
        render_leads_page()
    elif page == "📤 Import":
        render_import_page()
    elif page == "🤖 KI-Spalten":
        render_ai_column_page()
    elif page == "💬 Prompts":
        render_prompts_page()
    elif page == "⚙️ Settings":
        render_settings_page()


if __name__ == "__main__":
    main()
