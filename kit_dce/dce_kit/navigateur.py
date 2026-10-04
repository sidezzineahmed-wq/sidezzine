"""Pilote du navigateur standard (Playwright + Chromium) pour le parcours public PMMP observé :
page EntrepriseDemandeTelechargementDce -> formulaire (Nom, Prénom, Adresse électronique, case des conditions générales,
Valider) -> « Télécharger le Dossier ». Deux temps, séparés par la validation HUMAINE des CG :
  1. ouvrir()      : charge la page, vérifie l'association ref/org, lit le texte des CG ; ne remplit RIEN, ne coche RIEN.
  2. telecharger() : recharge la page, vérifie que les CG sont identiques à celles validées, remplit l'identité fournie par
                     l'exploitant, coche la case (sur la validation humaine de CE téléchargement), Valider, puis capture le
                     téléchargement déclenché par CE clic sur CETTE page (jamais un fichier quelconque d'un dossier).
401/403, page de contrôle ou CAPTCHA : arrêt immédiat, aucune nouvelle tentative, aucun contournement.
Les sélecteurs suivent les libellés visibles observés ; ils sont à confirmer au premier essai réel autorisé."""
import asyncio
import hashlib
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse


class Refus(RuntimeError):
    def __init__(self, code, motif):
        super().__init__(motif)
        self.code, self.motif = code, motif


@dataclass
class InfoCG:
    url: str
    texte: str
    empreinte: str
    lien_cg: str
    reference_vue: bool
    portee: str = "libellé seul"
    doc_sha256: str = ""


def empreinte_cg(texte, lien, doc_sha256=""):
    """Empreinte des CG présentées : libellé de la case + lien + SHA-256 du CONTENU du document lié quand il a pu être lu.
    Sans contenu lu (pas de lien, lien hors portail, lecture impossible), l'empreinte ne couvre que le libellé et le lien :
    un changement du document derrière un lien inchangé ne serait alors PAS détecté (limite affichée, jamais masquée)."""
    norm = re.sub(r"\s+", " ", (texte or "")).strip().lower() + "|" + (lien or "") + "|" + (doc_sha256 or "")
    return hashlib.sha256(norm.encode()).hexdigest()


MARQUEURS_CONTROLE = re.compile(r"captcha|recaptcha|hcaptcha|cf-challenge|vérification de sécurité|requête a été bloquée", re.I)


