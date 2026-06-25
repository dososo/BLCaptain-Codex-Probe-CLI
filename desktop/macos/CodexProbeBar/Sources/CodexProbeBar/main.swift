import AppKit
import SwiftUI
import Foundation

struct ProbeConfig: Equatable, Sendable {
    let cliPath: String
    let dbPath: String
    let reportsDir: String
    let range: String
    let workingDirectory: String

    static func load() -> ProbeConfig {
        let env = ProcessInfo.processInfo.environment
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        let bundle = BundleDefaults.load()
        let cwd = env["CODEX_PROBE_PROJECT_DIR"]
            ?? bundle.projectDir
            ?? home
        let cli = env["CODEX_PROBE_CLI"]
            ?? bundle.cliPath
            ?? ProbeConfig.findCLI(home: home)
            ?? "codex-probe"
        let db = ProbeConfig.firstWritableFile(
            preferred: env["CODEX_PROBE_DB"] ?? bundle.dbPath ?? "\(cwd)/.probe/codex-probe-bar.db",
            fallbackDirectories: [
                "\(cwd)/.probe",
                "\(home)/Library/Application Support/BLCaptain Codex Probe",
                NSTemporaryDirectory()
            ],
            filename: "codex-probe-bar.db"
        )
        let reports = ProbeConfig.firstWritableDirectory([
            env["CODEX_PROBE_REPORTS_DIR"] ?? bundle.reportsDir ?? "\(cwd)/reports/ledger",
            "\(cwd)/reports/ledger",
            "\(home)/Library/Application Support/BLCaptain Codex Probe/Reports",
            NSTemporaryDirectory() + "codex-probe-reports"
        ])
        let range = env["CODEX_PROBE_RANGE"]
            ?? bundle.range
            ?? "7d"
        return ProbeConfig(cliPath: cli, dbPath: db, reportsDir: reports, range: range, workingDirectory: cwd)
    }

    private static func findCLI(home: String) -> String? {
        let candidates = [
            "\(home)/.local/bin/codex-probe",
            "\(home)/.venv/bin/codex-probe",
            "\(home)/bin/codex-probe",
            "/opt/homebrew/bin/codex-probe",
            "/usr/local/bin/codex-probe"
        ]
        return candidates.first { FileManager.default.isExecutableFile(atPath: $0) }
    }

    private static func firstWritableDirectory(_ candidates: [String]) -> String {
        let manager = FileManager.default
        for candidate in candidates {
            guard !candidate.isEmpty else { continue }
            do {
                try manager.createDirectory(atPath: candidate, withIntermediateDirectories: true)
                let marker = "\(candidate)/.codex-probe-write-test"
                try "ok".write(toFile: marker, atomically: true, encoding: .utf8)
                try? manager.removeItem(atPath: marker)
                return candidate
            } catch {
                continue
            }
        }
        return NSTemporaryDirectory()
    }

    private static func firstWritableFile(preferred: String, fallbackDirectories: [String], filename: String) -> String {
        let manager = FileManager.default
        let preferredURL = URL(fileURLWithPath: preferred)
        let preferredDir = preferredURL.deletingLastPathComponent().path
        if canWriteDirectory(preferredDir, manager: manager) {
            return preferred
        }
        for directory in fallbackDirectories {
            if canWriteDirectory(directory, manager: manager) {
                return URL(fileURLWithPath: directory).appendingPathComponent(filename).path
            }
        }
        return URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent(filename).path
    }

    private static func canWriteDirectory(_ path: String, manager: FileManager) -> Bool {
        do {
            try manager.createDirectory(atPath: path, withIntermediateDirectories: true)
            let marker = "\(path)/.codex-probe-write-test"
            try "ok".write(toFile: marker, atomically: true, encoding: .utf8)
            try? manager.removeItem(atPath: marker)
            return true
        } catch {
            return false
        }
    }
}

struct BundleDefaults: Decodable, Sendable {
    let cliPath: String?
    let dbPath: String?
    let reportsDir: String?
    let range: String?
    let projectDir: String?

