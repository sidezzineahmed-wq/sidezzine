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
        self.soumis, self.cg_texte, self.telechargements, self.vues = [], "J'accepte les conditions générales d'utilisation", [], []
        self.cg_doc, self.lien_cg, self.lenteur_s = b"%PDF-1.4 Conditions generales fictives v1 %%EOF", "/cgu.pdf", 0
        self.zip_date, self.zips_servis = None, []   # date fixe des entrées (None : heure courante) ; archives réellement servies


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
            return f"""<!doctype html><html><head><title>Téléchargement du DCE</title></head><body>
            <h1>Téléchargement du dossier de consultation</h1><p>Référence : {'00/2099/FICTIF' if ref != 'RAUTRE' else '99/2099/XX'}</p>{err}
            <form method="post" action="/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation={ref}&orgAcronyme={org}">
            <label for="nom">Nom *</label><input id="nom" name="nom"><label for="prenom">Prénom *</label><input id="prenom" name="prenom">
            <label for="mail">Adresse électronique *</label><input id="mail" name="mail"><label for="tel">Téléphone</label><input id="tel" name="tel">
            <input type="checkbox" id="cgu" name="cgu"><label for="cgu">{etat.cg_texte}</label> {f'<a href="{etat.lien_cg}">conditions générales</a>' if etat.lien_cg else ''}
            <button type="submit">Valider</button></form></body></html>"""

        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            etat.vues.append(self.path)
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
            f = {k: v[0] for k, v in parse_qs(self.rfile.read(n).decode()).items()}
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
