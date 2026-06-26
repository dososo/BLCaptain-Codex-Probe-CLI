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
        let appSupport = "\(home)/Library/Application Support/BLCaptain Codex Probe"
        let cwd = env["CODEX_PROBE_PROJECT_DIR"]
            ?? bundle.projectDir
            ?? appSupport
        let cli = env["CODEX_PROBE_CLI"]
            ?? bundle.cliPath
            ?? ProbeConfig.findCLI(home: home)
            ?? "codex-probe"
        let db = ProbeConfig.firstWritableFile(
            preferred: env["CODEX_PROBE_DB"] ?? bundle.dbPath ?? "\(appSupport)/codex-probe-bar.db",
            fallbackDirectories: [
                appSupport,
                "\(cwd)/.probe",
                NSTemporaryDirectory()
            ],
            filename: "codex-probe-bar.db"
        )
        let reports = ProbeConfig.firstWritableDirectory([
            env["CODEX_PROBE_REPORTS_DIR"] ?? bundle.reportsDir ?? "\(appSupport)/Reports",
            "\(appSupport)/Reports",
            "\(cwd)/reports/ledger",
            NSTemporaryDirectory() + "codex-probe-reports"
        ])
        let range = env["CODEX_PROBE_RANGE"]
            ?? bundle.range
            ?? "7d"
        return ProbeConfig(cliPath: cli, dbPath: db, reportsDir: reports, range: range, workingDirectory: cwd)
    }

    private static func findCLI(home: String) -> String? {
        let candidates = [
            "\(home)/Library/Application Support/BLCaptain Codex Probe/.venv/bin/codex-probe",
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
        if canWriteDirectory(preferredDir, manager: manager), canWriteDatabaseFiles(preferred, manager: manager) {
            return preferred
        }
        for directory in fallbackDirectories {
            let candidate = URL(fileURLWithPath: directory).appendingPathComponent(filename).path
            if canWriteDirectory(directory, manager: manager), canWriteDatabaseFiles(candidate, manager: manager) {
                return candidate
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

    private static func canWriteDatabaseFiles(_ path: String, manager: FileManager) -> Bool {
        [path, "\(path)-journal", "\(path)-wal", "\(path)-shm"].allSatisfy { candidate in
            guard manager.fileExists(atPath: candidate) else { return true }
            guard let handle = FileHandle(forUpdatingAtPath: candidate) else { return false }
            try? handle.close()
            return true
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
        VStack(spacing: 0) {
            header
            VStack(spacing: 8) {
                summaryGrid
                if let error = store.lastError, !error.isEmpty {
                    errorBanner(error)
                } else {
                    decisionPanel
                    alertsPanel
                    sourcePanel
                }
            }
            .padding(.horizontal, 12)
            .padding(.top, 10)
            .padding(.bottom, 10)
            footer
        }
        .frame(width: 372, height: 520)
        .background(
            LinearGradient(
                colors: [
                    Color(red: 0.96, green: 0.98, blue: 1.00),
                    Color(red: 0.91, green: 0.95, blue: 0.97)
                ],
                startPoint: .top,
                endPoint: .bottom
            )
        )
    }

    private var header: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(red: 0.03, green: 0.09, blue: 0.20),
                    Color(red: 0.02, green: 0.37, blue: 0.47),
                    Color(red: 0.06, green: 0.54, blue: 0.37)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(.white.opacity(0.16))
                    .frame(height: 1)
            }

            HStack(alignment: .center, spacing: 11) {
                ZStack {
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(.white.opacity(0.16))
                        .frame(width: 46, height: 46)
                    Image(systemName: "gauge.with.dots.needle.50percent")
                        .font(.system(size: 19, weight: .semibold))
                        .foregroundStyle(.white)
                }
                VStack(alignment: .leading, spacing: 5) {
                    Text("BLCaptain Codex Probe")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundStyle(.white)
                        .lineLimit(1)
                    HStack(spacing: 5) {
                        Image(systemName: store.isLoading ? "hourglass" : "checkmark.seal.fill")
                            .font(.system(size: 10, weight: .semibold))
                        Text(store.isLoading ? "正在读取本地账本" : store.snapshot.message)
                            .lineLimit(1)
                    }
                    .font(.caption.weight(.medium))
                    .foregroundStyle(.white.opacity(0.76))
                }
                Spacer()
                Label("本地", systemImage: "lock.shield.fill")
                    .font(.caption.weight(.semibold))
                    .labelStyle(.titleAndIcon)
                    .padding(.horizontal, 9)
                    .padding(.vertical, 6)
                    .foregroundStyle(Color(red: 0.04, green: 0.32, blue: 0.20))
                    .background(.white.opacity(0.86), in: Capsule())
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 16)
        }
        .frame(height: 88)
    }

    private var summaryGrid: some View {
        HStack(spacing: 8) {
            MetricTile(title: "Token", value: formatCompactNumber(store.snapshot.totalTokens), caption: store.config.range, tint: Color(red: 0.00, green: 0.48, blue: 0.82))
            MetricTile(title: "会话", value: "\(store.snapshot.sessionCount)", caption: "账本", tint: Color(red: 0.05, green: 0.62, blue: 0.39))
            MetricTile(title: "预警", value: "\(store.snapshot.alertCount)", caption: riskLabel, tint: store.snapshot.alertCount > 0 ? Color(red: 0.96, green: 0.25, blue: 0.30) : Color(red: 0.05, green: 0.62, blue: 0.39))
        }
        .frame(height: 66)
    }

    private var decisionPanel: some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack {
                panelTitle("当前判断", systemImage: "bolt.fill", tint: Color(red: 1.00, green: 0.51, blue: 0.16))
                Spacer()
                RiskBadge(text: store.snapshot.alertCount > 0 ? "建议停止" : "可继续", color: store.snapshot.alertCount > 0 ? .red : .green)
            }
            if let top = store.snapshot.topSession {
                HStack(alignment: .firstTextBaseline) {
                    Text(top.title)
                        .font(.system(size: 14, weight: .semibold))
                        .lineLimit(1)
                    Spacer()
                    Text(formatCompactNumber(top.tokenDelta))
                        .font(.system(size: 15, weight: .bold))
                        .monospacedDigit()
                        .foregroundStyle(Color(red: 0.93, green: 0.35, blue: 0.12))
                }
                Text(top.recommendation)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(store.snapshot.alertCount > 0 ? Color(red: 0.88, green: 0.10, blue: 0.16) : .secondary)
                    .lineLimit(2)
            } else {
                Text("暂无会话账本数据。点击「采集」或先导入官方导出。")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
        }
        .panelStyle(height: 82)
    }

    private var alertsPanel: some View {
        VStack(alignment: .leading, spacing: 7) {
            panelTitle("预算预警", systemImage: "exclamationmark.triangle.fill", tint: store.snapshot.alertCount > 0 ? Color(red: 0.96, green: 0.25, blue: 0.30) : .green)
            if store.snapshot.alerts.isEmpty {
                Text("当前没有触发本地预警。")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            } else {
                ForEach(store.snapshot.alerts.prefix(2)) { item in
                    AlertRow(item: item)
                }
            }
        }
        .panelStyle(height: 100)
    }

    private var sourcePanel: some View {
        VStack(alignment: .leading, spacing: 7) {
            panelTitle("数据源可信度", systemImage: "checkmark.seal.fill", tint: Color(red: 0.00, green: 0.70, blue: 0.62))
            if store.snapshot.sources.isEmpty {
                Text("暂无数据源记录。")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(activeSources.prefix(1)) { source in
                    HStack(alignment: .center, spacing: 10) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(source.sourceType)
                                .font(.system(size: 13, weight: .semibold))
                                .lineLimit(1)
                            Text(source.missingFields.isEmpty ? "字段完整" : "缺失：\(source.missingFields.prefix(3).joined(separator: ", "))")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(1)
                        }
                        Spacer()
                        Text(source.confidenceCeiling)
                            .font(.caption.weight(.semibold))
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .foregroundStyle(confidenceColor(source.confidenceCeiling))
                            .background(confidenceColor(source.confidenceCeiling).opacity(0.15), in: Capsule())
                    }
                }
            }
        }
        .panelStyle(height: 70)
    }

    private var activeSources: [SourceItem] {
        let enabled = store.snapshot.sources.filter { $0.enabled }
        return enabled.isEmpty ? store.snapshot.sources : enabled
    }

    private var footer: some View {
        VStack(spacing: 8) {
            HStack(spacing: 8) {
                Button {
                    store.generateDashboardAndOpen()
                } label: {
                    Label("Dashboard", systemImage: "safari")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(ProbeActionButtonStyle(kind: .primary))
                .help("生成并打开本地 Dashboard")

                Button {
                    store.runOnce()
                } label: {
                    Label("采集", systemImage: "tray.and.arrow.down")
                        .frame(width: 78)
                }
                .buttonStyle(ProbeActionButtonStyle(kind: .secondary))
                .help("从本地数据源采集一次快照")

                Button {
                    store.refresh()
                } label: {
                    Image(systemName: store.isLoading ? "hourglass" : "arrow.clockwise")
                        .frame(width: 34)
                }
                .buttonStyle(ProbeActionButtonStyle(kind: .icon))
                .help("刷新当前面板")

                Menu {
                    Button("报告目录", systemImage: "folder") { store.openReports() }
                    Button("隐私报告", systemImage: "lock.doc") { store.generatePrivacyAndOpen() }
                    Divider()
                    Button("退出", systemImage: "xmark.circle") { NSApp.terminate(nil) }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .frame(width: 30)
                }
                .menuStyle(.borderlessButton)
                .help("更多操作")
            }
            .disabled(store.isLoading)

            HStack(spacing: 5) {
                Image(systemName: "lock.fill")
                    .font(.system(size: 9, weight: .semibold))
                Text("只调用本地 CLI，不读 cookie/token/钥匙串，不上传")
                    .lineLimit(1)
                    .minimumScaleFactor(0.82)
            }
            .font(.caption2.weight(.medium))
            .foregroundStyle(.secondary)
        }
        .padding(.horizontal, 12)
        .padding(.top, 10)
        .padding(.bottom, 9)
        .background(.thinMaterial)
        .overlay(alignment: .top) {
            Rectangle()
                .fill(Color(nsColor: .separatorColor).opacity(0.40))
                .frame(height: 0.5)
        }
    }

    private func errorBanner(_ error: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "exclamationmark.octagon.fill")
                .foregroundStyle(.red)
            VStack(alignment: .leading, spacing: 4) {
                Text("CLI 未就绪")
                    .font(.subheadline.weight(.semibold))
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(5)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(Color.red.opacity(0.08), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(Color.red.opacity(0.16), lineWidth: 1)
        )
    }

    private func panelTitle(_ title: String, systemImage: String, tint: Color) -> some View {
        HStack(spacing: 6) {
            Image(systemName: systemImage)
                .foregroundStyle(tint)
            Text(title)
        }
        .font(.subheadline.weight(.semibold))
    }

    private var riskLabel: String {
        store.snapshot.alertCount > 0 ? "需处理" : "健康"
    }
}

