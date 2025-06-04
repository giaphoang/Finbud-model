import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re
import xml.etree.ElementTree as ET # For parsing XML
from selenium import webdriver # Added for Selenium
from selenium.webdriver.chrome.options import Options as ChromeOptions # Added for headless option

from aws_lambda_powertools import Logger
from core.db.documents import MacroEconomicReportDocument, Content, Section # Metadata model is no longer used here
from data_crawling.crawlers.base import BaseCrawler

logger = Logger(service="llm-twin-course/fomc-crawler-xml")

class FOMCEconomicCrawler(BaseCrawler):
    model = MacroEconomicReportDocument
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }

    def __init__(self) -> None:
        super().__init__()
        # Initialize Selenium WebDriver
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless") # Run headless so it doesn't open a browser window
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium WebDriver initialized successfully (Headless Chrome).")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {e}", exc_info=True)
            self.driver = None # Ensure driver is None if init fails

    def __del__(self):
        # Ensure the driver is quit when the crawler object is destroyed
        if hasattr(self, 'driver') and self.driver:
            logger.info("Quitting Selenium WebDriver.")
            self.driver.quit()

    def _parse_meeting_date_from_title(self, title: str) -> datetime | None:
        logger.info(f"Attempting to parse date from title (repr): {repr(title)}")

        # Pattern 1: "Meeting, Month Day1-Day2, Year" (e.g., "Meeting, May 6-7, 2025")
        # Also handles cross-month ranges like "Meeting, January 31-February 1, 2023" by taking Jan 31.
        match_range = re.search(r"Meeting,\s*(\w+)\s+(\d{1,2})(?:-\w+\s+\d{1,2}|-\d{1,2})?,\s*(\d{4})", title)
        if match_range:
            month_str, day1_str, year_str = match_range.groups()
            # The regex is a bit broad for the second part of range to handle cross-month, so we only use month_str, day1_str, year_str
            date_to_parse_str = f"{month_str} {day1_str}, {year_str}"
            logger.info(f"Pattern 1 (Range/Single Day) matched. Groups: ('{month_str}', '{day1_str}', '{year_str}'). Constructed: '{date_to_parse_str}'")
            try:
                return datetime.strptime(date_to_parse_str, "%B %d, %Y")
            except ValueError as e:
                logger.warning(f"Pattern 1: strptime failed for '{date_to_parse_str}': {e}. Trying next patterns.")

        # Pattern 2: "Meeting, Month Day, Year" (explicit single day, simpler regex than above if range failed)
        # This is a more specific fallback if the broader Pattern 1 failed on strptime for a non-range that looked like a range start.
        match_single_strict = re.search(r"Meeting,\s*(\w+\s+\d{1,2},\s+\d{4})", title) # Captures full "Month Day, Year"
        if match_single_strict:
            date_text = match_single_strict.group(1)
            logger.info(f"Pattern 2 (Strict Single Day) matched. Date text: '{date_text}'")
            try:
                return datetime.strptime(date_text, "%B %d, %Y")
            except ValueError as e:
                logger.warning(f"Pattern 2: strptime failed for '{date_text}': {e}. Trying next patterns.")

        # Pattern 3: "Meeting, Month Year" (no day, e.g., "Meeting, January 2024")
        match_month_year = re.search(r"Meeting,\s*(\w+\s+\d{4})", title)
        if match_month_year:
            date_text_my = match_month_year.group(1)
            logger.info(f"Pattern 3 (Month Year) matched. Date text: '{date_text_my}'")
            try:
                return datetime.strptime(date_text_my, "%B %Y") # Defaults to 1st of month
            except ValueError as e:
                logger.warning(f"Pattern 3: strptime failed for '{date_text_my}': {e}. Trying next patterns.")

        # Pattern 4: YYYY-MM-DD anywhere in the title (e.g., from "Meeting, 2024-03-19")
        match_ymd = re.search(r"(\d{4}-\d{2}-\d{2})", title)
        if match_ymd:
            date_text_ymd = match_ymd.group(1)
            logger.info(f"Pattern 4 (YYYY-MM-DD) matched. Date text: '{date_text_ymd}'")
            try:
                return datetime.strptime(date_text_ymd, "%Y-%m-%d")
            except ValueError as e:
                logger.warning(f"Pattern 4: strptime failed for '{date_text_ymd}': {e}")

        logger.error(f"CRITICAL: Could not parse date from title '{title}' using any defined format.")
        return None

    def _fetch_raw_content(self, url: str) -> str | None:
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
            logger.info(f"Successfully fetched content from {url}")
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch content from {url}: {e}")
            return None

    def _extract_text_url_from_xml(self, xml_content: str, base_url: str) -> str | None:
        try:
            root = ET.fromstring(xml_content)
            # Define the MODS namespace (usually found in the root element of FRASER XML)
            # The log showed: <Element '{http://www.loc.gov/mods/v3}modsCollection' ...>
            # So the namespace URI is http://www.loc.gov/mods/v3
            namespaces = {'mods': 'http://www.loc.gov/mods/v3'}

            # print("test root XML",root) # Your existing print
            
            # Strategy: Find all <mods:location> elements, then <mods:textUrl> within them.
            # Then filter for the one containing "fomcminutes" in its URL path.
            
            target_text_url = None

            # Find all textUrl elements directly, respecting the namespace
            all_text_url_elements = root.findall(".//mods:location/mods:textUrl", namespaces)
            if not all_text_url_elements: # Fallback if mods:location isn't directly above textUrl, or for simpler structures
                all_text_url_elements = root.findall(".//mods:textUrl", namespaces)
            
            logger.info(f"Found {len(all_text_url_elements)} <textUrl> elements using MODS namespace.")

            for text_url_el in all_text_url_elements:
                if text_url_el.text:
                    url_text = text_url_el.text.strip()
                    logger.debug(f"Checking textUrl: {url_text}")
                    # We want the one that specifically refers to "fomcminutes"
                    if "fomcminutes" in url_text.lower():
                        target_text_url = url_text
                        logger.info(f"Found target FOMC minutes textURL: {target_text_url}")
                        break # Found the specific minutes URL
            
            if target_text_url:
                return urljoin(base_url, target_text_url) # Ensure it's an absolute URL

            # Fallback if no "fomcminutes" specific URL found, try original broader search but with namespace
            logger.warning("Could not find a 'fomcminutes' specific textURL. Trying broader XML search with namespace...")
            for tag_name in ['textURL', 'texturl', 'TEXTURL']: # These might exist without namespace or with different one
                # Try with mods namespace first for these generic tags if they are directly under a mods element
                text_url_element = root.find(f".//mods:{tag_name}", namespaces)
                if text_url_element is None:
                     text_url_element = root.find(f".//{tag_name}") # Try without namespace as a last resort for these tags

                if text_url_element is not None and text_url_element.text:
                    text_url = text_url_element.text.strip()
                    logger.info(f"Found textURL (fallback with generic tag '{tag_name}'): {text_url}")
                    return urljoin(base_url, text_url)

            logger.warning("Still could not find a clear textURL in the XML content after all strategies.")
            return None
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML content: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error extracting text URL from XML: {e}", exc_info=True)
            return None

    def extract_single_meeting_data(self, meeting_page_url: str, meeting_title: str):
        logger.info(f"Processing meeting page: {meeting_page_url} - Title: {meeting_title}")

        meeting_date = self._parse_meeting_date_from_title(meeting_title)
        if not meeting_date:
            logger.warning(f"Could not parse date for '{meeting_title}'. Skipping this meeting.")
            return

        # Check if document already exists
        existing_doc = self.model.find(date=meeting_date, type="fomc")
        if existing_doc:
            logger.info(f"FOMC data for {meeting_date.strftime('%Y-%m-%d')} (Title: {meeting_title}) already exists. Skipping.")
            return
        # print("test meeting page url",meeting_page_url)
        meeting_page_content = self._fetch_raw_content(meeting_page_url)
        # print("test meeting page content",meeting_page_content)
        if not meeting_page_content:
            return

        page_soup = BeautifulSoup(meeting_page_content, 'html.parser')

        # Find the "Metadata (XML)" link based on the HTML structure shown in the image
        xml_link_tag = None
        
        # Look for the specific link with href containing "metadata.php?type=itemid"
        # This appears to be the pattern used for XML metadata links on FRASER
        # Find the main container element first
        main_container = page_soup.find('main', class_='container-xl')
        # print("test main container",main_container)
        if not main_container:
            logger.warning(f"Could not find main container with class 'container-xl' on page: {meeting_page_url}")
            return
        
        # Look for div with id "content" within the main container
        content_div = main_container.find('div', id='content')
        # print("test content div", content_div)
        
        # Look for div with id "fraser-pdfviewer-root" within the main container
        # Use Selenium driver to handle JS-rendered content
        self.driver.get(meeting_page_url)
        
        # Wait for the JS content to load
        import time
        time.sleep(3)
        
        # Find the pdfviewer div using Selenium
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Wait for the pdfviewer div to be present
            pdfviewer_div_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "fraser-pdfviewer-root"))
            )
            print("test pdfviewer div found with Selenium",  pdfviewer_div_element)
            
            # Get all elements inside pdfviewer div
            all_elements = pdfviewer_div_element.find_elements(By.XPATH, ".//*")
            print(f"test all elements inside pdfviewer div: {len(all_elements)} elements found")
            
            # Look for div with class "additional-metadata" within the pdfviewer div
            try:
                additional_metadata_div_element = pdfviewer_div_element.find_element(By.CLASS_NAME, "additional-metadata")
                print("test additional metadata div found with Selenium", additional_metadata_div_element)
                
                # Convert back to BeautifulSoup for easier parsing if needed
                page_source = self.driver.page_source
                updated_soup = BeautifulSoup(page_source, 'html.parser')
                additional_metadata_div = updated_soup.find('div', class_='additional-metadata')
                print("test additional metadata div converted to BeautifulSoup")
                
            except Exception as e:
                logger.warning(f"Could not find additional-metadata div with Selenium: {e}")
                additional_metadata_div = None
                
        except Exception as e:
            logger.warning(f"Could not find fraser-pdfviewer-root div with Selenium: {e}")
            additional_metadata_div = None
        
        if not additional_metadata_div:
            logger.warning(f"Could not find div with class 'additional-metadata' on page: {meeting_page_url}")
            return
        
        
        # Look for div with class "metadata-spacing" within the main container
        metadata_divs = additional_metadata_div.find_all('div', class_='metadata-spacing')
        print("test metadata divs",metadata_divs)
        
        for metadata_div in metadata_divs:
            # Find the link with "Metadata (XML)" text within this div
            links_in_div = metadata_div.find_all('a', href=True)
            for link in links_in_div:
                link_text = link.get_text(strip=True)
                print("test link text",link_text)
                if 'Metadata (XML)' in link_text:
                    xml_link_tag = link
                    logger.info(f"Found XML metadata link in metadata-spacing div: {link_text} -> {link.get('href')}")
                    break
            
            if xml_link_tag:
                break
        if not xml_link_tag or not xml_link_tag.get('href'):
            logger.warning(f"No XML metadata link found in metadata-spacing divs on page: {meeting_page_url} for meeting: {meeting_title}")
            return
        
        # print("test xml link tag",xml_link_tag)
        
        xml_url = urljoin(meeting_page_url, xml_link_tag['href'])
        raw_xml_metadata = self._fetch_raw_content(xml_url)
        if not raw_xml_metadata:
            logger.warning(f"Failed to fetch XML metadata from {xml_url} for meeting: {meeting_title}")
            return
        
        print("test raw xml metadata",raw_xml_metadata)

        # Attempt to parse date from XML if title parsing was weak or for confirmation
        try:
            xml_root = ET.fromstring(raw_xml_metadata)
            print("test xml root",xml_root)
            # Common date tags in DC or MODS metadata
            date_elements = xml_root.findall(".//{*}dateIssued") + xml_root.findall(".//dateIssued") + \
                            xml_root.findall(".//{*}date") + xml_root.findall(".//date")
            for date_el in date_elements:
                if date_el.text:
                    try:
                        # FRASER XML often has YYYY-MM-DD or YYYY-MM or YYYY
                        parsed_xml_date = None
                        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_el.text.strip()):
                             parsed_xml_date = datetime.strptime(date_el.text.strip(), "%Y-%m-%d")
                        elif re.match(r"^\d{4}-\d{2}$", date_el.text.strip()):
                             parsed_xml_date = datetime.strptime(date_el.text.strip(), "%Y-%m")
                        elif re.match(r"^\d{4}$", date_el.text.strip()):
                             parsed_xml_date = datetime.strptime(date_el.text.strip(), "%Y")
                        
                        if parsed_xml_date:
                            logger.info(f"Date from XML '{date_el.text.strip()}' parsed as {parsed_xml_date}. Original from title was {meeting_date}.")
                            # Decide if XML date is better. For now, prefer more specific one.
                            if meeting_date.day == 1 and meeting_date.month == 1 and parsed_xml_date.year == meeting_date.year: # if title date was just year
                                meeting_date = parsed_xml_date
                            elif parsed_xml_date.strftime("%Y-%m-%d") != meeting_date.strftime("%Y-%m-%d"):
                                 if parsed_xml_date.day != 1: # If XML date is specific
                                     logger.info(f"Updating meeting date to XML provided specific date: {parsed_xml_date}")
                                     meeting_date = parsed_xml_date
                            break 
                    except ValueError:
                        logger.debug(f"Could not parse date '{date_el.text}' from XML for {meeting_title}")
        except ET.ParseError:
            logger.warning(f"Could not parse XML to refine date for {meeting_title}")


        # Re-check if document already exists with potentially refined date
        existing_doc_after_xml_date = self.model.find(date=meeting_date, type="fomc")
        if existing_doc_after_xml_date:
            logger.info(f"FOMC data for refined date {meeting_date.strftime('%Y-%m-%d')} (Title: {meeting_title}) already exists. Skipping.")
            return

        text_content_url = self._extract_text_url_from_xml(raw_xml_metadata, xml_url) # xml_url as base for relative paths
        if not text_content_url:
            logger.warning(f"No textURL found in XML for meeting: {meeting_title} (XML URL: {xml_url})")
            # Log part of XML to help debug textURL extraction
            logger.debug(f"XML Metadata Snippet (first 1000 chars for debugging textURL):\\n{raw_xml_metadata[:1000]}")
            return

        plain_text_content = self._fetch_raw_content(text_content_url)
        if not plain_text_content:
            logger.warning(f"Failed to fetch plain text content from {text_content_url} for meeting: {meeting_title}")
            return
            
        # Construct the document
        doc_title = f"FOMC Meeting Minutes - {meeting_date.strftime('%Y-%m-%d')} - {meeting_title}"
        
        doc_content_obj = Content(
            title=doc_title,
            sections=[Section(heading="Full Transcript", text=plain_text_content.strip())]
        )

        instance = self.model(
            date=meeting_date,
            type="fomc",
            content=doc_content_obj,
            metadata=raw_xml_metadata  # Store the full raw XML
        )
        instance.save()
        logger.info(f"Successfully saved FOMC data for {meeting_date.strftime('%Y-%m-%d')} (Title: {meeting_title}) from textURL: {text_content_url}")


    def extract_all_meeting_data(self, base_list_url: str):
        logger.info(f"Starting FOMC data crawl for 2020s using base URL: {base_list_url}")

        main_page_content = self._fetch_raw_content(base_list_url)
        if not main_page_content:
            return

        main_soup = BeautifulSoup(main_page_content, 'html.parser')
        
        # Using the selector that previously worked from logs: 'li a[href*="/title/"]'
        # And refining to ensure it's within the typical list structure for meetings.
        # The web search results show links like "Meeting, January 28-29, 2020" directly under 2020s
        # These are often in simple <a> tags within a list or div section for that decade.
        # Let's find a container for the 2020s meetings first.
        
        container_2020s = None
        # Try to find a header for "2020s" and then its sibling/parent list.
        # Look for the ul element with data-section attribute "2020s"
        container_2020s = main_soup.find('ul', {'data-section': '2020s'})
        
        if not container_2020s:
            # Fallback: try to find div with data-section "2020s" 
            container_2020s = main_soup.find('div', {'data-section': '2020s'})
            
        if not container_2020s:
            logger.warning("Could not reliably find the container for '2020s' meetings. Falling back to broad search on page.")
            container_2020s = main_soup # Search the whole page
        # print("test html element",container_2020s)
        meeting_link_tags = container_2020s.find_all('li')
        # print("test meeting link tags list",meeting_link_tags)
        meeting_link_tags = [li.find('a', class_='list-item') for li in meeting_link_tags if li.find('a', class_='list-item')]
        # print("test meeting link tags href",meeting_link_tags)
        
        logger.info(f"Found {len(meeting_link_tags)} potential meeting links for the 2020s.")
        if not meeting_link_tags:
            logger.warning(f"Found 0 meeting links. Check selector and page structure. Page snippet:\\n{str(container_2020s)[:1000]}")
            return

        processed_titles = set()
        for link_tag in meeting_link_tags:
            meeting_title = link_tag.get_text(strip=True)
            print("test meeting title",meeting_title)
            meeting_page_relative_url = link_tag.get('href')
            print("test meeting page relative url",meeting_page_relative_url)

            if not meeting_page_relative_url or not meeting_title:
                logger.debug(f"Skipping link with missing title or href. Title: '{meeting_title}', Href: '{meeting_page_relative_url}'")
                continue
            
            # Ensure we are only processing actual meeting links for the 2020s from this specific page
            if not "202" in meeting_title: # Simple check for 2020s
                logger.debug(f"Skipping link '{meeting_title}' as it does not appear to be from the 2020s based on title.")
                continue

            if meeting_title in processed_titles:
                logger.info(f"Title '{meeting_title}' already processed or queued this session. Skipping.")
                continue
            
            if "cancelled" in meeting_title.lower():
                logger.info(f"Skipping cancelled meeting: {meeting_title}")
                continue

            logger.info(f"Processing meeting link: Text='{meeting_title}', Href='{meeting_page_relative_url}'")
            meeting_page_full_url = urljoin("https://fraser.stlouisfed.org", meeting_page_relative_url)
            
            self.extract_single_meeting_data(meeting_page_full_url, meeting_title)
            processed_titles.add(meeting_title)

    def extract(self, link: str, **kwargs) -> None:
        """ Abstract method implementation.
            For this FOMC crawler, prefer using extract_all_meeting_data.
        """
        logger.info(f"FOMCEconomicCrawler.extract called with link: {link}. This crawler is run via extract_all_meeting_data.")
        if "fraser.stlouisfed.org/title/" in link and "/meeting-" in link:
            title_guess = kwargs.get('title', link.split('/')[-1].replace('-', ' ').title())
            logger.info(f"Attempting to process as single meeting: {title_guess}")
            self.extract_single_meeting_data(link, title_guess)
        elif "fraser.stlouisfed.org/title/" in link and "browse=2020s" in link:
            logger.info(f"Attempting to process as 2020s listing page: {link}")
            self.extract_all_meeting_data(link)
        else:
            logger.warning("Direct extract call with this URL is not directly supported. Please provide a 2020s listing page or a specific meeting page URL.")
        pass

