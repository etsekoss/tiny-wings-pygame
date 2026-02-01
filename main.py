import sys
import os
import importlib

# Ajoute src/ au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import du vrai jeu (src/main.py)
importlib.import_module("main")