    static func load() -> BundleDefaults {
        guard
            let url = Bundle.main.resourceURL?.appendingPathComponent("defaults.json"),
            let data = try? Data(contentsOf: url),
            let parsed = try? JSONDecoder().decode(BundleDefaults.self, from: data)
        else {
            return BundleDefaults(cliPath: nil, dbPath: nil, reportsDir: nil, range: nil, projectDir: nil)
        }
        return parsed
    }
}

struct SessionsPayload: Decodable, Sendable {
    let sessionCount: Int
    let sessions: [SessionItem]

    enum CodingKeys: String, CodingKey {
        case sessionCount = "session_count"
        case sessions
    }
}

struct SessionItem: Decodable, Identifiable, Sendable {
    let sessionId: String
    let title: String
    let project: String
    let model: String
    let tokenDelta: Int
    let confidenceLevel: String
    let recommendation: String

    var id: String { sessionId }

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case title
        case project
        case model
        case tokenDelta = "token_delta"
        case confidenceLevel = "confidence_level"
        case recommendation
    }
}

struct AlertsPayload: Decodable, Sendable {
    let alertCount: Int
    let alerts: [AlertItem]

    enum CodingKeys: String, CodingKey {
        case alertCount = "alert_count"
        case alerts
    }
}

struct AlertItem: Decodable, Identifiable, Sendable {
    let scope: String
    let name: String
    let tokenDelta: Int
    let usagePercent: Double
    let severity: String
    let recommendation: String

    var id: String { "\(scope)-\(name)-\(severity)" }

    enum CodingKeys: String, CodingKey {
        case scope
        case name
        case tokenDelta = "token_delta"
        case usagePercent = "usage_percent"
        case severity
        case recommendation
    }
}

struct ConfidencePayload: Decodable, Sendable {
    let sources: [SourceItem]
}

struct SourceItem: Decodable, Identifiable, Sendable {
    let sourceType: String
    let enabled: Bool
    let confidenceCeiling: String
    let snapshotCount: Int
    let missingFields: [String]
    let diagnosis: String

    var id: String { sourceType }

    enum CodingKeys: String, CodingKey {
        case sourceType = "source_type"
        case enabled
        case confidenceCeiling = "confidence_ceiling"
        case snapshotCount = "snapshot_count"
        case missingFields = "missing_fields"
        case diagnosis
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        sourceType = try container.decode(String.self, forKey: .sourceType)
        enabled = (try? container.decode(Bool.self, forKey: .enabled)) ?? true
        confidenceCeiling = try container.decode(String.self, forKey: .confidenceCeiling)
        snapshotCount = try container.decode(Int.self, forKey: .snapshotCount)
        missingFields = try container.decode([String].self, forKey: .missingFields)
        diagnosis = try container.decode(String.self, forKey: .diagnosis)
    }
}

struct ProbeSnapshot: Sendable {
    var totalTokens: Int = 0
    var sessionCount: Int = 0
    var alertCount: Int = 0
    var topSession: SessionItem?
    var alerts: [AlertItem] = []
    var sources: [SourceItem] = []
    var lastUpdated: Date?
    var message: String = "等待刷新"
}

struct CommandResult: Sendable {
    let status: Int32
    let stdout: String
    let stderr: String
}

final class ProbeRunner: @unchecked Sendable {
    let config: ProbeConfig

    init(config: ProbeConfig) {
        self.config = config
        try? FileManager.default.createDirectory(atPath: config.reportsDir, withIntermediateDirectories: true)
        try? FileManager.default.createDirectory(
            atPath: URL(fileURLWithPath: config.dbPath).deletingLastPathComponent().path,
            withIntermediateDirectories: true
        )
    }

