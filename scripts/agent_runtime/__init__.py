"""Portable subset used by repository-local Agent Runtime scripts.

The extended package path preserves access to a separately installed full
Agent Runtime package while allowing adopted hosts to carry the bounded state
modules required by hooks and gates.
"""

from pkgutil import extend_path

__version__ = "0.7.0"
__path__ = extend_path(__path__, __name__)
