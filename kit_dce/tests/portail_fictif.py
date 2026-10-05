"""Portail FICTIF local reproduisant le parcours public observé (aucun accès PMMP) : formulaire Nom / Prénom / Adresse
électronique / coordonnées facultatives / case des CG / Valider, puis « Télécharger le Dossier ». Modes de test par référence."""
import io
import json
import threading
import time
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"


def zip_fictif(date_time=None):
    """Archive du portail FICTIF. Sans date_time, chaque entrée porte l'heure courante (résolution ZIP : 2 s) : comme un vrai
    portail, deux téléchargements du même dossier donnent des octets différents pour un même contenu. Un test qui veut le SHA
    de l'archive téléchargée doit donc le prendre sur les octets SERVIS (Etat.zips_servis), jamais sur une archive régénérée."""
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        def ecrire(nom, contenu):
            if date_time is None:
                z.writestr(nom, contenu)
            else:
                z.writestr(zipfile.ZipInfo(nom, date_time=date_time), contenu, compress_type=zipfile.ZIP_DEFLATED)
        ecrire("DCE/", "")
        for n in ("RC.pdf", "CPS.pdf", "AVIS EN FR.pdf"):
            ecrire("DCE/" + n, PDF + n.encode())
        ecrire("DCE/BPDE.docx", _docx())
    return b.getvalue()


def _docx():
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        for n, c in (("[Content_Types].xml", "<Types/>"), ("word/document.xml", "<w:document/>")):
            z.writestr(zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0)), c)  # DOCX stable ; l'archive extérieure, elle, est régénérée
    return b.getvalue()


class Etat:
    def __init__(self):
        self.soumis, self.cg_texte, self.telechargements, self.vues = [], ("Je reconnais avoir pris connaissance des conditions générales de cette plate-forme "
                                                                         "de dématérialisation et je les accepte."), [], []
        self.cg_doc, self.lien_cg, self.lenteur_s = b"%PDF-1.4 Conditions generales fictives v1 %%EOF", "/cgu.pdf", 0
        self.zip_date, self.zips_servis = None, []
        # page HTML des conditions (type PRADO) : texte contractuel + parties techniques qui changent à CHAQUE requête
        self.cg_paragraphes = ["Article 1 - Objet : les présentes conditions régissent l'usage de la plate-forme fictive.",
                               "Article 2 - Responsabilité : l'utilisateur est responsable des informations saisies."]
        self.cg_clause_repliee = "Article 3 - Clause repliée : les données de connexion sont conservées un an."
        self.cg_prerequis = "Navigateur récent avec JavaScript activé."
        self.cg_bandeau = ""            # bandeau date/heure HORS #main-part (vide : heure courante, change à chaque requête)
        self.cg_main_part_html = None   # remplace toute la section (tests de structure absente ou ambiguë)
        self.cg_html_vues = 0   # date fixe des entrées (None : heure courante) ; archives réellement servies


