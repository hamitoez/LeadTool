"""
Impressum Scraper - Kompatibilitäts-Wrapper
Verwendet den neuen Ultimate-Scraper mit der alten API-Signatur
"""
from impressum_scraper_ultimate import ImpressumScraperUltimate, ContactResult
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ImpressumScraper:
    """
    Wrapper-Klasse für Rückwärts-Kompatibilität
    Verwendet intern den ImpressumScraperUltimate
    """
    
    def __init__(self, api_config_file: str = "api_config.json"):
        self._scraper = ImpressumScraperUltimate(api_config_file)
    
    def normalize_url(self, website: str) -> Optional[str]:
        """Normalisiert Website-URL"""
        return self._scraper.normalize_url(website)
    
    def find_impressum_url(self, base_url: str) -> Optional[str]:
        """Findet Impressum-URL auf Website"""
        return self._scraper.find_impressum_url(base_url)
    
    def scrape_impressum_html(self, impressum_url: str) -> str:
        """Lädt Impressum-HTML"""
        return self._scraper.scrape_html(impressum_url)
    
    def extract_name_with_deepseek(self, html: str) -> tuple:
        """Extrahiert Namen (alte Signatur)"""
        first, last, _, _ = self._scraper.extract_name(html)
        return first, last
    
    def extract_name_fallback(self, html: str) -> tuple:
        """Regex-Fallback für Namen"""
        text = self._scraper.extract_clean_text(html)
        first, last = self._scraper._heuristic_extract_name(text)
        return first, last
    
    def extract_emails_from_html(self, html: str) -> List[str]:
        """Extrahiert E-Mails aus HTML"""
        return self._scraper.extract_emails(html)
    
    def scrape_impressum(self, website: str) -> Dict[str, Any]:
        """
        Scraped Namen aus Impressum (alte Signatur)
        
        Returns:
            dict: {
                'first_name': str,
                'last_name': str,
                'found': bool,
                'impressum_url': str
            }
        """
        result = self._scraper.scrape(website)
        
        return {
            'first_name': result.first_name,
            'last_name': result.last_name,
            'found': result.found_name,
            'impressum_url': result.impressum_url
        }
    
    def scrape_all_contact_data(self, website: str) -> Dict[str, Any]:
        """
        Scraped Namen UND E-Mail aus Impressum (alte Signatur)
        
        Returns:
            dict: {
                'first_name': str,
                'last_name': str,
                'email': str,
                'found_name': bool,
                'found_email': bool,
                'impressum_url': str
            }
        """
        result = self._scraper.scrape(website)
        
        return {
            'first_name': result.first_name,
            'last_name': result.last_name,
            'email': result.email,
            'found_name': result.found_name,
            'found_email': result.found_email,
            'impressum_url': result.impressum_url
        }
    
    def scrape_all_contact_data_multiple(self, companies, progress_callback=None) -> Dict[str, int]:
        """
        Scraped Kontaktdaten für mehrere Companies (alte Signatur)
        
        Args:
            companies: Liste von Objekten mit .website, .name, .first_name, .last_name, .email Attributen
            progress_callback: Optional - Funktion(current, total, company_name)
        
        Returns:
            dict: {'names_found': int, 'emails_found': int, 'total': int}
        """
        stats = {'names_found': 0, 'emails_found': 0, 'total': len(companies)}
        
        for idx, company in enumerate(companies):
            try:
                if progress_callback:
                    progress_callback(idx + 1, len(companies), getattr(company, 'name', None) or company.website)
                
                result = self._scraper.scrape(company.website)
                
                if result.found_name:
                    company.first_name = result.first_name
                    company.last_name = result.last_name
                    stats['names_found'] += 1
                
                if result.found_email:
                    company.email = result.email
                    stats['emails_found'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Fehler bei {company.website}: {e}")
                continue
        
        return stats
    
    def scrape_multiple(self, companies, progress_callback=None) -> int:
        """
        Scraped Namen für mehrere Companies (alte Signatur)
        
        Args:
            companies: Liste von Objekten mit .website, .name, .first_name, .last_name Attributen
            progress_callback: Optional - Funktion(current, total, company_name)
        
        Returns:
            int: Anzahl erfolgreich gescrapeter Namen
        """
        success_count = 0
        
        for idx, company in enumerate(companies):
            try:
                if progress_callback:
                    progress_callback(idx + 1, len(companies), getattr(company, 'name', None) or company.website)
                
                result = self._scraper.scrape(company.website)
                
                if result.found_name:
                    company.first_name = result.first_name
                    company.last_name = result.last_name
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Fehler bei {company.website}: {e}")
                continue
        
        return success_count


# ===== DIREKTER ZUGRIFF AUF ULTIMATE SCRAPER =====
def get_ultimate_scraper(api_config_file: str = "api_config.json") -> ImpressumScraperUltimate:
    """
    Factory-Funktion für den Ultimate-Scraper
    Empfohlen für neue Projekte
    """
    return ImpressumScraperUltimate(api_config_file)


# ===== TEST =====
if __name__ == "__main__":
    # Test mit altem Interface
    scraper = ImpressumScraper()
    
    # Test mit einzelner URL
    result = scraper.scrape_all_contact_data("https://example.com")
    print(f"Ergebnis (alte API): {result}")
    
    # Test mit neuem Ultimate-Scraper
    ultimate = get_ultimate_scraper()
    result = ultimate.scrape("https://example.com")
    print(f"Ergebnis (neue API): {result.to_dict()}")