    func run(_ args: [String]) throws -> CommandResult {
        let process = Process()
        if config.cliPath.contains("/") {
            guard FileManager.default.isExecutableFile(atPath: config.cliPath) else {
                throw RuntimeError("找不到可执行的 codex-probe CLI：\(config.cliPath)。请先运行 scripts/setup-local.sh 或 scripts/macos/build-codex-probe-bar.sh。")
            }
            process.executableURL = URL(fileURLWithPath: config.cliPath)
            process.arguments = args
        } else {
            process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
            process.arguments = [config.cliPath] + args
        }
        process.currentDirectoryURL = URL(fileURLWithPath: config.workingDirectory)
        let currentPath = ProcessInfo.processInfo.environment["PATH"] ?? ""
        let localBin = "\(config.workingDirectory)/.venv/bin"
        process.environment = ProcessInfo.processInfo.environment.merging([
            "PYTHONDONTWRITEBYTECODE": "1",
            "PATH": "\(localBin):/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:\(currentPath)"
        ]) { _, new in new }

        let out = Pipe()
        let err = Pipe()
        process.standardOutput = out
        process.standardError = err
        try process.run()
        process.waitUntilExit()

        let stdout = String(data: out.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
        let stderr = String(data: err.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
        return CommandResult(status: process.terminationStatus, stdout: stdout, stderr: stderr)
    }

    func prepare() throws {
        try FileManager.default.createDirectory(atPath: config.reportsDir, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(
            atPath: URL(fileURLWithPath: config.dbPath).deletingLastPathComponent().path,
            withIntermediateDirectories: true
        )

        let help = try run(["--help"])
        guard help.status == 0 else {
            throw RuntimeError((help.stderr.isEmpty ? help.stdout : help.stderr).trimmingCharacters(in: .whitespacesAndNewlines))
        }
        guard help.stdout.contains("alerts"), help.stdout.contains("confidence-report") else {
            throw RuntimeError("当前 codex-probe CLI 版本过旧，不支持状态栏 App 所需命令。请重新运行 scripts/setup-local.sh 或 scripts/macos/build-codex-probe-bar.sh。")
        }

        if !FileManager.default.fileExists(atPath: config.dbPath) {
            let setup = try run([
                "--db", config.dbPath,
                "--json",
                "setup",
                "--sample",
                "--no-open",
                "--out-dir", config.reportsDir
            ])
            guard setup.status == 0 else {
                throw RuntimeError((setup.stderr.isEmpty ? setup.stdout : setup.stderr).trimmingCharacters(in: .whitespacesAndNewlines))
            }
        }
    }

    func json<T: Decodable>(_ type: T.Type, _ command: [String]) throws -> T {
        let result = try run(["--db", config.dbPath, "--json"] + command)
        guard result.status == 0 else {
            throw RuntimeError(result.stderr.isEmpty ? result.stdout : result.stderr)
        }
        do {
            return try JSONDecoder().decode(T.self, from: Data(result.stdout.utf8))
        } catch {
            throw RuntimeError("CLI JSON 解析失败：\(error.localizedDescription)。输出：\(String(result.stdout.prefix(300)))")
        }
    }

    func reportPath(_ name: String) -> String {
        "\(config.reportsDir)/\(name)"
    }
}

struct RuntimeError: LocalizedError, Sendable {
    let message: String

    init(_ message: String) {
        self.message = message
    }

    var errorDescription: String? { message }
}

@MainActor
final class ProbeStore: ObservableObject {
    @Published var snapshot = ProbeSnapshot()
    @Published var isLoading = false
    @Published var lastError: String?

    private let runner: ProbeRunner
    private let statusTitle: (String) -> Void

    init(runner: ProbeRunner, statusTitle: @escaping (String) -> Void) {
        self.runner = runner
        self.statusTitle = statusTitle
    }

    func refresh() {
        guard !isLoading else { return }
        isLoading = true
        lastError = nil
        Task.detached { [runner] in
            do {
                try runner.prepare()
                let sessions: SessionsPayload = try runner.json(
                    SessionsPayload.self,
                    [
                        "sessions",
                        "--range", runner.config.range,
                        "--out", runner.reportPath("sessions.md")
                    ]
                )
                let alerts: AlertsPayload = try runner.json(
                    AlertsPayload.self,
                    [
                        "alerts",
                        "--range", runner.config.range,
                        "--out", runner.reportPath("alerts.md")
                    ]
                )
                let confidence: ConfidencePayload = try runner.json(
                    ConfidencePayload.self,
                    [
                        "confidence-report",
                        "--out", runner.reportPath("source-confidence.md")
                    ]
                )
                _ = try? runner.run([
                    "--db", runner.config.dbPath,
                    "--json",
                    "dashboard",
                    "--range", runner.config.range,
                    "--out", runner.reportPath("dashboard.html")
                ])
                let top = sessions.sessions.first
                let total = sessions.sessions.reduce(0) { $0 + $1.tokenDelta }
                let updated = ProbeSnapshot(
                    totalTokens: total,
                    sessionCount: sessions.sessionCount,
                    alertCount: alerts.alertCount,
                    topSession: top,
                    alerts: alerts.alerts,
                    sources: confidence.sources,
                    lastUpdated: Date(),
                    message: top == nil ? "暂无会话账本数据" : "已读取本地账本"
                )
                await MainActor.run {
                    self.snapshot = updated
                    self.isLoading = false
                    self.statusTitle("Codex")
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                    self.lastError = error.localizedDescription.trimmingCharacters(in: .whitespacesAndNewlines)
                    self.snapshot.message = "需要检查本地 CLI"
                    self.statusTitle("Codex")
                }
            }
        }
    }

    func runOnce() {
        guard !isLoading else { return }
        isLoading = true
        lastError = nil
        Task.detached { [runner] in
            do {
                try runner.prepare()
                _ = try runner.run(["--db", runner.config.dbPath, "--json", "watch", "once"])
                await MainActor.run {
                    self.isLoading = false
                    self.refresh()
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                    self.lastError = error.localizedDescription
                }
            }
        }
    }

    func generateDashboardAndOpen() {
        guard !isLoading else { return }
        isLoading = true
        lastError = nil
        Task.detached { [runner] in
            do {
                try runner.prepare()
                _ = try runner.run([
                    "--db", runner.config.dbPath,
                    "--json",
                    "dashboard",
                    "--range", runner.config.range,
                    "--out", runner.reportPath("dashboard.html")
                ])
                await MainActor.run {
                    self.isLoading = false
                    self.openDashboard()
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                    self.lastError = error.localizedDescription
                }
            }
        }
    }

    func openDashboard() {
        NSWorkspace.shared.open(URL(fileURLWithPath: runner.reportPath("dashboard.html")))
    }

    func openReports() {
        NSWorkspace.shared.open(URL(fileURLWithPath: runner.config.reportsDir, isDirectory: true))
    }

    func generatePrivacyAndOpen() {
        guard !isLoading else { return }
        isLoading = true
        lastError = nil
        Task.detached { [runner] in
            do {
                try runner.prepare()
                _ = try runner.run([
                    "--db", runner.config.dbPath,
                    "--json",
                    "privacy",
                    "inspect",
                    "--out", runner.reportPath("privacy-report.md")
                ])
                await MainActor.run {
                    self.isLoading = false
                    NSWorkspace.shared.open(URL(fileURLWithPath: runner.reportPath("privacy-report.md")))
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                    self.lastError = error.localizedDescription
                }
            }
        }
    }

    var config: ProbeConfig { runner.config }
}

struct CodexProbePanel: View {
    @ObservedObject var store: ProbeStore

    var body: some View {
        ZStack(alignment: .top) {
            Color(nsColor: .windowBackgroundColor)
            LinearGradient(
                colors: [
                    Color(red: 0.04, green: 0.12, blue: 0.26),
                    Color(red: 0.02, green: 0.42, blue: 0.48),
                    Color(red: 0.12, green: 0.50, blue: 0.30)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .frame(height: 126)
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(.white.opacity(0.10))
                    .frame(height: 1)
            }

            VStack(spacing: 0) {
                ScrollView(showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 10) {
                        header
                        if let error = store.lastError, !error.isEmpty {
                            errorBanner(error)
                        }
                        summaryGrid
                        decisionPanel
                        alertsPanel
                        sourcePanel
                        privacyFooter
                    }
                    .padding(14)
                }
                actions
                    .padding(.horizontal, 14)
                    .padding(.vertical, 12)
                    .background(.regularMaterial)
            }
        }
        .frame(width: 360, height: 500)
    }

    private var header: some View {
        HStack(alignment: .center, spacing: 10) {
            ZStack {
                Circle()
                    .fill(.white.opacity(0.18))
                    .frame(width: 38, height: 38)
                Image(systemName: "gauge.with.dots.needle.50percent")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundStyle(.white)
            }
            VStack(alignment: .leading, spacing: 4) {
                Text("BLCaptain Codex Probe")
                    .font(.headline.weight(.semibold))
                    .foregroundStyle(.white)
                Text(store.snapshot.message)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.76))
                    .lineLimit(1)
            }
            Spacer()
            Label("本地", systemImage: "lock.shield.fill")
                .font(.caption.weight(.semibold))
                .labelStyle(.titleAndIcon)
                .padding(.horizontal, 8)
                .padding(.vertical, 5)
                .foregroundStyle(Color(red: 0.05, green: 0.28, blue: 0.17))
                .background(.white.opacity(0.82), in: Capsule())
        }
    }

    private var summaryGrid: some View {
        HStack(spacing: 8) {
            MetricPill(title: "token", value: formatNumber(store.snapshot.totalTokens), accent: .cyan)
            MetricPill(title: "会话", value: "\(store.snapshot.sessionCount)", accent: .green)
            MetricPill(title: "预警", value: "\(store.snapshot.alertCount)", accent: store.snapshot.alertCount > 0 ? .red : .mint)
        }
    }

    private var decisionPanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            panelTitle("当前判断", systemImage: "bolt.circle.fill", tint: .orange)
            if let top = store.snapshot.topSession {
                HStack(alignment: .firstTextBaseline) {
                    Text(top.title)
                        .font(.callout.weight(.semibold))
                        .lineLimit(1)
                    Spacer()
                    Text(formatNumber(top.tokenDelta))
                        .font(.callout.weight(.bold))
                        .monospacedDigit()
                        .foregroundStyle(.orange)
                }
                Text(top.recommendation)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(store.snapshot.alertCount > 0 ? .red : .primary)
                    .lineLimit(2)
            } else {
                Text("暂无会话账本数据。先运行仓库示例数据流程、导入官方导出，或点击「采集一次」。")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .panelStyle()
    }

    private var alertsPanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            panelTitle("预算预警", systemImage: "exclamationmark.triangle.fill", tint: store.snapshot.alertCount > 0 ? .red : .green)
            if store.snapshot.alerts.isEmpty {
                Text("当前本地阈值没有触发预警。")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(store.snapshot.alerts.prefix(2)) { item in
                    HStack(alignment: .top, spacing: 8) {
                        SeverityDot(severity: item.severity)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(item.name)
                                .font(.subheadline.weight(.semibold))
                            Text("\(item.scope) · \(formatNumber(item.tokenDelta)) · \(String(format: "%.0f%%", item.usagePercent))")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text(item.recommendation)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(2)
                        }
                    }
                }
            }
        }
        .panelStyle()
    }

    private var sourcePanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            panelTitle("数据源可信度", systemImage: "checkmark.seal.fill", tint: .mint)
            if store.snapshot.sources.isEmpty {
                Text("暂无数据源记录。")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(activeSources.prefix(2)) { source in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(source.sourceType)
                                .font(.subheadline.weight(.semibold))
                            Text(source.missingFields.isEmpty ? "字段完整" : "缺失：\(source.missingFields.prefix(3).joined(separator: ", "))")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        Text(source.confidenceCeiling)
                            .font(.caption.weight(.semibold))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(confidenceColor(source.confidenceCeiling).opacity(0.18), in: Capsule())
                    }
                }
            }
        }
        .panelStyle()
    }

    private var activeSources: [SourceItem] {
        let enabled = store.snapshot.sources.filter { $0.enabled }
        return enabled.isEmpty ? store.snapshot.sources : enabled
    }

    private var actions: some View {
        HStack(spacing: 8) {
            Button {
                store.generateDashboardAndOpen()
            } label: {
                Label("Dashboard", systemImage: "safari")
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

            Button {
                store.runOnce()
            } label: {
                Label("采集", systemImage: "tray.and.arrow.down")
            }
            .buttonStyle(.bordered)
            .controlSize(.large)

            Button {
                store.refresh()
            } label: {
                Image(systemName: store.isLoading ? "hourglass" : "arrow.clockwise")
            }
            .buttonStyle(.bordered)
            .controlSize(.large)

            Menu {
                Button("报告目录", systemImage: "folder") { store.openReports() }
                Button("隐私报告", systemImage: "lock.doc") { store.generatePrivacyAndOpen() }
                Divider()
                Button("退出", systemImage: "xmark.circle") { NSApp.terminate(nil) }
            } label: {
                Image(systemName: "ellipsis.circle")
            }
            .menuStyle(.borderlessButton)
            .frame(width: 32)
        }
        .disabled(store.isLoading)
    }

    private var privacyFooter: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("隐私边界")
                .font(.caption.weight(.semibold))
            Text("只调用本地 CLI；不登录、不读 cookie/token/钥匙串、不抓包、不上传。")
                .font(.caption)
                .foregroundStyle(.secondary)
            Text("DB：\(store.config.dbPath)")
                .font(.caption2)
                .foregroundStyle(.tertiary)
                .lineLimit(1)
                .truncationMode(.middle)
        }
    }

    private func errorBanner(_ error: String) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            Text("CLI 未就绪")
                .font(.subheadline.weight(.semibold))
            Text(error)
                .font(.caption)
                .lineLimit(3)
        }
        .foregroundStyle(.red)
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.red.opacity(0.08), in: RoundedRectangle(cornerRadius: 8))
    }

    private func panelTitle(_ title: String, systemImage: String, tint: Color) -> some View {
        HStack(spacing: 6) {
            Image(systemName: systemImage)
                .foregroundStyle(tint)
            Text(title)
        }
        .font(.subheadline.weight(.semibold))
    }

}

