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
# Custom CSS
# =====================
st.markdown("""
<style>
    /* Dark Theme Colors */
    :root {
        --bg-primary: #0f0f1e;
        --bg-secondary: #1a1a2e;
        --accent-primary: #3b82f6;
        --accent-success: #10b981;
        --accent-warning: #f59e0b;
        --accent-danger: #ef4444;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
    }

    /* Header Styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }

    /* Card Styling */
    .stMetric {
        background-color: #1e293b;
        padding: 1rem;
        border-radius: 10px;
    }

    /* Success/Warning/Error boxes */
    .success-box {
        padding: 1rem;
        background-color: #10b98120;
        border-left: 4px solid #10b981;
        border-radius: 0 8px 8px 0;
    }

    .warning-box {
        padding: 1rem;
        background-color: #f59e0b20;
        border-left: 4px solid #f59e0b;
        border-radius: 0 8px 8px 0;
    }

    /* Table Styling */
    .dataframe {
        font-size: 0.85rem;
    }

    /* Sidebar */
    .css-1d391kg {
        background-color: #1a1a2e;
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
        st.markdown("## 🚀 LeadTool v4.0")
        st.markdown("*Web Edition*")
        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["🔍 Filter & Suche", "📤 CSV Upload", "💬 Prompts", "🤖 API Config", "⚙️ Einstellungen"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Stats
        session = st.session_state.session
        total = session.query(CompanyV3).count()
        with_names = session.query(CompanyV3).filter(
            CompanyV3.first_name.isnot(None),
            CompanyV3.last_name.isnot(None)
        ).count()
        with_compliment = session.query(CompanyV3).filter(
            CompanyV3.compliment.isnot(None)
        ).count()

        st.markdown("### 📊 Datenbank")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", f"{total:,}")
        col2.metric("Namen", f"{with_names:,}")
        col3.metric("Komplimente", f"{with_compliment:,}")

        return page


# =====================
# Filter & Search Page
# =====================
def render_filter_page():
    """Render filter and search page"""
    st.markdown('<h1 class="main-header">🔍 Filter & Suche</h1>', unsafe_allow_html=True)

    session = st.session_state.session

    # Filter Section
    with st.expander("🎯 Filter-Optionen", expanded=True):
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

    # Quick Filters
    st.markdown("### ⚡ Schnellfilter")
    qf_col1, qf_col2, qf_col3, qf_col4 = st.columns(4)

    quick_filter = None
    with qf_col1:
        if st.button("✅ Kompletter Workflow", use_container_width=True):
            quick_filter = "complete"
    with qf_col2:
        if st.button("⚠️ Ohne Namen", use_container_width=True):
            quick_filter = "no_names"
    with qf_col3:
        if st.button("⚠️ Ohne Kompliment", use_container_width=True):
            quick_filter = "no_compliment"
    with qf_col4:
        if st.button("⭐ Top Rated (4.0+)", use_container_width=True):
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
    st.markdown(f"### 📋 Ergebnisse ({len(leads)} Leads)")

    # Action Buttons
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

    # Display Results
    if leads:
        df = get_leads_dataframe(leads)

        # Make table interactive with selection
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Website": st.column_config.LinkColumn("Website", width="medium"),
                "Rating": st.column_config.TextColumn("Rating", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small")
            }
        )

        # Lead Details Expander
        st.markdown("### 🔎 Lead-Details")
        selected_id = st.selectbox(
            "Lead auswählen",
            options=[lead.id for lead in leads],
            format_func=lambda x: next((f"{l.name} ({l.website})" for l in leads if l.id == x), str(x))
        )

        if selected_id:
            selected_lead = next((l for l in leads if l.id == selected_id), None)
            if selected_lead:
                render_lead_details(selected_lead)
    else:
        st.info("🔍 Keine Leads gefunden. Passe die Filter an oder importiere neue Leads.")


def render_lead_details(lead):
    """Render lead details"""
    with st.expander(f"📋 Details: {lead.name}", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🏢 Unternehmen**")
            st.write(f"**Name:** {lead.name or '-'}")
            st.write(f"**Website:** {lead.website or '-'}")
            st.write(f"**Telefon:** {lead.phone or '-'}")
            st.write(f"**Kategorie:** {lead.main_category or '-'}")

            st.markdown("**📍 Adresse**")
            st.write(f"{lead.address or '-'}")
            st.write(f"{lead.zip_code or ''} {lead.city or ''}")

        with col2:
            st.markdown("**👤 Kontaktperson**")
            st.write(f"**Vorname:** {lead.first_name or '-'}")
            st.write(f"**Nachname:** {lead.last_name or '-'}")
            st.write(f"**E-Mail:** {lead.email or '-'}")

            st.markdown("**⭐ Bewertung**")
            st.write(f"**Rating:** {lead.rating:.1f}" if lead.rating else "Kein Rating")
            st.write(f"**Reviews:** {lead.review_count or 0}")

        # Compliment
        if lead.compliment:
            st.markdown("**💬 Kompliment**")
            st.info(lead.compliment)

        # Review Keywords
        if lead.review_keywords:
            st.markdown("**📝 Review-Keywords**")
            st.text_area("Keywords", lead.review_keywords, height=100, disabled=True)

        # Actions
        st.markdown("---")
        action_col1, action_col2, action_col3 = st.columns(3)

        with action_col1:
            if st.button("📇 Kontakte scrapen", key=f"scrape_{lead.id}"):
                scrape_single_contact(lead)

        with action_col2:
            if st.button("💬 Kompliment generieren", key=f"gen_{lead.id}"):
                generate_single_compliment(lead)

        with action_col3:
            if st.button("🗑️ Kompliment löschen", key=f"del_{lead.id}"):
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
    st.markdown('<h1 class="main-header">📤 CSV Upload</h1>', unsafe_allow_html=True)

    st.info("""
    💡 **Tipp:** Du kannst CSV-Dateien von Google Maps Scraper oder anderen Quellen hochladen.
    Die CSV sollte mindestens eine **'website'** Spalte enthalten.
    """)

    uploaded_file = st.file_uploader(
        "CSV-Datei auswählen",
        type=['csv'],
        help="Unterstützte Spalten: name, website, phone, address, city, rating, reviews, review_keywords, etc."
    )

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

            st.success(f"✅ {len(df)} Zeilen gefunden")

            # Check for website column
            if 'website' not in df.columns:
                st.error("❌ Die CSV-Datei muss eine 'website' Spalte enthalten!")
                return

            # Preview
            st.markdown("### 📋 Vorschau")
            st.dataframe(df.head(10), use_container_width=True)

            st.markdown(f"**Spalten:** {', '.join(df.columns)}")

            # Import options
            col1, col2 = st.columns(2)

            with col1:
                auto_scrape = st.checkbox("📇 Nach Import automatisch Kontakte scrapen", value=False)

            with col2:
                skip_existing = st.checkbox("⏭️ Existierende überspringen", value=True)

            if st.button("✅ Importieren", type="primary", use_container_width=True):
                import_csv(df, auto_scrape, skip_existing)

        except Exception as e:
            st.error(f"❌ Fehler beim Lesen der CSV: {str(e)}")

    # Database Stats
    st.markdown("---")
    st.markdown("### 📊 Datenbank-Status")

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
    st.markdown('<h1 class="main-header">💬 Prompt Templates</h1>', unsafe_allow_html=True)

    st.info("""
    💡 Hier kannst du Prompt-Templates für die Kompliment-Generierung verwalten.
    Jeder Prompt kann individuell angepasst werden.
    """)

    # Load prompts
    prompts_data = st.session_state.prompt_manager.prompts.get('prompts', [])

    for prompt in prompts_data:
        with st.expander(f"📝 {prompt.get('name', 'Unnamed')}", expanded=False):
            st.markdown(f"**ID:** `{prompt.get('id', 'N/A')}`")
            st.markdown(f"**Beschreibung:** {prompt.get('description', '-')}")

            st.markdown("**System Prompt:**")
            st.text_area(
                "System",
                prompt.get('system_prompt', ''),
                height=100,
                key=f"sys_{prompt.get('id')}",
                disabled=True
            )

            st.markdown("**User Prompt Template:**")
            st.text_area(
                "User",
                prompt.get('user_prompt_template', ''),
                height=150,
                key=f"user_{prompt.get('id')}",
                disabled=True
            )

    # Placeholder info
    st.markdown("---")
    st.markdown("### ✏️ Custom Prompt erstellen")
    st.info("""
    **Verfügbare Platzhalter:**
    - `{name}` - Firmenname
    - `{rating}` - Google Rating
    - `{reviews}` - Anzahl Reviews
    - `{review_keywords}` - Extrahierte Keywords aus Reviews
    - `{category}` - Hauptkategorie
    - `{city}` - Stadt
    - `{first_name}` - Vorname
    - `{last_name}` - Nachname
    - `{description}` - Firmenbeschreibung
    """)


# =====================
# API Config Page
# =====================
def render_api_page():
    """Render API configuration page"""
    st.markdown('<h1 class="main-header">🤖 API Konfiguration</h1>', unsafe_allow_html=True)

    st.info("""
    💡 Konfiguriere hier deine API-Keys für verschiedene LLM-Provider.
    Der API-Key sollte in der `.env` Datei gespeichert werden.
    """)

    # Load config
    try:
        with open('api_config.json', 'r', encoding='utf-8') as f:
            api_config = json.load(f)
    except:
        api_config = {"apis": {}, "active_api": "deepseek"}

    current_api = api_config.get('active_api', 'deepseek')

    st.success(f"✅ Aktuell aktiv: **{current_api.upper()}**")

    # API Selection
    api_providers = ['deepseek', 'openai', 'anthropic', 'groq']

    selected_api = st.selectbox(
        "API Provider auswählen",
        api_providers,
        index=api_providers.index(current_api) if current_api in api_providers else 0
    )

    # Environment variable info
    st.markdown("---")
    st.markdown("### 🔑 API Key Konfiguration")

    env_vars = {
        'deepseek': 'DEEPSEEK_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'groq': 'GROQ_API_KEY'
    }

    env_var = env_vars.get(selected_api, 'API_KEY')
    current_key = os.environ.get(env_var, '')

    st.markdown(f"""
    **Umgebungsvariable:** `{env_var}`

    **Status:** {'✅ Konfiguriert' if current_key else '❌ Nicht konfiguriert'}
    """)

    if not current_key:
        st.warning(f"""
        ⚠️ API Key nicht gefunden!

        Füge folgende Zeile zu deiner `.env` Datei hinzu:
        ```
        {env_var}=dein-api-key-hier
        ```
        """)

    # Save button
    if st.button("💾 Als aktiv setzen", type="primary"):
        api_config['active_api'] = selected_api
        with open('api_config.json', 'w', encoding='utf-8') as f:
            json.dump(api_config, f, indent=2)
        st.success(f"✅ {selected_api.upper()} als aktiv gesetzt!")
        st.rerun()


# =====================
# Settings Page
# =====================
def render_settings_page():
    """Render settings page"""
    st.markdown('<h1 class="main-header">⚙️ Einstellungen</h1>', unsafe_allow_html=True)

    session = st.session_state.session

    # Database Stats
    st.markdown("### 🗄️ Datenbank")

    total = session.query(CompanyV3).count()
    with_names = session.query(CompanyV3).filter(
        CompanyV3.first_name.isnot(None)
    ).count()
    with_compliment = session.query(CompanyV3).filter(
        CompanyV3.compliment.isnot(None)
    ).count()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Leads", f"{total:,}")
    col2.metric("Mit Namen", f"{with_names:,}")
    col3.metric("Mit Kompliment", f"{with_compliment:,}")

    st.markdown("---")

    # Danger Zone
    st.markdown("### ⚠️ Gefahrenzone")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Alle Komplimente löschen", type="secondary"):
            if st.checkbox("Ja, ich bin sicher", key="confirm_delete_compliments"):
                session.query(CompanyV3).update({
                    CompanyV3.compliment: None,
                    CompanyV3.confidence_score: None,
                    CompanyV3.compliment_generated_at: None
                })
                session.commit()
                st.success("✅ Alle Komplimente gelöscht!")
                st.rerun()

    with col2:
        if st.button("💀 Alle Leads löschen", type="secondary"):
            if st.checkbox("Ja, ich bin sicher (ALLE DATEN WERDEN GELÖSCHT)", key="confirm_delete_all"):
                session.query(CompanyV3).delete()
                session.commit()
                st.success("✅ Alle Leads gelöscht!")
                st.rerun()

    st.markdown("---")

    # Export all
    st.markdown("### 📥 Komplett-Export")

    if st.button("📥 Alle Leads als CSV exportieren"):
        all_leads = session.query(CompanyV3).all()
        if all_leads:
            csv_data = export_leads_to_csv(all_leads)
            st.download_button(
                label="💾 Download starten",
                data=csv_data,
                file_name=f"all_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("Keine Leads zum Exportieren vorhanden.")


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
