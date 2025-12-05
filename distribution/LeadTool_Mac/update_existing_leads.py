"""
Update-Script: Aktualisiert existierende Leads mit Daten aus CSV
OHNE Scraping-Ergebnisse (Namen, E-Mails, Komplimente) zu überschreiben
"""
import pandas as pd
from models_v3 import DatabaseV3, CompanyV3

def update_leads_from_csv():
    """Update existierende Leads mit CSV-Daten"""

    # CSV laden
    csv_path = 'leads/all-task-3-overview.csv'
    print(f"Lade CSV: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"Gefunden: {len(df)} Leads in CSV")

    # Datenbank
    db = DatabaseV3()
    session = db.get_session()

    updated = 0
    not_found = 0

    print("\nAktualisiere Leads...\n")

    for idx, row in df.iterrows():
        website = row.get('website')

        if pd.isna(website) or not website:
            continue

        # Finde existierenden Lead
        company = session.query(CompanyV3).filter(
            CompanyV3.website == website
        ).first()

        if not company:
            not_found += 1
            continue

        # UPDATE NUR FELDER DIE NICHT DURCH SCRAPING GEFÜLLT WERDEN
        # Basis-Daten aktualisieren
        if pd.notna(row.get('rating')):
            company.rating = float(row.get('rating'))

        if pd.notna(row.get('reviews')) and str(row.get('reviews')).strip() != '':
            company.review_count = int(row.get('reviews'))

        if pd.notna(row.get('description')):
            company.description = row.get('description')

        if pd.notna(row.get('owner_name')):
            company.owner_name = row.get('owner_name')

        if pd.notna(row.get('review_keywords')):
            company.review_keywords = row.get('review_keywords')

        if pd.notna(row.get('workday_timing')):
            company.workday_timing = row.get('workday_timing')

        if pd.notna(row.get('competitors')):
            company.competitors = row.get('competitors')

        if pd.notna(row.get('place_id')):
            company.place_id = row.get('place_id')

        if pd.notna(row.get('link')):
            company.link = row.get('link')

        if pd.notna(row.get('query')):
            company.query = row.get('query')

        if pd.notna(row.get('featured_image')):
            company.featured_image = row.get('featured_image')

        if pd.notna(row.get('owner_profile_link')):
            company.owner_profile_link = row.get('owner_profile_link')

        if pd.notna(row.get('closed_on')):
            company.closed_on = row.get('closed_on')

        # Categories
        categories_str = row.get('categories')
        if pd.notna(categories_str) and categories_str:
            categories = [c.strip() for c in str(categories_str).split(',')]
            company.industries = categories

        updated += 1

        if updated % 20 == 0:
            print(f"Aktualisiert: {updated} Leads...")
            session.commit()

    session.commit()

    print(f"\n{'='*60}")
    print(f"UPDATE ABGESCHLOSSEN")
    print(f"{'='*60}")
    print(f"Aktualisiert: {updated} Leads")
    print(f"Nicht gefunden: {not_found} Leads")
    print(f"\nWICHTIG: Scraping-Daten (Namen, E-Mails, Komplimente) wurden NICHT überschrieben!")

if __name__ == "__main__":
    try:
        update_leads_from_csv()
    except Exception as e:
        print(f"\n[ERROR] Update failed: {e}")
        import traceback
        traceback.print_exc()
