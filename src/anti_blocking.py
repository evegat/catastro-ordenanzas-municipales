"""
Módulo de Seguridad Operacional y Polite Crawling para el Catastro Municipal P090.
Implementa rate limiting adaptativo, rotación de encabezados de navegador real y reintentos con backoff.
"""

import time
import random
import logging
import requests
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AntiBlocking")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

class PoliteSession:
    def __init__(self, min_delay: float = 1.5, max_delay: float = 3.5, max_retries: int = 4):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.last_request_time: Dict[str, float] = {}
        self.total_requests = 0
        self.blocked_count = 0

    def _get_domain(self, url: str) -> str:
        from urllib.parse import urlparse
        return urlparse(url).netloc

    def _apply_rate_limit(self, domain: str):
        now = time.time()
        last = self.last_request_time.get(domain, 0.0)
        elapsed = now - last
        delay = random.uniform(self.min_delay, self.max_delay)
        
        if elapsed < delay:
            sleep_time = delay - elapsed
            time.sleep(sleep_time)
            
        self.last_request_time[domain] = time.time()

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> Optional[requests.Response]:
        domain = self._get_domain(url)
        
        default_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,image/webp,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }
        if headers:
            default_headers.update(headers)

        retries = 0
        backoff = 5.0

        while retries <= self.max_retries:
            self._apply_rate_limit(domain)
            try:
                self.total_requests += 1
                resp = self.session.get(url, headers=default_headers, timeout=kwargs.get("timeout", 20), **kwargs)
                
                # Check for rate limiting / temporary server block
                if resp.status_code in [429, 503]:
                    self.blocked_count += 1
                    logger.warning(f"Servidor respondió con código {resp.status_code} para {domain}. Entrando en backoff de {backoff}s...")
                    time.sleep(backoff)
                    backoff *= 2.0
                    retries += 1
                    continue
                
                return resp
            except (requests.RequestException, Exception) as e:
                logger.warning(f"Error al conectar con {url}: {e}. Reintentando ({retries+1}/{self.max_retries})...")
                time.sleep(backoff)
                backoff *= 2.0
                retries += 1

        logger.error(f"Fallo definitivo al consultar {url} después de {self.max_retries} intentos.")
        return None
