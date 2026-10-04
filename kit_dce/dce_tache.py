"""Point d'entrée du kit DCE : python3 kit_dce/dce_tache.py <commande> (voir dce_kit/tache.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dce_kit.tache import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
