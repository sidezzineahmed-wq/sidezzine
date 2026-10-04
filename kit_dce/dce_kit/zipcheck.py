"""Validation d'une archive DCE reçue : signature, intégrité (CRC), chemins, limites, inventaire typé (sans extraction disque)."""
import hashlib
import io
import zipfile


class ZipInvalide(ValueError):
    pass


def inspecter(octets, zip_max=200 * 2**20, entrees_max=500, decompresse_max=1024 * 2**20, ratio_max=200):
    if not octets or octets[:4] != b"PK\x03\x04":
        raise ZipInvalide("le fichier reçu n'est pas une archive ZIP (signature)")
    if len(octets) > zip_max:
        raise ZipInvalide(f"archive de {len(octets)} octets au-delà de la limite")
    try:
        z = zipfile.ZipFile(io.BytesIO(octets))
    except zipfile.BadZipFile as e:
        raise ZipInvalide(f"archive illisible : {e}")
    infos = [i for i in z.infolist() if not i.is_dir()]
    if not infos:
        raise ZipInvalide("archive vide")
    if len(infos) > entrees_max:
        raise ZipInvalide("trop d'entrées")
    total, inv = 0, []
    for i in infos:
        p = i.filename.replace("\\", "/")
        if p.startswith("/") or ".." in p.split("/"):
            raise ZipInvalide(f"chemin dangereux : {i.filename}")
        if i.flag_bits & 1:
            raise ZipInvalide(f"entrée chiffrée : {i.filename}")
        if i.compress_size and i.file_size / max(i.compress_size, 1) > ratio_max:
            raise ZipInvalide(f"taux de compression suspect : {i.filename}")
        total += i.file_size
        if total > decompresse_max:
            raise ZipInvalide("volume décompressé au-delà de la limite")
        d = z.read(i)  # lève sur CRC invalide
        typ = "pdf" if d[:5] == b"%PDF-" else "office" if d[:4] == b"PK\x03\x04" else "autre"
        inv.append({"nom": p.split("/")[-1], "chemin": p, "taille": len(d), "sha256": hashlib.sha256(d).hexdigest(), "type": typ})
    if z.testzip():
        raise ZipInvalide("entrée corrompue")
    return {"sha256": hashlib.sha256(octets).hexdigest(), "taille": len(octets), "entrees": inv}
