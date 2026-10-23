from filefit import updater


def test_version_compare():
    assert updater.is_newer("1.3.0", "1.2.0")
    assert updater.is_newer("1.10.0", "1.9.9")
    assert updater.is_newer("2.0", "1.99.99")
    assert not updater.is_newer("1.2.0", "1.2.0")
    assert not updater.is_newer("1.1.9", "1.2.0")
    assert not updater.is_newer("", "1.2.0")


def test_check_reports_only_newer(monkeypatch):
    rel = updater.Release(version="999.0.0", page="p", assets={"FileFit-Setup.exe": "u"})
    monkeypatch.setattr(updater, "fetch_latest", lambda timeout=8.0: rel)
    assert updater.check() is rel
    monkeypatch.setattr(updater, "fetch_latest", lambda timeout=8.0: updater.Release(version="0.0.1", page="p"))
    assert updater.check() is None


def test_source_install_is_pip():
    assert updater.install_kind() == "pip"
    assert not updater.can_self_install()