if __name__ == "__main__":
    crawler = None
    try:
        crawler = FOMCEconomicCrawler()
        # test_meeting_page_url = "https://fraser.stlouisfed.org/title/federal-open-market-committee-meeting-minutes-transcripts-documents-677/meeting-may-6-7-2025-685851"
        # test_meeting_title = "Meeting, May 6-7, 2025"
        # logger.info(f"--- STARTING UNIT TEST for extract_single_meeting_data ---")
        # logger.info(f"Testing with URL: {test_meeting_page_url}")
        # logger.info(f"Testing with Title: {test_meeting_title}")
        # if crawler.driver: # Only run test if driver initialized
        #     crawler.extract_single_meeting_data(test_meeting_page_url, test_meeting_title)
        # else:
        #     logger.error("SKIPPING extract_single_meeting_data test because WebDriver failed to initialize.")
        # logger.info(f"--- FINISHED UNIT TEST for extract_single_meeting_data ---")

        # --- Full Crawl (currently commented out) ---
        base_url_2020s = "https://fraser.stlouisfed.org/title/federal-open-market-committee-meeting-minutes-transcripts-documents-677?browse=2020s"
        logger.info(f"--- STARTING FULL CRAWL for {base_url_2020s} ---")
        crawler.extract_all_meeting_data(base_list_url=base_url_2020s)
        logger.info(f"--- FINISHED FULL CRAWL for {base_url_2020s} ---")
    except Exception as e:
        logger.error(f"Exception during main execution: {e}", exc_info=True)
    finally:
        if crawler: # Ensure crawler is defined before trying to access driver
            # The __del__ method will handle quitting the driver when the crawler object is garbage collected.
            # For explicit cleanup if not relying on garbage collection timing:
            if hasattr(crawler, 'driver') and crawler.driver:
                 logger.info("Explicitly quitting WebDriver in main finally block.")
                 crawler.driver.quit()
                 crawler.driver = None # Prevent __del__ from trying to quit again

    
