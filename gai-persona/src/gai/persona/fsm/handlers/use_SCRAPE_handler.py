import logging,os
from gai.lib.tools.scraper import Scraper
from gai.lib.common.file_utils import split_text
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)

class use_SCRAPE_handler:

    def handle_SCRAPE(self, urls:list,chunk_size=1000, chunk_overlap=100):
        chunk_dirs = []
        for url in urls:
            try:
                html, links = Scraper().scrape(url)
                chunk_dir = split_text(text=html,sub_dir=None, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                with open(os.path.join(chunk_dir,"preview.txt"),'w') as f:
                    preview=html[:2000]
                    f.write(preview)
                chunk_dirs.append(chunk_dir)
                logger.info(f"on_SCRAPE_handler: scraped {url}")
            except:
                logger.warning(f"on_SCRAPE_handler: scraped {url} error")
        return chunk_dirs



