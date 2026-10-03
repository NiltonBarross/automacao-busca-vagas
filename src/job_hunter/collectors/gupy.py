import time
from urllib.parse import quote
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError
from job_hunter.domain.models import fold
from job_hunter.normalization.gupy import parse_cards, parse_detail


class CollectionError(RuntimeError):
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


class StopCollection(Exception):
    def __init__(self, status):
        self.status = status


class GupyCollector:
    def __init__(self, config, cancel, progress):
        self.config, self.cancel, self.progress = config, cancel, progress
        self.deadline = time.monotonic() + config.max_seconds
        self.engine = self.browser = None

    def check(self):
        if self.cancel.is_set():
            raise StopCollection("cancelled")
        if time.monotonic() >= self.deadline:
            raise StopCollection("limited")

    def timeout(self):
        self.check()
        return max(1, min(30000, int((self.deadline - time.monotonic()) * 1000)))

    def __enter__(self):
        try:
            self.engine = sync_playwright().start()
            self.browser = self.engine.chromium.launch(headless=True, timeout=self.timeout())
            self.listing = self.browser.new_page()
            self.detail = self.browser.new_page()
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        try:
            if self.browser:
                self.browser.close()
        finally:
            if self.engine:
                self.engine.stop()

    def navigate(self, page, url):
        for attempt in range(2):
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=self.timeout())
                status = response.status if response else 0
                if status in [401, 403, 429]:
                    raise CollectionError("bloqueio", f"Acesso recusado pela plataforma (HTTP {status}).")
                if status >= 500:
                    if attempt == 0:
                        self.cancel.wait(min(1, max(0, self.deadline - time.monotonic())))
                        continue
                    raise CollectionError("rede", f"Serviço indisponível (HTTP {status}).")
                if status >= 400 or not status:
                    raise CollectionError("anúncio indisponível", f"Página indisponível (HTTP {status}).")
                self.check_block(page)
                return
            except (PlaywrightTimeout, PlaywrightError) as exc:
                self.check()
                if attempt == 1:
                    raise CollectionError("rede", str(exc).splitlines()[0]) from exc
                self.cancel.wait(min(1, max(0, self.deadline - time.monotonic())))

    def check_block(self, page):
        title = fold(page.title())
        if any(s in title for s in ["access denied", "just a moment", "captcha", "forbidden"]):
            raise CollectionError("bloqueio", "A plataforma apresentou um controle de acesso.")

    def jobs(self, term, cache):
        self.navigate(self.listing, "https://portal.gupy.io/job-search/term=" + quote(term, safe=""))
        signatures = set()
        for page_number in range(1, self.config.max_pages + 1):
            self.check()
            try:
                self.listing.wait_for_function("""() => [...document.querySelectorAll('a h3')].length > 0 ||
                    /0 resultados|nenhuma vaga|não encontramos vagas|nenhum resultado/i.test(document.body.innerText)""", timeout=self.timeout())
            except PlaywrightTimeout as exc:
                self.check()
                self.check_block(self.listing)
                raise CollectionError("mudança de estrutura", "Lista e estado vazio não reconhecidos no portal.") from exc
            cards = parse_cards(self.listing.content())
            self.progress("page", f"Página {page_number}: {term}")
            if not cards:
                body = fold(self.listing.locator("body").inner_text(timeout=self.timeout()))
                if any(x in body for x in ["0 resultados", "nenhuma vaga", "nao encontramos vagas", "nenhum resultado"]):
                    self.progress("empty", f"Sem resultados para {term}")
                    return
                raise CollectionError("extração incompleta", "Cartões encontrados, mas links não reconhecidos.")
            signature = tuple(sorted(c.key for c in cards))
            if signature in signatures:
                raise CollectionError("paginação repetida", "Página repetida; coleta do termo interrompida.")
            signatures.add(signature)
            for card in cards:
                self.check()
                if card.key in cache:
                    self.progress("duplicate", card.title)
                    yield cache[card.key]
                    continue
                if len(cache) >= self.config.max_jobs:
                    raise StopCollection("limited")
                self.progress("detail", f"Lendo anúncio: {card.title}")
                try:
                    self.navigate(self.detail, card.url)
                    self.detail.locator('h1').first.wait_for(timeout=self.timeout())
                    job = parse_detail(self.detail.content(), card)
                    if job.extraction == "incompleta":
                        self.progress("error", {"kind": "extração incompleta", "message": f"Descrição incompleta: {card.url}"})
                except CollectionError as exc:
                    if exc.kind == "bloqueio":
                        raise
                    self.progress("error", {"kind": exc.kind, "message": f"{card.url}: {exc}"})
                    job = card
                except (PlaywrightTimeout, PlaywrightError) as exc:
                    self.check()
                    self.progress("error", {"kind": "extração incompleta", "message": f"{card.url}: {str(exc).splitlines()[0]}"})
                    job = card
                cache[job.key] = job
                yield job
            next_button = self.listing.locator('button[aria-label*="róxima"], button[aria-label*="next"], button[aria-label*="Next"]').first
            if not next_button.count() or not next_button.is_enabled():
                return
            if page_number == self.config.max_pages:
                self.progress("page_limit", f"Limite de páginas atingido para {term}")
                return
            old = self.listing.locator("a").filter(has=self.listing.locator("h3")).evaluate_all("els => els.map(e => e.href).sort().join('|')")
            next_button.click(timeout=self.timeout())
            try:
                self.listing.wait_for_function("old => [...document.querySelectorAll('a')].filter(e=>e.querySelector('h3')).map(e=>e.href).sort().join('|') !== old", arg=old, timeout=self.timeout())
            except PlaywrightTimeout as exc:
                self.check()
                raise CollectionError("paginação repetida", "Botão próxima não avançou os resultados.") from exc