struct MetricTile: View {
    let title: String
    let value: String
    let caption: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Capsule()
                .fill(tint)
                .frame(width: 27, height: 3)
            Text(title)
                .font(.caption2.weight(.semibold))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .monospacedDigit()
                .lineLimit(1)
                .minimumScaleFactor(0.72)
            Text(caption)
                .font(.caption2)
                .foregroundStyle(.tertiary)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 11)
        .padding(.vertical, 8)
        .background(
            LinearGradient(
                colors: [tint.opacity(0.14), Color.white.opacity(0.78)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            ),
            in: RoundedRectangle(cornerRadius: 13, style: .continuous)
        )
        .overlay(roundedStroke(tint.opacity(0.22), radius: 13))
    }
}

struct RiskBadge: View {
    let text: String
    let color: Color

    var body: some View {
        Text(text)
            .font(.caption2.weight(.bold))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .foregroundStyle(color)
            .background(color.opacity(0.12), in: Capsule())
    }
}

struct AlertRow: View {
    let item: AlertItem

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Circle()
                .fill(severityColor(item.severity))
                .frame(width: 8, height: 8)
                .padding(.top, 5)
            VStack(alignment: .leading, spacing: 2) {
                HStack(alignment: .firstTextBaseline) {
                    Text(item.name)
                        .font(.system(size: 12, weight: .semibold))
                        .lineLimit(1)
                    Spacer(minLength: 8)
                    RiskBadge(text: alertActionText(item), color: severityColor(item.severity))
                }
                Text(alertUsageText(item))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
        }
    }
}

