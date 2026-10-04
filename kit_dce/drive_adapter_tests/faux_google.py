"""Faux serveur Google LOCAL (127.0.0.1) reproduisant le protocole documenté : jeton OAuth (refresh_token), envoi resumable
(Location de session, PUT avec Content-Range, 308 + Range, interrogation « bytes */N »), téléchargement alt=media.
Aucun accès réseau extérieur. Pannes injectables : coupure de connexion, jeton expiré, refresh invalide, fichier corrompu."""
import hashlib
import json
import re
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORTEE = "https://www.googleapis.com/auth/drive.file"


class Etat:
    def __init__(self):
        self.jetons, self.emis, self.sessions, self.fichiers = set(), 0, {}, {}
        self.couper_morceaux = set()      # indices de PUT de données à couper (connexion fermée sans réponse)
        self.expirer_premier = False      # le premier jeton émis est refusé une fois (401)
        self.refus_401 = 0
        self.corrompre = False            # téléchargement : un octet modifié
        self.puts = 0
        self.octets_recus = 0
        self.requetes = []                # (méthode, chemin) — pour vérifier qu'aucune requête ne part ailleurs
        self.duree_jeton = 3599           # expires_in renvoyé au renouvellement
        self.toujours_401 = False         # l'API Drive refuse tout jeton (401)
        self.corps_jeton = []             # champs reçus par /token (après proxy simulé)
        self.metas = {}                   # id -> fiche (name, mimeType, parents, appProperties)
        self.recherches = []              # requêtes q reçues


_VAL = r"'((?:[^'\\]|\\.)*)'"
_CLAUSES = [(re.compile(r"name = " + _VAL), lambda m, f: f.get("name") == _dv(m.group(1))),
            (re.compile(r"mimeType = " + _VAL), lambda m, f: f.get("mimeType") == _dv(m.group(1))),
            (re.compile(_VAL + r" in parents"), lambda m, f: _dv(m.group(1)) in f.get("parents", [])),
            (re.compile(r"appProperties has \{ key=" + _VAL + r" and value=" + _VAL + r" \}"),
             lambda m, f: (f.get("appProperties") or {}).get(_dv(m.group(1))) == _dv(m.group(2))),
            (re.compile(r"trashed = false"), lambda m, f: True)]


def _dv(v):
    return re.sub(r"\\(.)", r"\1", v)


def filtrer(q, metas):
    """Sous-ensemble de la syntaxe q de Drive utilisé par l'adaptateur ; toute autre syntaxe est refusée (ValueError)."""
    tests, reste = [], q
    for rx, fn in _CLAUSES:
        for m in list(rx.finditer(q)):
            tests.append((m, fn))
            reste = reste.replace(m.group(0), "", 1)
    if re.sub(r"\s+", " ", reste).replace("and", "").strip():
        raise ValueError("syntaxe q non prise en charge : " + reste)
    return [f for f in metas.values() if all(fn(m, f) for m, fn in tests)]


def fiche(et, fid):
    f = dict(et.metas[fid])
    if fid in et.fichiers:
        f["size"] = str(len(et.fichiers[fid]))
        f["md5Checksum"] = hashlib.md5(et.fichiers[fid]).hexdigest()
    return f


