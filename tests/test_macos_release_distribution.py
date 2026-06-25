import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MacOSReleaseDistributionTests(unittest.TestCase):
    def test_release_scripts_exist_and_are_executable(self):
        for name in [
            "sign-codex-probe-bar.sh",
            "notarize-codex-probe-bar.sh",
            "package-codex-probe-bar.sh",
            "preflight-codex-probe-bar.sh",
        ]:
            script = ROOT / "scripts" / "macos" / name
            self.assertTrue(script.exists(), name)
            self.assertTrue(os.access(script, os.X_OK), name)

    def test_release_scripts_use_standard_macos_distribution_tools(self):
        scripts = {
            path.name: path.read_text(encoding="utf-8")
            for path in (ROOT / "scripts" / "macos").glob("*codex-probe-bar.sh")
        }
        self.assertIn("codesign", scripts["sign-codex-probe-bar.sh"])
        self.assertIn("--options runtime", scripts["sign-codex-probe-bar.sh"])
        self.assertIn("notarytool submit", scripts["notarize-codex-probe-bar.sh"])
        self.assertIn("stapler staple", scripts["notarize-codex-probe-bar.sh"])
        self.assertIn("spctl --assess", scripts["notarize-codex-probe-bar.sh"])
        self.assertIn("ditto -c -k --keepParent", scripts["package-codex-probe-bar.sh"])
        self.assertIn("spctl --assess", scripts["preflight-codex-probe-bar.sh"])
        self.assertIn("stapler validate", scripts["preflight-codex-probe-bar.sh"])

    def test_release_distribution_docs_disclose_unsigned_beta_boundary(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        install = (ROOT / "docs" / "INSTALL.md").read_text(encoding="utf-8")
        release_doc = (ROOT / "docs" / "MACOS_RELEASE_DISTRIBUTION.md").read_text(encoding="utf-8")

        for text in [readme, install, release_doc]:
            self.assertIn("签名", text)
            self.assertIn("公证", text)

        self.assertIn("默认未签名、未公证", readme)
        self.assertIn("不能承诺普通用户", release_doc)
        self.assertIn("--require-signed --require-notarized", release_doc)

    def test_no_apple_credentials_are_hardcoded(self):
        candidates = [
            ROOT / "scripts" / "macos" / "sign-codex-probe-bar.sh",
            ROOT / "scripts" / "macos" / "notarize-codex-probe-bar.sh",
            ROOT / "scripts" / "macos" / "package-codex-probe-bar.sh",
            ROOT / "scripts" / "macos" / "preflight-codex-probe-bar.sh",
            ROOT / "docs" / "MACOS_RELEASE_DISTRIBUTION.md",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in candidates)
        forbidden_literals = [
            "-----BEGIN PRIVATE KEY-----",
            "-----BEGIN CERTIFICATE-----",
            "AKIA",
            "ghp_",
            "xoxb-",
            "sk-",
        ]
        for literal in forbidden_literals:
            self.assertNotIn(literal, combined)


if __name__ == "__main__":
    unittest.main()
