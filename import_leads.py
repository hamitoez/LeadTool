"""
Automatischer Import der Leads aus leads/all-task-3-overview.csv
"""
import pandas as pd
from models_v3 import DatabaseV3, CompanyV3

def import_leads_csv():
    """Importiert die CSV-Datei automatisch"""

    csv_file = "leads/all-task-3-overview.csv"

    print("=" * 70)
    print(" AUTOMATISCHER CSV-IMPORT")
    print("=" * 70)
    print(f"\nLese: {csv_file}")

    # CSV einlesen
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    total_rows = len(df)

    print(f"✅ {total_rows} Zeilen gefunden\n")

    # Datenbank
    db = DatabaseV3()
    session = db.get_session()

    imported = 0
    skipped = 0
    errors = 0

    print("Importiere...")

    for idx, row in df.iterrows():
        try:
            website = row.get('website', '').strip() if pd.notna(row.get('website')) else None

            # Skip wenn keine Website
            if not website:
                skipped += 1
                continue

            # Check ob bereits vorhanden
            existing = session.query(CompanyV3).filter_by(website=website).first()
            if existing:
                skipped += 1
                continue

            # Categories als JSON Array
            categories_str = row.get('categories', '')
            categories = []
            if pd.notna(categories_str) and categories_str:
                # Split by comma
                categories = [c.strip() for c in str(categories_str).split(',')]

            # Neue Company erstellen - AUTOMATISCHE ÜBERNAHME ALLER FELDER
            company = CompanyV3(
                # Basis
                website=website,
                name=row.get('name') if pd.notna(row.get('name')) else None,
                description=row.get('description') if pd.notna(row.get('description')) else None,
                phone=row.get('phone') if pd.notna(row.get('phone')) else None,

                # Kontakt-Person - NUR via Impressum-Scraper!
                first_name=None,  # Wird via "Namen aus Impressum scrapen" gefüllt
                last_name=None,   # Wird via "Namen aus Impressum scrapen" gefüllt
                email=None,       # Wird später angereichert

                # Kategorien - AUTOMATISCH aus CSV
                main_category=row.get('main_category') if pd.notna(row.get('main_category')) else None,
                industries=categories,  # Aus categories Spalte

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

            # Batch commit alle 50 Zeilen
            if imported % 50 == 0:
                session.commit()
                print(f"  {imported}/{total_rows}...")

        except Exception as e:
            session.rollback()
            errors += 1
            print(f"❌ Fehler bei Zeile {idx}: {e}")
            continue

    # Final commit
    session.commit()
    session.close()

    print("\n" + "=" * 70)
    print(" IMPORT ABGESCHLOSSEN")
    print("=" * 70)
    print(f"✅ Importiert: {imported}")
    print(f"⏭️  Übersprungen: {skipped}")
    print(f"❌ Fehler: {errors}")
    print("=" * 70)

    if imported > 0:
        print("\n🚀 Starte Anwendung: START_V3.bat")
    else:
        print("\n💡 Daten bereits vorhanden oder keine neuen Leads")


if __name__ == "__main__":
    import_leads_csv()