struct ProbeActionButtonStyle: ButtonStyle {
    enum Kind {
        case primary
        case secondary
        case icon
    }

    let kind: Kind

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .semibold))
            .foregroundStyle(foreground)
            .padding(.horizontal, kind == .icon ? 8 : 12)
            .frame(height: 36)
            .background {
                background(isPressed: configuration.isPressed)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            }
            .overlay(roundedStroke(stroke, radius: 12))
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
    }

    private var foreground: Color {
        switch kind {
        case .primary: return .white
        case .secondary: return Color(red: 0.19, green: 0.25, blue: 0.32)
        case .icon: return Color(red: 0.29, green: 0.34, blue: 0.40)
        }
    }

    private var stroke: Color {
        switch kind {
        case .primary: return Color.white.opacity(0.18)
        default: return Color.black.opacity(0.07)
        }
    }

    @ViewBuilder
    private func background(isPressed: Bool) -> some View {
        switch kind {
        case .primary:
            LinearGradient(
                colors: [
                    Color(red: 0.02, green: 0.46, blue: 0.95).opacity(isPressed ? 0.86 : 1),
                    Color(red: 0.00, green: 0.68, blue: 0.72).opacity(isPressed ? 0.86 : 1)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        case .secondary:
            Color.white.opacity(isPressed ? 0.58 : 0.82)
        case .icon:
            Color.white.opacity(isPressed ? 0.50 : 0.72)
        }
    }
}

extension View {
    func panelStyle(height: CGFloat) -> some View {
        self
            .padding(12)
            .frame(height: height)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.white.opacity(0.78), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(roundedStroke(Color.black.opacity(0.07), radius: 14))
    }
}

func roundedStroke(_ color: Color, radius: CGFloat) -> some View {
    RoundedRectangle(cornerRadius: radius, style: .continuous)
        .stroke(color, lineWidth: 1)
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

func formatCompactNumber(_ value: Int) -> String {
    let absolute = abs(value)
    let sign = value < 0 ? "-" : ""
    if absolute >= 1_000_000_000 {
        return "\(sign)\(formatOneDecimal(Double(absolute) / 1_000_000_000))B"
    }
    if absolute >= 1_000_000 {
        return "\(sign)\(formatOneDecimal(Double(absolute) / 1_000_000))M"
    }
    if absolute >= 10_000 {
        return "\(sign)\(formatOneDecimal(Double(absolute) / 1_000))K"
    }
    return formatNumber(value)
}

func alertActionText(_ item: AlertItem) -> String {
    switch item.severity {
    case "critical": return "建议拆分"
    case "high": return "先降配"
    case "medium": return "需关注"
    default: return "观察"
    }
}

func alertUsageText(_ item: AlertItem) -> String {
    if item.scope == "context" {
        return "上下文峰值 \(formatOneDecimal(Double(item.tokenDelta)))%，需要拆分处理"
    }
    return "已用 \(formatCompactNumber(item.tokenDelta))，触发本地预警"
}

private func formatOneDecimal(_ value: Double) -> String {
    let rounded = (value * 10).rounded() / 10
    if rounded == rounded.rounded() {
        return "\(Int(rounded))"
    }
    return String(format: "%.1f", rounded)
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
            self?.statusItem.button?.toolTip = "BLCaptain Codex Probe: \(title)"
        }

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let button = statusItem.button {
            button.title = ""
            button.image = NSImage(systemSymbolName: "gauge.with.dots.needle.50percent", accessibilityDescription: "Codex Probe")
            button.imagePosition = .imageOnly
            button.toolTip = "BLCaptain Codex Probe"
            button.action = #selector(togglePopover(_:))
            button.target = self
        }

        popover = NSPopover()
        popover.behavior = .transient
        popover.contentSize = NSSize(width: 372, height: 520)
        popover.contentViewController = NSHostingController(rootView: CodexProbePanel(store: store))

        store.refresh()
        if ProcessInfo.processInfo.environment["CODEX_PROBE_OPEN_ON_LAUNCH"] == "1" {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { [weak self] in
                self?.togglePopover(nil)
            }
        }
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
