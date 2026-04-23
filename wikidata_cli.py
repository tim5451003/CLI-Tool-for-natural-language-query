"""相容入口：保留原本 `python wikidata_cli.py` 使用方式。"""

from cli import main


if __name__ == "__main__":
    raise SystemExit(main())