struct MetricPill: View {
    let title: String
    let value: String
    let accent: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption2.weight(.semibold))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.title3.weight(.bold))
                .monospacedDigit()
                .lineLimit(1)
                .minimumScaleFactor(0.74)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 10)
        .padding(.vertical, 9)
        .background(
            LinearGradient(
                colors: [accent.opacity(0.18), Color(nsColor: .controlBackgroundColor)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            ),
            in: RoundedRectangle(cornerRadius: 10)
        )
        .overlay(alignment: .topLeading) {
            Capsule()
                .fill(accent)
                .frame(width: 28, height: 3)
                .padding(.top, 7)
                .padding(.leading, 10)
        }
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(accent.opacity(0.26), lineWidth: 0.8)
        )
    }
}

struct SeverityDot: View {
    let severity: String

    var body: some View {
        Circle()
            .fill(severityColor(severity))
            .frame(width: 9, height: 9)
            .padding(.top, 5)
    }
}

extension View {
    func panelStyle() -> some View {
        self
            .padding(11)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 10))
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(Color(nsColor: .separatorColor).opacity(0.58), lineWidth: 0.6)
            )
    }
}

func severityColor(_ severity: String) -> Color {
    switch severity {
    case "critical": return .red
    case "high": return .orange
    case "medium": return .yellow
    default: return .green
    }
}

