"""
Email Scraper - Extrahiert E-Mail-Adressen von Websites
VERBESSERTE VERSION mit hoher Erfolgsquote + Verschleierungs-Erkennung
"""
import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin, urlparse, unquote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException as SeleniumTimeout
from webdriver_manager.chrome import ChromeDriverManager
import time
import html

# Versuche dotenv zu laden (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# OpenAI optional für LLM-Fallback
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.info("OpenAI-Modul nicht installiert - LLM-Fallback nicht verfügbar")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EmailScraper:
    """Scraped E-Mail-Adressen von Websites mit Selenium für JS-Seiten"""

    def __init__(self, deepseek_api_key=None, use_llm_fallback=False):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # E-Mail Regex Pattern - Mehrere Patterns für bessere Erkennung
        self.email_patterns = [
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            re.compile(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),
            re.compile(r'["\']([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})["\']'),
        ]

        # Chrome driver setup
        try:
            self.chrome_driver_path = ChromeDriverManager().install()
            self.use_selenium = True
        except Exception as e:
            self.chrome_driver_path = None
            self.use_selenium = False
            logging.warning(f"ChromeDriver nicht verfügbar - nur requests: {e}")

        # Spam-Keywords erweitert
        self.spam_keywords = [
            'example.com', 'test@', 'noreply', 'no-reply', 'donotreply',
            'spam@', 'admin@localhost', 'webmaster@', 'postmaster@',
            'info@example', '@domain.com', '@test.', '@localhost'
        ]

        # DeepSeek LLM Fallback (optional)
        self.use_llm_fallback = False
        if use_llm_fallback and deepseek_api_key:
            if not OPENAI_AVAILABLE:
                logging.warning("LLM-Fallback aktiviert, aber OpenAI-Modul nicht installiert. Installiere mit: pip install openai")
            else:
                try:
                    self.llm_client = OpenAI(
                        api_key=deepseek_api_key,
                        base_url="https://api.deepseek.com"
                    )
                    self.use_llm_fallback = True
                    logging.info("✅ DeepSeek LLM-Fallback aktiviert")
                except Exception as e:
                    logging.warning(f"DeepSeek LLM konnte nicht initialisiert werden: {e}")
                    self.use_llm_fallback = False

    def normalize_url(self, website):
        """Normalisiert URL"""
        if not website:
            return None

        website = website.strip().rstrip('/')

        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website

        return website

    def find_contact_pages(self, base_url, html):
        """Findet Kontakt/Impressum-Seiten"""
        soup = BeautifulSoup(html, 'html.parser')
        contact_urls = []

        # Suche nach Links mit Kontakt/Impressum Keywords
        keywords = ['kontakt', 'contact', 'impressum', 'imprint', 'about', 'über']

        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text('', strip=True).lower()

            if any(keyword in href or keyword in text for keyword in keywords):
                full_url = urljoin(base_url, link['href'])
                if full_url not in contact_urls and urlparse(full_url).netloc == urlparse(base_url).netloc:
                    contact_urls.append(full_url)

        return contact_urls[:5]  # Max 5 Seiten

    def decode_obfuscated_emails(self, text):
        """
        Dekodiert verschleierte E-Mail-Adressen
        Erkennt ALLE gängigen Verschleierungsvarianten deutscher Impressum-Seiten
        """
        if not text:
            return text

        # HTML Entities dekodieren (&#64; → @, &#46; → ., etc.)
        text = html.unescape(text)

        # URL-Encoding dekodieren (%40 → @, %2E → .)
        text = text.replace('%40', '@').replace('%2E', '.')

        # @-Ersetzungen (alle Varianten: Klammern, Brackets, Leerzeichen, etc.)
        at_replacements = [
            # Deutsch
            r'\s*\(at\)\s*', r'\s*\[at\]\s*', r'\s*\{at\}\s*',
            r'\s*_at_\s*', r'\s*-at-\s*', r'\s+at\s+', r'\s*/at/\s*',
            r'\s*\(ät\)\s*', r'\s*\[ät\]\s*', r'\s+ät\s+',
            # Englisch
            r'\s*\(AT\)\s*', r'\s*\[AT\]\s*', r'\s*\{AT\}\s*',
            r'\s*_AT_\s*', r'\s*-AT-\s*', r'\s+AT\s+',
            # HTML Entities (bereits dekodiert oben, aber zur Sicherheit)
            r'&#64;', r'&#x40;',
        ]

        for pattern in at_replacements:
            text = re.sub(pattern, '@', text, flags=re.IGNORECASE)

        # Punkt-Ersetzungen für Domain-Endung
        dot_replacements = [
            # Deutsch
            r'\s*\(punkt\)\s*', r'\s*\[punkt\]\s*', r'\s*\{punkt\}\s*',
            r'\s*_punkt_\s*', r'\s*-punkt-\s*', r'\s+punkt\s+',
            r'\s*\(dot\)\s*', r'\s*\[dot\]\s*', r'\s*\{dot\}\s*',
            r'\s*_dot_\s*', r'\s*-dot-\s*', r'\s+dot\s+', r'\s*/dot/\s*',
            # Nur einzelner Punkt in Klammern/Brackets
            r'\s*\(\.\)\s*', r'\s*\[\.\]\s*',
            # HTML Entities
            r'&#46;', r'&#x2E;',
        ]

        for pattern in dot_replacements:
            text = re.sub(pattern, '.', text, flags=re.IGNORECASE)

        return text

    def validate_email(self, email):
        """
        Validiert E-Mail-Adresse nach strengen Kriterien
        Returns: True wenn gültig, False sonst
        """
        if not email or not isinstance(email, str):
            return False

        email = email.strip().lower()

        # Mindestlänge
        if len(email) < 5:
            return False

        # Genau ein @ Zeichen
        if email.count('@') != 1:
            return False

        # Keine Leerzeichen
        if ' ' in email:
            return False

        # Mindestens ein Punkt nach dem @
        local, domain = email.split('@')
        if '.' not in domain:
            return False

        # Local part nicht leer
        if not local or len(local) < 1:
            return False

        # Domain part validieren
        if not domain or len(domain) < 3:
            return False

        # TLD muss mindestens 2 Zeichen haben
        domain_parts = domain.split('.')
        if not domain_parts[-1] or len(domain_parts[-1]) < 2:
            return False

        # Basic regex check
        email_regex = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
        if not email_regex.match(email):
            return False

        return True

    def extract_emails_with_llm(self, text):
        """
        LLM-Fallback: Nutzt DeepSeek um E-Mails zu extrahieren
        Wird nur aufgerufen wenn Regex nichts findet
        """
        if not self.use_llm_fallback:
            return []

        try:
            # Begrenze Text auf 2000 Zeichen (Kosten sparen)
            text_snippet = text[:2000] if len(text) > 2000 else text

            prompt = f"""Du bist ein E-Mail-Extraktions-Experte. Analysiere den folgenden Text von einer deutschen Website (Impressum/Kontaktseite) und extrahiere ALLE E-Mail-Adressen.

WICHTIG:
- Erkenne auch verschleierte E-Mails wie "info (at) firma (dot) de" oder "mail[at]domain[punkt]com"
- Dekodiere alle Verschleierungen zu normalen E-Mails
- Gib NUR die E-Mail-Adressen zurück, eine pro Zeile
- Keine Erklärungen, keine Formatierung
- Wenn keine E-Mail gefunden: gib "KEINE" zurück

TEXT:
{text_snippet}

E-MAIL-ADRESSEN:"""

            response = self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Du bist ein präziser E-Mail-Extraktions-Assistent. Antworte nur mit E-Mail-Adressen, eine pro Zeile."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=200
            )

            result = response.choices[0].message.content.strip()

            if result and result != "KEINE":
                # Extrahiere E-Mails aus Antwort
                lines = result.split('\n')
                emails = []
                for line in lines:
                    line = line.strip()
                    if self.validate_email(line):
                        emails.append(line.lower())

                if emails:
                    logging.info(f"🤖 LLM fand {len(emails)} E-Mail(s): {emails}")
                    return emails

            return []

        except Exception as e:
            logging.warning(f"LLM-Fallback fehlgeschlagen: {e}")
            return []

    def extract_emails_advanced(self, html):
        """
        NEUE HAUPTMETHODE: Erweiterte E-Mail-Extraktion mit Verschleierungs-Erkennung

        Ablauf:
        1. HTML zu Text konvertieren
        2. Verschleierungen dekodieren
        3. Standard-Regex auf dekodiertem Text
        4. Validierung aller gefundenen E-Mails
        5. Optional: LLM-Fallback wenn nichts gefunden
        """
        emails = set()

        # Entferne Script und Style Tags
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()

        # 1. Text aus HTML extrahieren
        text = soup.get_text(separator=' ', strip=True)

        # 2. Verschleierungen dekodieren
        decoded_text = self.decode_obfuscated_emails(text)

        # 3. Standard-Regex auf dekodiertem Text anwenden
        for pattern in self.email_patterns:
            matches = pattern.findall(decoded_text)
            if matches:
                for match in matches:
                    # Handle tuple results from regex groups
                    email = match[0] if isinstance(match, tuple) else match
                    if self.validate_email(email):
                        emails.add(email.lower().strip())

        # 4. Suche in HTML-Attributen (mailto:, data-email, etc.)
        for tag in soup.find_all(['a', 'span', 'div', 'p']):
            # mailto: links
            href = tag.get('href', '')
            if 'mailto:' in href.lower():
                # Erst URL-Decoding, dann mailto: entfernen
                email = unquote(href).lower().replace('mailto:', '').split('?')[0].strip()
                # Dann Verschleierungen dekodieren
                email = self.decode_obfuscated_emails(email)
                if self.validate_email(email):
                    emails.add(email)

            # data-email attributes
            for attr in ['data-email', 'data-mail', 'email']:
                attr_value = tag.get(attr)
                if attr_value:
                    decoded_attr = self.decode_obfuscated_emails(attr_value.strip())
                    if self.validate_email(decoded_attr):
                        emails.add(decoded_attr.lower())

        # 5. Suche in HTML-Kommentaren
        for comment in soup.find_all(string=lambda t: isinstance(t, str)):
            decoded_comment = self.decode_obfuscated_emails(str(comment))
            for pattern in self.email_patterns:
                matches = pattern.findall(decoded_comment)
                if matches:
                    for match in matches:
                        email = match[0] if isinstance(match, tuple) else match
                        if self.validate_email(email):
                            emails.add(email.lower().strip())

        # Filtere Spam-E-Mails
        filtered_emails = {
            email for email in emails
            if not any(spam in email for spam in self.spam_keywords)
        }

        # 6. Optional: LLM-Fallback wenn nichts gefunden
        if not filtered_emails and self.use_llm_fallback:
            logging.info("🔄 Keine E-Mails mit Regex gefunden - versuche LLM-Fallback")
            llm_emails = self.extract_emails_with_llm(text)
            if llm_emails:
                # Validiere und filtere LLM-Ergebnisse
                for email in llm_emails:
                    if self.validate_email(email) and not any(spam in email for spam in self.spam_keywords):
                        filtered_emails.add(email)

        return list(filtered_emails)

    def extract_emails_from_html(self, html):
        """
        Extrahiert E-Mails aus HTML - WRAPPER für neue Methode
        Nutzt jetzt extract_emails_advanced() für Verschleierungs-Erkennung
        """
        return self.extract_emails_advanced(html)

    def get_with_selenium(self, url):
        """Lädt Seite mit Selenium für JS-Rendering"""
        driver = None
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            service = Service(self.chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)

            driver.set_page_load_timeout(15)
            driver.get(url)

            # Warte auf JS-Rendering
            time.sleep(3)

            return driver.page_source

        except SeleniumTimeout:
            logging.warning(f"Selenium-Timeout bei {url}")
            return None
        except WebDriverException as e:
            logging.error(f"Selenium WebDriver-Fehler: {e}")
            return None
        except Exception as e:
            logging.error(f"Selenium-Fehler: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except WebDriverException:
                    pass  # Driver bereits geschlossen

    def scrape_email(self, website):
        """
        Scraped E-Mail von Website - VERBESSERTE VERSION
        Returns: {'email': 'info@example.com', 'source': 'homepage'} oder None
        """
        try:
            base_url = self.normalize_url(website)
            if not base_url:
                return None

            logging.info(f"🔍 Scrape E-Mail von {base_url}")

            # 1. Homepage mit requests prüfen
            try:
                response = requests.get(base_url, headers=self.headers, timeout=10, allow_redirects=True)
                response.raise_for_status()

                emails = self.extract_emails_from_html(response.text)

                if emails:
                    logging.info(f"✅ E-Mail gefunden auf Homepage (requests): {emails[0]}")
                    return {
                        'email': emails[0],
                        'source': 'homepage',
                        'all_emails': emails
                    }

                # 2. Kontakt-Seiten prüfen
                contact_pages = self.find_contact_pages(base_url, response.text)

                for contact_url in contact_pages:
                    try:
                        response = requests.get(contact_url, headers=self.headers, timeout=10)
                        response.raise_for_status()

                        emails = self.extract_emails_from_html(response.text)

                        if emails:
                            logging.info(f"✅ E-Mail gefunden auf {contact_url}: {emails[0]}")
                            return {
                                'email': emails[0],
                                'source': contact_url,
                                'all_emails': emails
                            }

                    except Exception as e:
                        logging.debug(f"Fehler bei {contact_url}: {e}")
                        continue

            except requests.exceptions.RequestException as e:
                logging.warning(f"Requests fehlgeschlagen: {e}")

            # 3. Fallback: Selenium für JS-Seiten
            if self.use_selenium:
                logging.info(f"🔄 Versuche Selenium für {base_url}")

                html = self.get_with_selenium(base_url)
                if html:
                    emails = self.extract_emails_from_html(html)

                    if emails:
                        logging.info(f"✅ E-Mail gefunden mit Selenium: {emails[0]}")
                        return {
                            'email': emails[0],
                            'source': 'homepage (selenium)',
                            'all_emails': emails
                        }

                    # Selenium: Kontaktseiten
                    soup = BeautifulSoup(html, 'html.parser')
                    contact_pages = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '').lower()
                        text = link.get_text('', strip=True).lower()
                        keywords = ['kontakt', 'contact', 'impressum']

                        if any(keyword in href or keyword in text for keyword in keywords):
                            full_url = urljoin(base_url, link['href'])
                            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                                contact_pages.append(full_url)

                    for contact_url in contact_pages[:3]:
                        html = self.get_with_selenium(contact_url)
                        if html:
                            emails = self.extract_emails_from_html(html)
                            if emails:
                                logging.info(f"✅ E-Mail gefunden auf {contact_url} (selenium): {emails[0]}")
                                return {
                                    'email': emails[0],
                                    'source': contact_url,
                                    'all_emails': emails
                                }

            logging.warning(f"❌ Keine E-Mail gefunden für {base_url}")
            return None

        except Exception as e:
            logging.error(f"❌ Scraping-Fehler für {website}: {e}")
            return None
