import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # Se for EXE, a raiz é onde o EXE está
    BASE_DIR = Path(sys.executable).parent
else:
    # Se for script, a raiz é o local deste arquivo de config
    # Como o config.py está na raiz, apenas um .parent basta
    BASE_DIR = Path(__file__).resolve().parent