def construire(et):
    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _rep(self, code, corps=b"", entetes=None):
            b = corps if isinstance(corps, bytes) else json.dumps(corps).encode()
            self.send_response(code)
            for k, v in (entetes or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def _corps(self):
            return self.rfile.read(int(self.headers.get("Content-Length") or 0))

        def _auth(self):
            a = self.headers.get("Authorization", "")
            t = a[7:] if a.startswith("Bearer ") else ""
            if t not in et.jetons or et.toujours_401:
                self._rep(401, {"error": "invalid_token"})
                return False
            if et.expirer_premier and t == "tok-1" and et.refus_401 == 0:
                et.refus_401 += 1
                et.jetons.discard(t)
                self._rep(401, {"error": "expired"})
                return False
            return True

        def do_POST(self):
            u = urlparse(self.path)
            et.requetes.append(("POST", u.path))
            if u.path == "/token":
                f = {k: v[0] for k, v in parse_qs(self._corps().decode()).items()}
                et.corps_jeton.append(sorted(f))
                if f.get("grant_type") != "refresh_token" or f.get("refresh_token") == "refresh-invalide" or not (f.get("client_id") and f.get("client_secret") and f.get("refresh_token")):
                    return self._rep(400, {"error": "invalid_grant"})
                et.emis += 1
                t = f"tok-{et.emis}"
                et.jetons.add(t)
                return self._rep(200, {"access_token": t, "scope": PORTEE, "expires_in": et.duree_jeton, "token_type": "Bearer"})
            if u.path == "/upload" and parse_qs(u.query).get("uploadType") == ["resumable"]:
                meta = json.loads(self._corps() or b"{}")
                if not self._auth():
                    return
                sid = "SESSIONSECRET" + uuid.uuid4().hex[:12]
                et.sessions[sid] = {"meta": meta, "taille": int(self.headers["X-Upload-Content-Length"]), "donnees": bytearray(), "fini": None}
                host = self.headers["Host"]
                return self._rep(200, b"", {"Location": f"http://{host}/upload?uploadType=resumable&upload_id={sid}"})
            if u.path == "/files":
                meta = json.loads(self._corps() or b"{}")
                if not self._auth():
                    return
                fid = "1Fd" + uuid.uuid4().hex[:24]
                et.metas[fid] = {"id": fid, "name": meta.get("name"), "mimeType": meta.get("mimeType"), "parents": meta.get("parents", ["racine-drive"]),
                                 "appProperties": meta.get("appProperties", {})}
                return self._rep(200, fiche(et, fid), {"Content-Type": "application/json"})
            self._rep(404, {"error": "inconnu"})

        def do_PATCH(self):
            u = urlparse(self.path)
            et.requetes.append(("PATCH", u.path))
            m = re.fullmatch(r"/upload/([A-Za-z0-9_-]+)", u.path)
            d = self._corps()
            if not m or parse_qs(u.query).get("uploadType") != ["media"]:
                return self._rep(404, {"error": "inconnu"})
            if not self._auth():
                return
            if m.group(1) not in et.fichiers:
                return self._rep(404, {"error": "absent"})
            et.fichiers[m.group(1)] = d
            return self._rep(200, fiche(et, m.group(1)), {"Content-Type": "application/json"})

        def do_PUT(self):
            u = urlparse(self.path)
            et.requetes.append(("PUT", u.path))
            sid = (parse_qs(u.query).get("upload_id") or [""])[0]
            s = et.sessions.get(sid)
            if not s:
                self._corps()
                return self._rep(404, {"error": "session inconnue"})
            cr = self.headers.get("Content-Range", "")
            m_stat = re.fullmatch(r"bytes \*/(\d+)", cr)
            m_dat = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", cr)
            if m_stat:
                self._corps()
                return self._fin_ou_308(s)
            if not m_dat:
                return self._rep(400, {"error": "Content-Range"})
            a, b = int(m_dat.group(1)), int(m_dat.group(2))
            n = et.puts
            et.puts += 1
            if n in et.couper_morceaux:  # panne : la moitié du morceau arrive, puis la connexion est fermée sans réponse
                moitie = int(self.headers.get("Content-Length") or 0) // 2
                self.rfile.read(moitie)
                self.close_connection = True
                self.connection.shutdown(2)
                return
            d = self._corps()
            et.octets_recus += len(d)
            if a != len(s["donnees"]):
                return self._fin_ou_308(s)
            s["donnees"] += d
            if len(s["donnees"]) >= s["taille"]:
                fid = "1Fx" + uuid.uuid4().hex[:24]
                et.fichiers[fid] = bytes(s["donnees"])
                mt = s["meta"]
                et.metas[fid] = {"id": fid, "name": mt.get("name"), "mimeType": mt.get("mimeType", "application/octet-stream"),
                                 "parents": mt.get("parents", ["racine-drive"]), "appProperties": mt.get("appProperties", {})}
                s["fini"] = {"id": fid, "name": s["meta"].get("name"), "size": str(len(s["donnees"])), "appProperties": s["meta"].get("appProperties", {})}
            return self._fin_ou_308(s)

        def _fin_ou_308(self, s):
            if s["fini"]:
                return self._rep(200, s["fini"], {"Content-Type": "application/json"})
            h = {"Range": f"bytes=0-{len(s['donnees']) - 1}"} if s["donnees"] else {}
            return self._rep(308, b"", h)

        def do_GET(self):
            u = urlparse(self.path)
            et.requetes.append(("GET", u.path))
            if u.path == "/files":
                if not self._auth():
                    return
                q = parse_qs(u.query).get("q", [""])[0]
                et.recherches.append(q)
                try:
                    r = filtrer(q, et.metas)
                except ValueError as e:
                    return self._rep(400, {"error": str(e)})
                return self._rep(200, {"files": [fiche(et, f["id"]) for f in r]}, {"Content-Type": "application/json"})
            m = re.fullmatch(r"/files/([A-Za-z0-9_-]+)", u.path)
            if m and parse_qs(u.query).get("alt") != ["media"]:
                if not self._auth():
                    return
                if m.group(1) not in et.metas:
                    return self._rep(404, {"error": "absent"})
                return self._rep(200, fiche(et, m.group(1)), {"Content-Type": "application/json"})
            if not m:
                return self._rep(404, {"error": "inconnu"})
            if not self._auth():
                return
            if m.group(1) == "1FxINTERDIT0000":
                return self._rep(403, {"error": "forbidden"})
            d = et.fichiers.get(m.group(1))
            if d is None:
                return self._rep(404, {"error": "absent"})
            if et.corrompre:
                d = d[:100] + bytes([d[100] ^ 1]) + d[101:]
            self._rep(200, d, {"Content-Type": "application/octet-stream"})
    return H


def demarrer():
    et = Etat()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), construire(et))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    p = srv.server_address[1]
    urls = {"jeton": f"http://127.0.0.1:{p}/token", "envoi": f"http://127.0.0.1:{p}/upload?uploadType=resumable&fields=id,name,size,appProperties",
            "fichier": f"http://127.0.0.1:{p}/files/{{id}}?alt=media", "api": f"http://127.0.0.1:{p}/files",
            "maj": f"http://127.0.0.1:{p}/upload/{{id}}?uploadType=media&fields=id,name,size,md5Checksum,appProperties"}
    return srv, et, urls
