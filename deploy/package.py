"""Package the current website and server without secrets, records or studio files."""

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
FILES = ("Dockerfile", "compose.yaml", ".dockerignore", ".env.example", "requirements.txt")
IGNORED = {"__pycache__", ".DS_Store", "data", "_pages", ".gitkeep"}


def package(destination):
    destination = Path(destination).expanduser().resolve()
    if destination.exists():
        raise FileExistsError("Choose a new archive name; existing files are not overwritten")
    if any(destination == ROOT / folder or ROOT / folder in destination.parents
           for folder in ("site", "server", "deploy")):
        raise ValueError("Archive must be outside site/server/deploy")
    destination.parent.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / name for name in FILES]
    sources.extend((ROOT / "docs" / name) for name in ("backend.md", "pamyatka-servera.md"))
    for folder in ("site", "server", "deploy"):
        sources.extend(path for path in (ROOT / folder).rglob("*")
                       if path.is_file() and not path.is_symlink()
                       and not any(part in IGNORED or part.startswith(".env")
                                   for part in path.relative_to(ROOT).parts)
                       and not path.name.endswith(".pyc")
                       and not any(suffix in path.name for suffix in (".sqlite", ".db")))
    with ZipFile(destination, "x", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(set(sources)):
            archive.write(source, "teacherdesk/" + source.relative_to(ROOT).as_posix())
        archive.writestr("teacherdesk/README.md", """# TeacherDesk: сайт и прием обращений

Локальный запуск из этой папки (Python 3.9+):

```sh
python3 -m server.manage init-env
python3 -m server --host 127.0.0.1 --port 8131
```

Сайт: http://127.0.0.1:8131/. Панель: http://127.0.0.1:8131/admin/.
Ключ панели создается в личном `.env`; в архиве его нет.
Инструкция Docker, HTTPS, переноса данных и резервных копий: docs/backend.md.
Вопросы отправляются из FAQ; консультация открывается по /#consultation.
Регистрация подключается к отдельному приложению через REGISTER_URL и LOGIN_URL.

Архив содержит текущие страницы для просмотра, включая примеры с noindex.
Перед публичным запуском нужно завершить приемку контента и документов.
Пользовательских данных и секретов в архиве нет.
""")
    print(str(destination))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", help="New .zip path outside site/server/deploy")
    args = parser.parse_args()
    package(args.destination)
