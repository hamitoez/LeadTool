"""
Fresh Import: Leert Datenbank und importiert CSV neu
"""
import pandas as pd
from models_v3 import DatabaseV3, CompanyV3

def fresh_import():
    """Leert DB und importiert CSV neu"""

    print("="*60)
    print("FRESH IMPORT - Datenbank wird neu geladen")
    print("="*60)

    # Datenbank
    db = DatabaseV3()
    session = db.get_session()

    # Schritt 1: Lösche alle existierenden Daten
    print("\n[1/3] Lösche existierende Daten...")
    count_before = session.query(CompanyV3).count()
    print(f"      Aktuell in DB: {count_before} Firmen")

    session.query(CompanyV3).delete()
    session.commit()
    print("      Alle Daten gelöscht!")

    # Schritt 2: CSV laden
    csv_path = 'leads/all-task-3-overview.csv'
    print(f"\n[2/3] Lade CSV: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"      Gefunden: {len(df)} Leads in CSV")

    # Schritt 3: Importieren
    print(f"\n[3/3] Importiere {len(df)} Leads...")

    imported = 0
    skipped = 0

    for idx, row in df.iterrows():
        website = row.get('website')

        if pd.isna(website) or not website:
            skipped += 1
            continue

        # Check Duplikat
        exists = session.query(CompanyV3).filter(
            CompanyV3.website == website
        ).first()

        if exists:
            skipped += 1
            continue

        # Categories parsen
        categories = []
        categories_str = row.get('categories')
        if pd.notna(categories_str) and categories_str:
            categories = [c.strip() for c in str(categories_str).split(',')]

        # Neue Company erstellen
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

            # Rating
            rating=float(row.get('rating')) if pd.notna(row.get('rating')) and row.get('rating') != '' else None,
            review_count=int(row.get('reviews')) if pd.notna(row.get('reviews')) and str(row.get('reviews')).strip() != '' else None,

            # CSV-spezifisch
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
            attributes={},
            country="Deutschland"
        )

        session.add(company)
        imported += 1

        # Batch commit
        if imported % 50 == 0:
            session.commit()
            print(f"      Importiert: {imported}/{len(df)}...")

    session.commit()

    print(f"\n{'='*60}")
    print(f"IMPORT ABGESCHLOSSEN")
    print(f"{'='*60}")
    print(f"Importiert: {imported} Leads")
    print(f"Übersprungen: {skipped} Leads")
    print(f"\nDatenbank ist jetzt aktuell mit der CSV!")
    print(f"Starte die Anwendung neu: python gui_modern.py")

if __name__ == "__main__":
    try:
        fresh_import()
    except Exception as e:
        print(f"\n[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
