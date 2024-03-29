# CargoExport
![Tests](https://github.com/theneosloth/cargo/actions/workflows/ci.yml/badge.svg)
![Deployment](https://github.com/theneosloth/cargo/actions/workflows/cd.yml/badge.svg)

Export utilities for mediawiki cargo tables

Cargo table definitions are dynamically parsed into Pydantic dataclasses.

cargo/fetcher.py provides the basic interface for all fighting game wiki related methods.

Results are cached and network requests are lazy whenever possible

See sites/test_sites for up to date usage examples

```
from sites import dustloop, dreamcancel
assert (KOFXV["Kyo Kusanagi"]) is not None
assert len(KOFXV) >= 49
assert len(KOFXV.get_moves_by_input("Kyo Kusanagi", "214236A/C")) == 1

assert GGST.get_moves_by_input("Baiken", "41236H") is not None
assert BBCF.get_moves_by_input("Jin Kisaragi", "214B") is not None
assert GGACR.get_moves_by_input("Ky Kiske", "236S")[0].name == "S Stun Edge"

```

# Modules

This is currently a hodgepodge of vaguely related libraries and applications that could (and should) in the future be separated out

- cargo: lower level wrapper around the Mediawiki cargoquery endpoint
- sites: higher level wrapper around
- web: rest api wrapper around sites