def construire(etat):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _env(self, code, corps, typ="text/html; charset=utf-8", extra=None):
            b = corps if isinstance(corps, bytes) else corps.encode()
            self.send_response(code)
            self.send_header("Content-Type", typ)
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def _form(self, ref, org, err=""):
            # Fidèle au relevé PMMP du 05/10/2026 : <label for="nom"> ne vise PAS l'id préfixé PRADO (input.labels vide) ;
            # le nom accessible des zones de texte vient de leur attribut title exact. La case des CG a un <label for> valide.
            P, I = "ctl0$CONTENU_PAGE$EntrepriseFormulaireDemande", "ctl0_CONTENU_PAGE_EntrepriseFormulaireDemande"
            champs = [("nom", "Nom"), ("prenom", "Prénom"), ("email", "Adresse électronique"), ("telephone", "Téléphone")]
            if ref == "RAMBIGU":
                champs.append(("nom2", "Nom"))
            return f"""<!doctype html><html><head><title>Téléchargement du DCE</title></head><body>
            <h1>Téléchargement du dossier de consultation</h1><p>Référence : {'00/2099/FICTIF' if ref != 'RAUTRE' else '99/2099/XX'}</p>{err}
            <form method="post" action="/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation={ref}&orgAcronyme={org}">
            {''.join(f'<label for="{c}"> {l.upper()} </label><input name="{P}${c}" type="text" id="{I}_{c}" title="{l}">' for c, l in champs)}
            <input type="checkbox" name="{P}$accepterConditions" id="{I}_accepterConditions" title="J'accepte les conditions générales d'utilisation"><label for="{I}_accepterConditions">{etat.cg_texte}</label> {f'<a href="{etat.lien_cg}">conditions générales</a>' if etat.lien_cg else ''}
            <button type="submit">Valider</button></form></body></html>"""

        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            etat.vues.append(self.path)
            if u.path == "/cgu.html":
                # structure du relevé DOM officiel : bandeau date/heure HORS section ; section unique div#main-part.main-part avec
                # rubriques rubrique_1 (Conditions d'utilisation) et rubrique_2 (Pré-requis techniques) ; parties techniques qui
                # changent à CHAQUE requête (état PRADO, attributs et liens de session, scripts, commentaires, titre)
                etat.cg_html_vues += 1
                n, t = etat.cg_html_vues, time.time()
                sections = etat.cg_main_part_html if etat.cg_main_part_html is not None else (
                    f"""<div id="main-part" class="main-part" data-rendu="{t}"><script>var nonce="{n}-{t}";</script><style>.x{{margin:{n}px}}</style>"""
                    f"""<h1>Conditions d'utilisation</h1><div id="rubrique_1" class="rubrique"><h2>Conditions d'utilisation</h2>"""
                    + "".join(f'<p style="margin:{n}px">{x}</p>' for x in etat.cg_paragraphes)
                    + f"""<div class="deplier" style="display:none"><p>{etat.cg_clause_repliee}</p></div>"""
                    f"""<p>Voir <a href="/index.php?page=commun.Aide&amp;PRADO_SESSION=S{n}&amp;sid={t}#aide">l'aide</a>.</p></div>"""
                    f"""<div id="rubrique_2" class="rubrique"><h2>Pré-requis techniques</h2><p>{etat.cg_prerequis}</p>"""
                    f"""<img src="/img/navigateurs.png?v={n}" alt="Navigateurs supportés"></div></div>""")
                corps = (f"""<!doctype html><html><head><title>Conditions - session {n}</title><script>var s="{t}";</script></head>"""
                         f"""<body><!-- rendu {t} --><div id="bandeau" class="bandeau">Nous sommes le {etat.cg_bandeau or time.strftime('%d/%m/%Y %H:%M:%S')}</div>"""
                         f"""<form><input type="hidden" name="PRADO_PAGESTATE" value="ETAT{n}-{t}">{sections}</form></body></html>""")
                return self._env(200, corps)
            if u.path == "/cgu.pdf":
                return self._env(200, etat.cg_doc, "application/pdf")
            if u.path == "/download":
                etat.telechargements.append(q.get("ref"))
                if etat.lenteur_s:
                    time.sleep(etat.lenteur_s)
                corps = b"PK\x03\x04 pas une archive" if q.get("ref") == "RBAD" else zip_fictif(etat.zip_date)
                if q.get("ref") != "RBAD":
                    etat.zips_servis.append(corps)
                return self._env(200, corps, "application/zip", {"Content-Disposition": f'attachment; filename="DCE_{q.get("ref")}.zip"'})
            ref, org = q.get("refConsultation", ""), q.get("orgAcronyme", "")
            if ref == "R403":
                return self._env(403, "<html><title>403 Interdit</title>Accès refusé</html>")
            if ref == "RCAP":
                return self._env(200, "<html><body>Merci de compléter le captcha</body></html>")
            if u.path == "/cadre":
                return self._env(200, self._form(ref, org))
            if ref == "RTABLE" and "jeton" not in q:   # variante : paramètre de session ajouté par redirection (ne doit jamais sortir)
                self.send_response(302)
                self.send_header("Location", f"/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation={ref}&orgAcronyme={org}&jeton=SESS-FICTIF")
                self.end_headers()
                return
            if ref == "RTABLE":   # variante : libellés en cellules de tableau, AUCUN <label for> ; état caché et valeur pré-remplie
                return self._env(200, f"""<!doctype html><html><head><title>PMMP - Demande de téléchargement</title></head><body><h1>Téléchargement du DCE</h1>
                <p>Référence : 00/2099/FICTIF</p><form method="post" action="/x"><input type="hidden" name="PRADO_PAGESTATE" value="JETON-SECRET-FICTIF">
                <table><tr><td>Nom <span>*</span> :</td><td><input type="text" name="ctl0$CONTENU$nom" id="ctl0_CONTENU_nom" value="VALEUR-FICTIVE"></td></tr>
                <tr><td>Prénom :</td><td><input type="text" name="ctl0$CONTENU$prenom" id="ctl0_CONTENU_prenom"></td></tr></table>
                <input type="submit" value="Valider"></form></body></html>""")
            if ref == "RCOMPLET":   # variante : état déjà téléchargé, sans formulaire
                return self._env(200, """<!doctype html><html><head><title>PMMP</title></head><body><p>Référence : 00/2099/FICTIF</p>
                <p>Téléchargement complet</p><a href="/download?ref=RCOMPLET">Télécharger le Dossier</a> <a href="/nouveau">Nouveau téléchargement</a></body></html>""")
            if ref == "RIFRAME":    # variante : formulaire dans un cadre interne
                return self._env(200, f"""<!doctype html><html><head><title>PMMP cadre</title></head><body><p>Référence : 00/2099/FICTIF</p>
                <iframe src="/cadre?page=formulaire&refConsultation={ref}&orgAcronyme={org}&jeton=SESS-CADRE" width="600" height="300"></iframe></body></html>""")
            if ref == "RREDIR":
                self.send_response(302)
                self.send_header("Location", f"/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation=AUTRE&orgAcronyme={org}")
                self.end_headers()
                return
            return self._env(200, self._form(ref, org))

        def do_POST(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            n = int(self.headers.get("Content-Length", "0"))
            brut = {k: v[0] for k, v in parse_qs(self.rfile.read(n).decode()).items()}
            f = {{"email": "mail", "accepterConditions": "cgu"}.get(k.split("$")[-1], k.split("$")[-1]): v for k, v in brut.items()}
            etat.soumis.append({"ref": q.get("refConsultation"), **f})
            if not (f.get("nom") and f.get("prenom") and f.get("mail") and f.get("cgu") == "on"):
                return self._env(200, self._form(q.get("refConsultation"), q.get("orgAcronyme"), "<p>Champs obligatoires manquants</p>"))
            return self._env(200, f"""<html><body><p>Téléchargement complet</p><a href="/download?ref={q.get('refConsultation')}">Télécharger le Dossier</a></body></html>""")
    return H


def demarrer():
    etat = Etat()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), construire(etat))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, etat


if __name__ == "__main__":  # banc cloud : portail FICTIF local seulement, port affiché ; aucun accès extérieur
    s, _ = demarrer()
    print("PORT", s.server_address[1], flush=True)
    threading.Event().wait()
