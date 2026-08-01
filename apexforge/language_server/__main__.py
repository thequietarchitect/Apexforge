"""Module entry point for ``python -m language_server``."""

from language_server.server import main


if __name__ == "__main__":
    raise SystemExit(main())
