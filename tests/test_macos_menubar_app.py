import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MacOSMenuBarAppTests(unittest.TestCase):
    def test_macos_menu_bar_sources_exist(self):
        package = ROOT / "desktop" / "macos" / "CodexProbeBar" / "Package.swift"
        source = ROOT / "desktop" / "macos" / "CodexProbeBar" / "Sources" / "CodexProbeBar" / "main.swift"
        script = ROOT / "scripts" / "macos" / "build-codex-probe-bar.sh"
        app_doc = ROOT / "docs" / "MACOS_MENUBAR_APP.md"
        release_doc = ROOT / "docs" / "MACOS_RELEASE_DISTRIBUTION.md"
        self.assertTrue(package.exists())
        self.assertTrue(source.exists())
        self.assertTrue(script.exists())
        self.assertTrue(app_doc.exists())
        self.assertTrue(release_doc.exists())
        self.assertTrue(os.access(script, os.X_OK))

    def test_macos_menu_bar_reuses_cli_and_preserves_privacy_boundary(self):
        source = (ROOT / "desktop" / "macos" / "CodexProbeBar" / "Sources" / "CodexProbeBar" / "main.swift").read_text(
            encoding="utf-8"
        )
        self.assertIn("codex-probe", source)
        self.assertIn("--json", source)
        self.assertIn("sessions", source)
        self.assertIn("alerts", source)
        self.assertIn("confidence-report", source)
        self.assertIn("dashboard", source)
        self.assertIn("不登录、不读 cookie、不碰 token/钥匙串、不抓包、不上传", source)
        forbidden = [
            "Keychain",
            "SecItemCopyMatching",
            "HTTPCookie",
            "URLSession",
            "WKWebView",
            "SFAuthorization",
            "NEPacketTunnel",
            "CGEventTapCreate",
        ]
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_macos_bundle_script_writes_lsui_element_app(self):
        script = (ROOT / "scripts" / "macos" / "build-codex-probe-bar.sh").read_text(encoding="utf-8")
        self.assertIn("LSUIElement", script)
        self.assertIn("defaults.json", script)
        self.assertIn("CODEX_PROBE_CLI", script)
        self.assertIn("0.9.0", script)


if __name__ == "__main__":
    unittest.main()