class NavigateurPlaywright:
    def __init__(self, config, headless=True):
        self.c, self.headless, self._pw, self._b = config, headless, None, None

    async def _demarrer(self):
        if self._b:
            return
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().start()
        kw = {"headless": self.headless}
        if self.c.chromium:
            kw["executable_path"] = self.c.chromium
        self._b = await self._pw.chromium.launch(**kw)

    async def fermer(self):
        if self._b:
            await self._b.close()
            await self._pw.stop()
            self._b = self._pw = None

    def url_demande(self, ref, org):
        return f"{self.c.base_url}?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation={ref}&orgAcronyme={org}"

    async def _charger(self, ctx, ref, org, reference_attendue):
        page = await ctx.new_page()
        rep = await page.goto(self.url_demande(ref, org), timeout=self.c.delai_page_s * 1000)
        if rep is None:
            raise Refus("reseau", "aucune réponse du portail")
        if rep.status in (401, 403):
            raise Refus(f"http_{rep.status}", f"HTTP {rep.status} : arrêt, aucun contournement")
        if rep.status != 200:
            raise Refus(f"http_{rep.status}", f"HTTP {rep.status}")
        u = urlparse(page.url)
        q = parse_qs(u.query)
        if u.hostname != urlparse(self.c.base_url).hostname or q.get("refConsultation") != [ref] or q.get("orgAcronyme") != [org]:
            raise Refus("association", f"page inattendue ({page.url}) : association ref/org non garantie")
        corps = await page.content()
        if MARQUEURS_CONTROLE.search(corps):
            raise Refus("controle", "page de contrôle ou CAPTCHA : arrêt, aucun contournement")
        vue = True
        if reference_attendue:
            vue = reference_attendue.replace(" ", "").lower() in re.sub(r"\s+", "", await page.inner_text("body")).lower()
            if not vue:
                raise Refus("association", f"la référence {reference_attendue} n'apparaît pas sur la page : rien n'est téléchargé")
        return page

    async def _cg(self, page):
        case = page.get_by_role("checkbox", name=re.compile(r"condition", re.I))
        if await case.count() != 1:
            raise Refus("formulaire", "case des conditions générales introuvable ou ambiguë")
        lid = await case.get_attribute("id")
        lab = page.locator(f"label[for='{lid}']") if lid else case.locator("xpath=ancestor::label[1]")
        texte = (await lab.inner_text()) if await lab.count() else ""
        lien = ""
        a = page.locator("a", has_text=re.compile(r"condition", re.I))
        if await a.count():
            lien = (await a.first.get_attribute("href")) or ""
        doc_sha, portee = "", "libellé seul : aucun document de conditions lié sur la page"
        if lien:
            absolu = urljoin(page.url, lien)
            if urlparse(absolu).hostname != urlparse(self.c.base_url).hostname:
                portee = "libellé et lien seulement : document hors du portail, contenu non vérifié"
            else:
                try:
                    r = await page.request.get(absolu, timeout=self.c.delai_page_s * 1000)
                    if r.status in (401, 403):
                        raise Refus(f"http_{r.status}", f"HTTP {r.status} sur le document des conditions : arrêt")
                    corps = await r.body()
                    if r.ok and corps:
                        doc_sha, portee = hashlib.sha256(corps).hexdigest(), f"libellé et contenu complet du document lié ({len(corps)} octets)"
                    else:
                        portee = f"libellé et lien seulement : document non lu (HTTP {r.status})"
                except Refus:
                    raise
                except Exception as e:
                    portee = f"libellé et lien seulement : document non lu ({str(e)[:80]})"
        return case, texte, lien, doc_sha, portee

    async def ouvrir(self, ref, org, reference_attendue=None):
        await self._demarrer()
        ctx = await self._b.new_context(accept_downloads=True, locale="fr-FR")
        try:
            page = await self._charger(ctx, ref, org, reference_attendue)
            for lib in ("Nom", "Prénom", "Adresse électronique"):
                if await page.get_by_label(re.compile(rf"^\s*{lib}\b", re.I)).count() < 1:
                    raise Refus("formulaire", f"champ « {lib} » introuvable")
            _, texte, lien, doc_sha, portee = await self._cg(page)
            return InfoCG(url=page.url, texte=texte.strip(), empreinte=empreinte_cg(texte, lien, doc_sha), lien_cg=lien, reference_vue=True, portee=portee, doc_sha256=doc_sha)
        finally:
            await ctx.close()

    async def telecharger(self, ref, org, identite, empreinte_validee, reference_attendue=None):
        await self._demarrer()
        ctx = await self._b.new_context(accept_downloads=True, locale="fr-FR")
        try:
            page = await self._charger(ctx, ref, org, reference_attendue)
            case, texte, lien, doc_sha, _ = await self._cg(page)
            if empreinte_cg(texte, lien, doc_sha) != empreinte_validee:
                raise Refus("cg_modifiees", "les conditions générales affichées diffèrent de celles validées : nouvelle validation humaine requise")
            await page.get_by_label(re.compile(r"^\s*Nom\b", re.I)).first.fill(identite.nom)
            await page.get_by_label(re.compile(r"^\s*Prénom\b", re.I)).first.fill(identite.prenom)
            await page.get_by_label(re.compile(r"^\s*Adresse électronique\b", re.I)).first.fill(identite.email)
            await case.check()
            await page.get_by_role("button", name=re.compile(r"^\s*Valider\s*$", re.I)).click()
            await page.wait_for_load_state("domcontentloaded")
            if MARQUEURS_CONTROLE.search(await page.content()):
                raise Refus("controle", "page de contrôle ou CAPTCHA après validation : arrêt")
            lien_dl = page.get_by_role("link", name=re.compile(r"Télécharger le Dossier", re.I))
            if await lien_dl.count() < 1:
                raise Refus("formulaire", "lien « Télécharger le Dossier » introuvable après validation")
            try:
                async with page.expect_download(timeout=self.c.delai_debut_telechargement_s * 1000) as att:
                    await lien_dl.first.click()
                dl = await att.value
            except Exception as e:
                if "Timeout" in type(e).__name__ or "timeout" in str(e).lower():
                    raise Refus("delai_telechargement", f"le téléchargement n'a pas commencé en {self.c.delai_debut_telechargement_s} s")
                raise
            if urlparse(dl.url).hostname != urlparse(self.c.base_url).hostname:
                raise Refus("association", f"téléchargement venu d'un autre hôte ({dl.url})")
            try:
                chemin = await asyncio.wait_for(dl.path(), timeout=self.c.delai_fin_transfert_s)
            except asyncio.TimeoutError:
                await dl.cancel()
                raise Refus("delai_telechargement", f"transfert non terminé en {self.c.delai_fin_transfert_s} s : archive ignorée")
            echec = await dl.failure()
            if echec:
                raise Refus("telechargement", f"transfert interrompu : {echec}")
            octets = open(chemin, "rb").read()
            return octets, dl.suggested_filename, dl.url
        finally:
            await ctx.close()
