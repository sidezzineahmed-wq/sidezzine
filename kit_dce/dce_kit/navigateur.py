"""Pilote du navigateur standard (Playwright + Chromium) pour le parcours public PMMP observé :
page EntrepriseDemandeTelechargementDce -> formulaire (Nom, Prénom, Adresse électronique, case des conditions générales,
Valider) -> « Télécharger le Dossier ». Deux temps, séparés par la validation HUMAINE des CG :
  1. ouvrir()      : charge la page, vérifie l'association ref/org, lit le texte des CG ; ne remplit RIEN, ne coche RIEN.
  2. telecharger() : recharge la page, vérifie que les CG sont identiques à celles validées, remplit l'identité fournie par
                     l'exploitant, coche la case (sur la validation humaine de CE téléchargement), Valider, puis capture le
                     téléchargement déclenché par CE clic sur CETTE page (jamais un fichier quelconque d'un dossier).
401/403, page de contrôle ou CAPTCHA : arrêt immédiat, aucune nouvelle tentative, aucun contournement.
Champs d'identité : rôle textbox + nom accessible EXACT (title relevé le 05/10/2026), uniques ; aucun repli par position."""
import asyncio
import hashlib
import json
import os
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

from . import cg_texte, confiance


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
    canonique: str = ""            # copie canonique lisible des CG (document HTML, cg_texte) ; vide pour un PDF (empreinte binaire)
    doc_brut_sha256: str = ""      # octets bruts du document lié (information ; hors empreinte quand il est en HTML)
    algo: str = cg_texte.ALGO


def empreinte_cg(texte, lien, doc_sha256=""):
    """Empreinte des CG présentées : libellé de la case + lien + SHA-256 du CONTENU du document lié quand il a pu être lu.
    Sans contenu lu (pas de lien, lien hors portail, lecture impossible), l'empreinte ne couvre que le libellé et le lien :
    un changement du document derrière un lien inchangé ne serait alors PAS détecté (limite affichée, jamais masquée)."""
    norm = re.sub(r"\s+", " ", (texte or "")).strip().lower() + "|" + (lien or "") + "|" + (doc_sha256 or "") + "|" + cg_texte.ALGO
    return hashlib.sha256(norm.encode()).hexdigest()


# Inventaire d'un cadre (exécuté dans la page) : éléments VISIBLES seulement, aucune propriété `value`, textes tronqués.
_JS_INVENTAIRE = r"""() => {
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none"; };
  const t = (s, n) => (s || "").replace(/\s+/g, " ").trim().slice(0, n);
  const lib = e => { const l = [...(e.labels || [])].map(x => t(x.innerText, 80)); const a = e.getAttribute("aria-label"); if (a) l.push("aria:" + t(a, 80));
    const by = e.getAttribute("aria-labelledby"); if (by) by.split(/\s+/).forEach(i => { const x = document.getElementById(i); if (x) l.push("aria-by:" + t(x.innerText, 80)); }); return l; };
  const champs = [...document.querySelectorAll("input,select,textarea")].filter(e => !["hidden", "submit", "button", "reset", "image"].includes(e.type) && vis(e)).slice(0, 80).map(e => ({
    balise: e.tagName.toLowerCase(), type: e.type || "", id: t(e.id, 80), name: t(e.name, 80), placeholder: t(e.getAttribute("placeholder"), 60), title: t(e.getAttribute("title"), 80),
    libelles: lib(e), requis: !!e.required, desactive: !!e.disabled }));
  return {
    titres: [...document.querySelectorAll("h1,h2,h3,legend")].filter(vis).slice(0, 20).map(e => t(e.innerText, 120)),
    libelles: [...document.querySelectorAll("label")].filter(vis).slice(0, 60).map(e => ({ texte: t(e.innerText, 80), pour: t(e.htmlFor, 80) })),
    champs,
    boutons: [...document.querySelectorAll("button,input[type=submit],input[type=button],[role=button]")].filter(vis).slice(0, 30).map(e => t(e.tagName === "INPUT" ? e.getAttribute("value") : (e.innerText || e.getAttribute("aria-label")), 80)),
    liens: [...document.querySelectorAll("a")].filter(vis).map(e => t(e.innerText, 80)).filter(Boolean).slice(0, 60),
    formulaires: document.forms.length, cadres_internes: document.querySelectorAll("iframe,frame").length,
    champs_caches: document.querySelectorAll("input[type=hidden]").length };
}"""

