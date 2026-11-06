"""Remove local source paths from shareable Playwright trace archives."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def sanitise_trace(path):
    path = Path(path)
    temporary = path.with_suffix(".sanitised.zip")
    with ZipFile(path) as source, ZipFile(temporary, "w", ZIP_DEFLATED) as target:
        for name in source.namelist():
            if name.endswith(".stacks") or "resources/src@" in name:
                continue
            data = source.read(name)
            for value in (
                str(Path.home()),
                str(Path.home()).replace("\\", "\\\\"),
                Path.home().as_posix(),
            ):
                data = data.replace(value.encode(), b"<local-user>")
            target.writestr(name, data)
    temporary.replace(path)
