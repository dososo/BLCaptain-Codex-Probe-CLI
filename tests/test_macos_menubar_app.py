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
        self.assertIn("runner.prepare()", source)
        self.assertIn("statusTitle(\"Codex\")", source)
        self.assertIn("NSStatusItem.squareLength", source)
        self.assertIn("button.title = \"\"", source)
        self.assertIn("button.imagePosition = .imageOnly", source)
        self.assertIn("button.toolTip = \"BLCaptain Codex Probe\"", source)
        self.assertNotIn("Codex" + " ?", source)
        self.assertIn("NSSize(width: 372, height: 520)", source)
        self.assertIn("RiskBadge(text: alertActionText(item)", source)
        self.assertIn("Text(alertUsageText(item))", source)
        self.assertIn("func alertActionText(_ item: AlertItem) -> String", source)
        self.assertIn("func alertUsageText(_ item: AlertItem) -> String", source)
        self.assertIn("已用 \\(formatCompactNumber(item.tokenDelta))，触发本地预警", source)
        self.assertIn("当前没有触发本地预警。", source)
        self.assertNotIn("let threshold", source)
        self.assertNotIn("预警线", source)
        self.assertNotIn("formatCompactPercent", source)
        self.assertNotIn("formatBudgetPressure", source)
        self.assertNotIn("K%\"", source)
        self.assertIn("codex-probe-bar.db", source)
        self.assertIn("Library/Application Support/BLCaptain Codex Probe", source)
        self.assertIn("不读 cookie/token/钥匙串，不上传", source)
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
        self.assertIn("pip install --quiet \"$ROOT\"", script)
        self.assertIn("Library/Application Support/BLCaptain Codex Probe", script)
        self.assertIn("codex-probe-bar.db", script)
        self.assertIn("Reports", script)
        self.assertIn("0.9.1", script)


if __name__ == "__main__":
    unittest.main()