CHAMPS_IDENTITE = ("Nom", "Prénom", "Adresse électronique")   # noms accessibles EXACTS (attribut title relevé sur PMMP)

def _n(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


MARQUEURS_CONTROLE = re.compile(r"captcha|recaptcha|hcaptcha|cf-challenge|vérification de sécurité|requête a été bloquée", re.I)


class NavigateurPlaywright:
    def __init__(self, config, headless=True):
        self.c, self.headless, self._pw, self._b = config, headless, None, None

    async def _demarrer(self):
        if self._b:
            return
        from playwright.async_api import async_playwright
        kw = {"headless": self.headless}   # jamais d'option d'ignorance d'erreur TLS
        if self.c.chromium:
            kw["executable_path"] = self.c.chromium
        self._home = None
        if self.c.confiance_navigateur == "proxy_ccr":
            try:
                self._home = confiance.preparer_magasin(self.c.racine_travail, confiance.verifier_ca())
            except confiance.ErreurConfiance as e:
                raise Refus("confiance", str(e)) from None
            kw["env"] = {**os.environ, "HOME": self._home}
        try:
            self._pw = await async_playwright().start()
            self._b = await self._pw.chromium.launch(**kw)
        except BaseException:
            await self.fermer()
            raise

    async def fermer(self):
        try:
            if self._b:
                await self._b.close()
        finally:
            try:
                if self._pw:
                    await self._pw.stop()
            finally:
                self._b = self._pw = None
                confiance.nettoyer(getattr(self, "_home", None))
                self._home = None

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
        self._http = rep.status
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

    async def _champ(self, page, nom):
        """Champ d'identité : zone de texte dont le NOM ACCESSIBLE est exactement `nom`, unique sur la page. Sur PMMP (relevé du
        05/10/2026), <label for="nom"> ne vise pas l'id préfixé PRADO : le nom accessible vient de l'attribut title exact."""
        loc = page.get_by_role("textbox", name=nom, exact=True)
        n = await loc.count()
        if n != 1:
            raise Refus("formulaire", f"champ « {nom} » " + ("introuvable" if n == 0 else f"ambigu ({n} champs)"))
        return loc

    async def _preuves(self, page, ref):
        """Diagnostic d'un formulaire non reconnu, SANS aucune valeur : titre, chemin et seuls paramètres publics (page,
        refConsultation, orgAcronyme), statut HTTP, et pour chaque cadre les métadonnées des champs/libellés/titres/boutons/liens
        VISIBLES. Ni HTML, ni capture, ni valeur de champ, ni cookie. Écrit sous la racine de travail ; n'échoue jamais."""
        if not self.c.racine_travail:
            return None
        try:
            def chemin(u):
                p = urlparse(u)
                q = parse_qs(p.query)
                return {"hote": p.hostname, "chemin": p.path, **{k: q[k][0] for k in ("page", "refConsultation", "orgAcronyme") if k in q}}
            cadres = []
            for f in page.frames:
                try:
                    d = await f.evaluate(_JS_INVENTAIRE)
                except Exception as x:
                    d = {"erreur": type(x).__name__}
                cadres.append({"principal": f == page.main_frame, **chemin(f.url), **d})
            r = {"ref": ref, "http": getattr(self, "_http", None), "titre": (await page.title())[:200], **chemin(page.url), "cadres": cadres}
            os.makedirs(self.c.racine_travail, exist_ok=True)
            p = os.path.join(self.c.racine_travail, f"preuves_formulaire_{re.sub(r'[^A-Za-z0-9_-]', '_', ref)}.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(r, fh, ensure_ascii=False, indent=1)
            return p
        except Exception:
            return None

    def _preuves_cg(self, ref, validee, lue, texte, lien, detail, cg_validee):
        """CG différentes de celles validées : différences ligne à ligne entre la copie canonique VALIDÉE et celle LUE, pour
        décision HUMAINE (rien n'est ignoré ni revalidé ici). Texte public de la section des conditions seulement."""
        if not self.c.racine_travail:
            return None
        try:
            cg_validee = cg_validee or {}
            avant, apres = cg_validee.get("canonique"), detail.get("canonique")
            r = {"ref": ref, "algo": cg_texte.ALGO, "algo_validation": cg_validee.get("algo"), "empreinte_validee": validee, "empreinte_lue": lue,
                 "libelle_lu": texte.strip()[:400], "libelle_identique": cg_validee.get("texte") is None or _n(cg_validee.get("texte")) == _n(texte),
                 "lien_lu": lien, "lien_identique": cg_validee.get("lien") is None or cg_validee.get("lien") == lien,
                 "document": "html" if apres is not None else "binaire", "doc_brut_sha256": detail.get("brut"),
                 "doc_identique": (avant == apres) if (avant is not None and apres is not None) else None,
                 "differences": cg_texte.differences(avant, apres) if (avant is not None and apres is not None) else
                 ["comparaison ligne à ligne impossible : copie canonique validée absente (validation antérieure à " + cg_texte.ALGO + " ou document binaire)"]}
            os.makedirs(self.c.racine_travail, exist_ok=True)
            p = os.path.join(self.c.racine_travail, f"preuves_cg_{re.sub(r'[^A-Za-z0-9_-]', '_', ref)}.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(r, fh, ensure_ascii=False, indent=1)
            return p
        except Exception:
            return None

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
        doc_sha, portee, detail = "", "libellé seul : aucun document de conditions lié sur la page", {}
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
                    typ = (r.headers.get("content-type") or "").lower()
                    if r.ok and corps and "html" in typ:
                        # page HTML (PRADO) : copie canonique de la section unique #main-part (cg_texte), jamais les octets bruts
                        try:
                            canon = cg_texte.canonique(cg_texte.decoder(corps, r.headers.get("content-type") or ""))
                        except cg_texte.ExtractionRefusee as x:
                            raise Refus("cg_extraction", f"conditions générales illisibles de façon sûre : {x} ; rien n'est validable") from None
                        doc_sha = cg_texte.empreinte(canon)
                        portee = (f"libellé et texte intégral de la section des conditions #main-part ({len(canon.splitlines())} lignes "
                                  f"canoniques, algorithme {cg_texte.ALGO} ; scripts, styles, attributs et valeurs de champs exclus)")
                        detail = {"canonique": canon, "brut": hashlib.sha256(corps).hexdigest()}
                    elif r.ok and corps:
                        doc_sha, portee = hashlib.sha256(corps).hexdigest(), f"libellé et contenu binaire complet du document lié ({len(corps)} octets)"
                        detail = {"brut": doc_sha}
                    else:
                        portee = f"libellé et lien seulement : document non lu (HTTP {r.status})"
                except Refus:
                    raise
                except Exception as e:
                    portee = f"libellé et lien seulement : document non lu ({str(e)[:80]})"
        return case, texte, lien, doc_sha, portee, detail

    async def ouvrir(self, ref, org, reference_attendue=None):
        await self._demarrer()
        ctx = await self._b.new_context(accept_downloads=True, locale="fr-FR")
        try:
            page = await self._charger(ctx, ref, org, reference_attendue)
            for lib in CHAMPS_IDENTITE:
                try:
                    await self._champ(page, lib)
                except Refus as e:
                    e.preuves = await self._preuves(page, ref)
                    raise
            _, texte, lien, doc_sha, portee, detail = await self._cg(page)
            return InfoCG(url=page.url, texte=texte.strip(), empreinte=empreinte_cg(texte, lien, doc_sha), lien_cg=lien, reference_vue=True, portee=portee,
                          doc_sha256=doc_sha, canonique=detail.get("canonique", ""), doc_brut_sha256=detail.get("brut", ""))
        finally:
            await ctx.close()

    async def telecharger(self, ref, org, identite, empreinte_validee, reference_attendue=None, cg_validee=None):
        await self._demarrer()
        ctx = await self._b.new_context(accept_downloads=True, locale="fr-FR")
        try:
            page = await self._charger(ctx, ref, org, reference_attendue)
            case, texte, lien, doc_sha, _, detail = await self._cg(page)
            lue = empreinte_cg(texte, lien, doc_sha)
            if lue != empreinte_validee:
                e = Refus("cg_modifiees", "les conditions générales affichées diffèrent de celles validées : nouvelle validation humaine requise")
                e.preuves = self._preuves_cg(ref, empreinte_validee, lue, texte, lien, detail, cg_validee)
                raise e
            for lib, val in zip(CHAMPS_IDENTITE, (identite.nom, identite.prenom, identite.email)):
                await (await self._champ(page, lib)).fill(val)
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
