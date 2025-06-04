from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from aws_lambda_powertools import Logger
from core.db.documents import InvestopediaDocument
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers.html2text import Html2TextTransformer

from .base import BaseCrawler

logger = Logger(service="llm-twin-course/crawler")


class InvestopediaTermsCrawler(BaseCrawler):
    model = InvestopediaDocument
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }

    def __init__(self) -> None:
        super().__init__()

    def extract(self, link: str, **kwargs) -> None:
        """
        Extract a single Investopedia term page and store as InvestopediaDocument.
        """
        old_model = self.model.find(url=link)
        if old_model is not None:
            logger.info(f"Article already exists in the database: {link}")
            return

        logger.info(f"Starting scrapping article: {link}")
        try:
            resp = requests.get(link, headers=self.HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            term = soup.find('h1', class_='comp article-heading mntl-text-block').get_text(strip=True) if soup.find('h1', class_='comp article-heading mntl-text-block') else ''
            
            definition_tag = soup.find('p', id=lambda x: x and x.startswith('mntl-sc-block_1-0-') and not soup.find('p', id=lambda y: y and y.startswith('mntl-sc-block_1-0-') and y < x))
            if not definition_tag:
                 definition_tag = soup.find('div', class_=lambda c: c and 'article-content' in c).find('p')

            definition = definition_tag.get_text(strip=True) if definition_tag else ''

            content_title = term 
            sections = []
            content_body = soup.find('div', id=lambda x: x and x.startswith('mntl-sc-page_1-0'))
            if content_body:
                for section_tag in content_body.find_all(['h2','h3'], class_=lambda x: x and x.startswith('mntl-sc-block-heading_1-0')):
                    heading = section_tag.get_text(strip=True)
                    texts = []
                    sib = section_tag.find_next_sibling()
                    # Collect paragraph texts
                    while sib and sib.name == 'p' and sib.get('id', '').startswith('mntl-sc-block_1-0'):
                        texts.append(sib.get_text(strip=True))
                        sib = sib.find_next_sibling()
                    
                    # Check for lists if no paragraph text was found or if a list is the immediate next relevant content
                    if not texts and sib and sib.name == 'ul' and sib.get('id','').startswith('mntl-sc-block_1-0'):
                        list_items = [li.get_text(strip=True) for li in sib.find_all('li')]
                        if list_items:
                             sections.append({'heading': heading, 'list': list_items})
                    elif texts: # Only add if we found paragraph text
                        sections.append({'heading': heading, 'text': ' '.join(texts)})

                # Fallback if no structured sections were found but a content body exists
                if not sections and content_body:
                    logger.warning(f"Structured sections not found for {link}. Falling back to full text of content body.")
                    # Get all text from content_body, trying to maintain some paragraph separation
                    full_text_parts = []
                    for element in content_body.find_all(['p', 'ul', 'h2', 'h3'], recursive=False): # Process direct children
                        if element.name in ['h2', 'h3'] and element.get_text(strip=True) == term: # Avoid recapturing main title
                            continue
                        if element.name == 'ul':
                            list_text = "\\n".join([f"- {li.get_text(strip=True)}" for li in element.find_all('li')])
                            if list_text:
                                full_text_parts.append(list_text)
                        else:
                            paragraph_text = element.get_text(strip=True)
                            if paragraph_text:
                                full_text_parts.append(paragraph_text)
                    
                    if full_text_parts:
                        sections = [{'heading': 'Full Article Content', 'text': '\\n\\n'.join(full_text_parts)}]
                    elif content_body.get_text(strip=True): # Simpler fallback if the above is too complex or yields nothing
                         sections = [{'heading': 'Full Article Content', 'text': content_body.get_text(separator='\\n', strip=True)}]

            content = {'title': content_title, 'sections': sections}
            
            metadata_div = soup.find('div', class_='mntl-byline__group')
            author = None
            last_updated = None
            if metadata_div:
                author_tag = metadata_div.find('a', class_='mntl-byline__author-name')
                if author_tag:
                    author = author_tag.get_text(strip=True)
                
                date_tag = metadata_div.find('div', class_='mntl-byline__date')
                if date_tag:
                    last_updated_text = date_tag.get_text(strip=True).replace('Updated', '').strip()
                    try:
                        dt_object = datetime.strptime(last_updated_text, '%B %d, %Y')
                        last_updated = dt_object.isoformat()
                    except ValueError:
                        logger.warning(f"Could not parse date: {last_updated_text} for {link}")
                        last_updated = last_updated_text

            metadata = {
                'source': 'Investopedia',
                'author': author,
                'last_updated': last_updated,
                'platform': urlparse(link).netloc,
                'tags': [tag.get_text(strip=True) for tag in soup.select('div.mntl-tags__list a')]
            }
            
            instance = self.model(
                term=term,
                url=link,
                definition=definition,
                content=content,
                metadata=metadata
            )
            instance.save()
            logger.info(f"Successfully scraped and saved: {link}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {link}: {e}")
        except Exception as e:
            logger.error(f"Failed to extract {link}: {e}", exc_info=True)

    def extract_all_terms(self, dictionary_url: str, **kwargs):
        """
        Crawl the Investopedia dictionary page, extract all term links, and process each.
        """
        logger.info(f"Fetching all term links from: {dictionary_url}")
        try:
            resp = requests.get(dictionary_url, headers=self.HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            term_links = set()
            link_elements = soup.select('ul.dictionary-top24-list__list li a[href*="/terms/"]') 
            if not link_elements:
                link_elements = soup.select('a[href*="/terms/"]')

            for a_tag in link_elements:
                href = a_tag.get('href')
                if href:
                    full_url = urljoin(dictionary_url, href)
                    if "/terms/" in full_url and full_url.endswith(".asp"):
                        term_links.add(full_url)
            
            logger.info(f"Found {len(term_links)} term links.")
            if not term_links:
                logger.warning(f"No term links found on {dictionary_url}. Check selectors or page structure.")

            for i, link in enumerate(term_links):
                logger.info(f"Processing link {i+1}/{len(term_links)}: {link}")
                try:
                    self.extract(link, **kwargs)
                except Exception as e:
                    logger.error(f"Failed to process link {link}: {e}", exc_info=True)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Could not fetch dictionary page {dictionary_url}: {e}")
        except Exception as e:
            logger.error(f"An error occurred during extract_all_terms: {e}", exc_info=True)

# Optional: main entry point for running as a script
if __name__ == "__main__":
    crawler = InvestopediaTermsCrawler()
    dictionary_url = "https://www.investopedia.com/financial-term-dictionary-4769738?utm_source=chatgpt.com"
    crawler.extract_all_terms(dictionary_url)
