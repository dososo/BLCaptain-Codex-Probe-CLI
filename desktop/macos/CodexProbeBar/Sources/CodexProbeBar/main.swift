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
        let cli = env["CODEX_PROBE_CLI"]
            ?? bundle.cliPath
            ?? ProbeConfig.findCLI(home: home)
            ?? "codex-probe"
        let db = env["CODEX_PROBE_DB"]
            ?? bundle.dbPath
            ?? "\(home)/.codex-probe/probe.db"
        let reports = env["CODEX_PROBE_REPORTS_DIR"]
            ?? bundle.reportsDir
            ?? "\(home)/CodexProbeReports/ledger"
        let range = env["CODEX_PROBE_RANGE"]
            ?? bundle.range
            ?? "7d"
        let cwd = env["CODEX_PROBE_PROJECT_DIR"]
            ?? bundle.projectDir
            ?? home
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
    let confidenceCeiling: String
    let snapshotCount: Int
    let missingFields: [String]
    let diagnosis: String

    var id: String { sourceType }

    enum CodingKeys: String, CodingKey {
        case sourceType = "source_type"
        case confidenceCeiling = "confidence_ceiling"
        case snapshotCount = "snapshot_count"
        case missingFields = "missing_fields"
        case diagnosis
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
    }

    func run(_ args: [String]) throws -> CommandResult {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: config.cliPath)
        process.arguments = args
        process.currentDirectoryURL = URL(fileURLWithPath: config.workingDirectory)
        process.environment = ProcessInfo.processInfo.environment.merging([
            "PYTHONDONTWRITEBYTECODE": "1"
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

    func json<T: Decodable>(_ type: T.Type, _ command: [String]) throws -> T {
        let result = try run(["--db", config.dbPath, "--json"] + command)
        guard result.status == 0 else {
            throw RuntimeError(result.stderr.isEmpty ? result.stdout : result.stderr)
        }
        return try JSONDecoder().decode(T.self, from: Data(result.stdout.utf8))
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
                    self.statusTitle(alerts.alertCount > 0 ? "Codex !" : "Codex OK")
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                    self.lastError = error.localizedDescription.trimmingCharacters(in: .whitespacesAndNewlines)
                    self.snapshot.message = "无法读取本地账本"
                    self.statusTitle("Codex ?")
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
        VStack(alignment: .leading, spacing: 14) {
            header
            if let error = store.lastError, !error.isEmpty {
                errorBanner(error)
            }
            summaryGrid
            decisionPanel
            alertsPanel
            sourcePanel
            actions
            privacyFooter
        }
        .padding(18)
        .frame(width: 430)
        .background(Color(nsColor: .windowBackgroundColor))
    }

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text("BLCaptain Codex Probe")
                    .font(.title3.weight(.semibold))
                Text(store.snapshot.message)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Label("本地", systemImage: "lock.shield")
                .font(.caption.weight(.semibold))
                .labelStyle(.titleAndIcon)
                .padding(.horizontal, 8)
                .padding(.vertical, 5)
                .background(Color.green.opacity(0.14), in: Capsule())
        }
    }

    private var summaryGrid: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
            StatCard(title: "token delta", value: formatNumber(store.snapshot.totalTokens), detail: "本地账本范围 \(store.config.range)")
            StatCard(title: "会话数", value: "\(store.snapshot.sessionCount)", detail: "已导入会话")
            StatCard(title: "预警", value: "\(store.snapshot.alertCount)", detail: store.snapshot.alertCount > 0 ? "建议处理" : "暂无本地预警")
            StatCard(title: "更新", value: timeText(store.snapshot.lastUpdated), detail: "系统本地时间")
        }
    }

    private var decisionPanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("当前判断")
                .font(.headline)
            if let top = store.snapshot.topSession {
                Text("最耗会话是「\(top.title)」，token delta \(formatNumber(top.tokenDelta))。")
                    .font(.subheadline)
                Text(top.recommendation)
                    .font(.callout.weight(.semibold))
                    .foregroundStyle(store.snapshot.alertCount > 0 ? .red : .primary)
            } else {
                Text("暂无会话账本数据。先运行仓库示例数据流程、导入官方导出，或点击「采集一次」。")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .panelStyle()
    }

    private var alertsPanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("预算预警")
                .font(.headline)
            if store.snapshot.alerts.isEmpty {
                Text("当前本地阈值没有触发预警。")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(store.snapshot.alerts.prefix(3)) { item in
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
            Text("数据源可信度")
                .font(.headline)
            if store.snapshot.sources.isEmpty {
                Text("暂无数据源记录。")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(store.snapshot.sources.prefix(3)) { source in
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

    private var actions: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
            ActionButton(title: store.isLoading ? "处理中" : "刷新", systemImage: "arrow.clockwise") {
                store.refresh()
            }
            ActionButton(title: "采集一次", systemImage: "tray.and.arrow.down") {
                store.runOnce()
            }
            ActionButton(title: "打开 Dashboard", systemImage: "safari") {
                store.generateDashboardAndOpen()
            }
            ActionButton(title: "报告目录", systemImage: "folder") {
                store.openReports()
            }
            ActionButton(title: "隐私报告", systemImage: "lock.doc") {
                store.generatePrivacyAndOpen()
            }
            ActionButton(title: "退出", systemImage: "xmark.circle") {
                NSApp.terminate(nil)
            }
        }
        .disabled(store.isLoading)
    }

    private var privacyFooter: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("隐私边界")
                .font(.caption.weight(.semibold))
            Text("只调用本地 codex-probe CLI；不登录、不读 cookie、不碰 token/钥匙串、不抓包、不上传。")
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
            Text("无法读取 CLI")
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

    private func timeText(_ date: Date?) -> String {
        guard let date else { return "未刷新" }
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        formatter.dateStyle = .none
        return formatter.string(from: date)
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let detail: String

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.title2.weight(.bold))
                .monospacedDigit()
            Text(detail)
                .font(.caption2)
                .foregroundStyle(.secondary)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color(nsColor: .separatorColor), lineWidth: 0.5)
        )
    }
}

struct ActionButton: View {
    let title: String
    let systemImage: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Label(title, systemImage: systemImage)
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.bordered)
        .controlSize(.large)
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
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 8))
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color(nsColor: .separatorColor), lineWidth: 0.5)
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
        popover.contentSize = NSSize(width: 430, height: 650)
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
