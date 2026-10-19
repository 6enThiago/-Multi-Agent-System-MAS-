"""Permite ejecutar `python -m mas ...` como si fuera el comando `mas`."""
import sys

from .cli import main

sys.exit(main())
