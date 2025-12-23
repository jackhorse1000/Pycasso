from pathlib import Path

from pycasso.harvest import harvest


def test_harvest_finds_python_files(tmp_path: Path):
    (tmp_path / "module.py").write_text("x = 1")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.py").write_text("y = 2")

    files = list(harvest(tmp_path, []))

    assert len(files) == 2
    names = {f.name for f in files}
    assert names == {"module.py", "nested.py"}


def test_harvest_excludes_venv(tmp_path: Path):
    (tmp_path / "main.py").write_text("x = 1")
    (tmp_path / "venv").mkdir()
    (tmp_path / "venv" / "lib.py").write_text("y = 2")

    files = list(harvest(tmp_path, ["venv"]))

    assert len(files) == 1
    assert files[0].name == "main.py"


def test_harvest_excludes_hidden_dirs(tmp_path: Path):
    (tmp_path / "main.py").write_text("x = 1")
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "secret.py").write_text("y = 2")

    files = list(harvest(tmp_path, []))

    assert len(files) == 1
    assert files[0].name == "main.py"


def test_harvest_excludes_pycache(tmp_path: Path):
    (tmp_path / "main.py").write_text("x = 1")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cached.py").write_text("y = 2")

    files = list(harvest(tmp_path, ["__pycache__"]))

    assert len(files) == 1


def test_harvest_empty_dir(tmp_path: Path):
    files = list(harvest(tmp_path, []))
    assert files == []