func confidenceColor(_ confidence: String) -> Color {
    switch confidence {
    case "exact": return .green
    case "high": return .mint
    case "medium": return .yellow
    default: return .red
    }
}

func formatNumber(_ value: Int) -> String {
    let formatter = NumberFormatter()
    formatter.numberStyle = .decimal
    return formatter.string(from: NSNumber(value: value)) ?? "\(value)"
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private var popover: NSPopover!
    private var store: ProbeStore!

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)

        let config = ProbeConfig.load()
        let runner = ProbeRunner(config: config)
        store = ProbeStore(runner: runner) { [weak self] title in
            self?.statusItem.button?.title = title
        }

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem.button {
            button.title = "Codex"
            button.image = NSImage(systemSymbolName: "gauge.with.dots.needle.50percent", accessibilityDescription: "Codex Probe")
            button.imagePosition = .imageLeading
            button.action = #selector(togglePopover(_:))
            button.target = self
        }

        popover = NSPopover()
        popover.behavior = .transient
        popover.contentSize = NSSize(width: 360, height: 500)
        popover.contentViewController = NSHostingController(rootView: CodexProbePanel(store: store))

        store.refresh()
    }

    @MainActor @objc private func togglePopover(_ sender: AnyObject?) {
        guard let button = statusItem.button else { return }
        if popover.isShown {
            popover.performClose(nil)
        } else {
            popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            popover.contentViewController?.view.window?.makeKey()
        }
    }
}

let application = NSApplication.shared
let delegate = AppDelegate()
application.delegate = delegate
application.run()
