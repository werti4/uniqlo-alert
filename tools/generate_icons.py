"""Restore the bundled PNG icons from text; no downloads or dependencies required."""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = {
    'icon128.png': (
        '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'
        'rkJggg=='
    ),
    'icon16.png': (
        'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAuElEQVR4nGN8oW3wn4ECwESJZuobwKKqwiB+5TwDT142AwMD'
        'AwOrthaD+JXzDNzpqXRywcAb8P/HDwiDmRlCs7BAxH9CxMWvnMdvwN9nzxn+ffjIwGZsxMDIzc3AZmnOwMDAwPDn6nXiXMDw'
        '9y/Dx9JyBkZOTgbRQ/sYOEODGb5MnMLw6/QZnAawoAv8On6S4W1wOE4N+F2AA6D7HZnPSGxeQNb0UseQNBcga0LWTJIB2DST'
        'bAA2AAA8mjStEJlEEAAAAABJRU5ErkJggg=='
    ),
    'icon32.png': (
        'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABPElEQVR4nGN8oW3wn2EAAdNAWj7qgFEH4HUAh6c7g/iV83DM'
        'yM6GIs8VFQGXEzt3kvoOoBcYdcCoA4aJAyioznA64P+PHyh8Ri5uVD43N5La79R3wN9Hj1H4LMqKqHwlRZxqGRgY4IUU2Q74'
        'c/cew5/bd+B8nsICBhYFBQZGLi4GdldnBnY3V7jcjx27CFqECzDia5Cw6mgzCM6ZycDIw41LCcOvE6cYPmTmMPz//RtFHOb7'
        'lzqGeB3Agk/y95WrDG8DQxi44mIY2CzMGZhlpBkY2dgY/n3+wvDn1i2GH9t3Mnxfu56B4d8/vJaQ7QAGBgaGv89fMHzu7CHb'
        'AkJgmJQDg8EBhLIcLnmqOeCljiFOS8SvnMeZG6gaBdgcgc9yqjsAmyMIlQM0SYSELEUGeEtCeoDhkw1HHUAuAABK7GVaQIt8'
        'TQAAAABJRU5ErkJggg=='
    ),
    'icon48.png': (
        'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAACAUlEQVR4nO2YTUsCQRyHf7u6mSQZXYJCozpmYZfoVMfoEH2C'
        'oEAqCPoQQTcpCLpLHaRTBNE1ukWHNnqljtqhPBSaLeao2yFW0t3F2XV1lOY5yex/Zn6P67yg8DoaVtHGiKwD1AsXYA0XYA0X'
        'YI2bttC3sY6ulUhFmxI7wGd027C+e2sT3oX5irbP6A6U2L6NmOa0/RvgAqzhAqzhAqzhAqzhAqyhFlALBYPegmm9IBoMTQjt'
        'dNTQC6QzujbB5zOtN3pWyujHqBdqgWIyqWtzjwyb1ruHh/RjJBK001FDfZ3OX8lQCYEgSeU2aSwEVzCAYqJSTgqNwjUYrGhT'
        's18g94+6cfvu5PLnt9AEdXAN+p9Q9gu5o+Oq3iJ69nbRMTUJweOB4PXCMzMN/05U11+JHwJG66hOBCt/bIl+P3rjB3AFA5Ym'
        'KTw9431xGaqi6J417Q0AQCmdxvtSBPmLS+o+32fn+IisGYZ3Auo1oFFKpfARWYU0EUbn3Cyk8TG4Bvp/dx1VhZrNoph8Abm5'
        'Re7kFOT+oRG5y1gW0CDyNYh87WAUe/yfk7hV4QKsabrA333fibqmCmihaoWjrQOaLPD3pDULZ/VktnSVcAqab5b2WsFkEdcK'
        'Z+VOxGwXMgtp9ULHdButDtvw22gj0ELbCQ+0gABgPzzQIgL1wAVYwwVY0/YCP6JslxfP3RckAAAAAElFTkSuQmCC'
    ),
}


def generate(destination: Path | None = None) -> None:
    """Write the exact original PNG bytes into extension/icons by default."""
    target = destination if destination is not None else ROOT / "extension" / "icons"
    target.mkdir(parents=True, exist_ok=True)
    for name, encoded in ICONS.items():
        (target / name).write_bytes(base64.b64decode(encoded, validate=True))


if __name__ == "__main__":
    generate()
    print("Four bundled extension icons generated.")
