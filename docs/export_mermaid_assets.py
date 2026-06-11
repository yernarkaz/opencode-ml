"""Export Mermaid blocks from the slide markdown into standalone .mmd files.

This keeps Mermaid sources versioned and ready for SVG/PNG rendering via mermaid-cli.
"""

from pathlib import Path
import re


SOURCE = Path("docs/agentic-engineering-slides.md")
TARGET = Path("docs/mermaid-src")


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    matches = re.findall(r"```mermaid\n(.*?)```", text, flags=re.DOTALL)
    if not matches:
        raise SystemExit("No Mermaid blocks found")

    TARGET.mkdir(parents=True, exist_ok=True)

    for index, block in enumerate(matches, start=1):
        output = TARGET / f"slide{index}.mmd"
        output.write_text(block.strip() + "\n", encoding="utf-8")

    print(f"Exported {len(matches)} Mermaid sources to {TARGET}")


if __name__ == "__main__":
    main()
