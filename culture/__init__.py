from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _v

try:
    __version__ = _v("culture")
except PackageNotFoundError:
    try:
        __version__ = _v("agentirc-cli")
    except PackageNotFoundError:
        __version__ = _v("agentirc")
