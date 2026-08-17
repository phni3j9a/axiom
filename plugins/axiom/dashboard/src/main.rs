mod git;
mod model;
mod trace;

use std::convert::Infallible;
use std::net::{IpAddr, Ipv4Addr, SocketAddr};
use std::path::PathBuf;
use std::process::Command as ProcessCommand;
use std::sync::Arc;
use std::time::Duration;

use anyhow::{bail, Context, Result};
use axum::extract::State;
use axum::http::{header, HeaderValue, StatusCode};
use axum::response::sse::{Event, KeepAlive, Sse};
use axum::response::{Html, IntoResponse, Response};
use axum::routing::get;
use axum::{Json, Router};
use clap::{Args, Parser, Subcommand};
use futures_util::StreamExt;
use model::DashboardSnapshot;
use tokio::net::TcpListener;
use tokio::sync::{broadcast, RwLock};
use tokio_stream::wrappers::BroadcastStream;
use trace::{build_snapshot, build_snapshot_cached, SnapshotCache, SnapshotOptions};

const INDEX_HTML: &str = include_str!("../web/dist/index.html");
const APP_JS: &str = include_str!("../web/dist/app.js");
const STYLES_CSS: &str = include_str!("../web/dist/styles.css");
const REACT_JS: &str = include_str!("../web/dist/vendor/react.production.min.js");
const REACT_DOM_JS: &str = include_str!("../web/dist/vendor/react-dom.production.min.js");

#[derive(Debug, Parser)]
#[command(
    name = "axiom-dashboard",
    version,
    about = "Local read-only observability for Axiom and Codex Rollout Trace"
)]
struct Cli {
    #[command(subcommand)]
    command: Option<Command>,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Serve the local dashboard.
    Serve(ServeArgs),
    /// Check trace and repository discovery without starting a server.
    Doctor(CommonArgs),
    /// Print the current dashboard snapshot as JSON.
    Snapshot(CommonArgs),
}

#[derive(Debug, Clone, Args)]
struct CommonArgs {
    /// Root written by CODEX_ROLLOUT_TRACE_ROOT.
    #[arg(long, env = "CODEX_ROLLOUT_TRACE_ROOT")]
    trace_root: Option<PathBuf>,
    /// Repository to inspect with read-only Git commands.
    #[arg(long)]
    repo: Option<PathBuf>,
    /// Maximum number of trace sessions to retain in the read model.
    #[arg(long, default_value_t = 30)]
    max_sessions: usize,
}

#[derive(Debug, Clone, Args)]
struct ServeArgs {
    #[command(flatten)]
    common: CommonArgs,
    /// Bind address. Loopback is required unless --allow-remote is explicitly set.
    #[arg(long, default_value = "127.0.0.1")]
    bind: IpAddr,
    /// Preferred port. The next available port is selected when occupied.
    #[arg(long, default_value_t = 43127)]
    port: u16,
    /// Open the dashboard in the default browser.
    #[arg(long)]
    open: bool,
    /// Permit a non-loopback bind. The dashboard has no authentication.
    #[arg(long)]
    allow_remote: bool,
    /// Snapshot refresh interval in milliseconds.
    #[arg(long, default_value_t = 1250)]
    refresh_ms: u64,
}

#[derive(Clone)]
struct AppState {
    snapshot: Arc<RwLock<DashboardSnapshot>>,
    updates: broadcast::Sender<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command.unwrap_or_else(|| Command::Serve(default_serve_args())) {
        Command::Serve(args) => serve(args).await,
        Command::Doctor(args) => doctor(args),
        Command::Snapshot(args) => snapshot(args),
    }
}

fn default_serve_args() -> ServeArgs {
    ServeArgs {
        common: CommonArgs {
            trace_root: None,
            repo: None,
            max_sessions: 30,
        },
        bind: IpAddr::V4(Ipv4Addr::LOCALHOST),
        port: 43127,
        open: false,
        allow_remote: false,
        refresh_ms: 1250,
    }
}

fn snapshot_options(args: &CommonArgs) -> SnapshotOptions {
    SnapshotOptions {
        trace_root: args.trace_root.clone().unwrap_or_else(default_trace_root),
        repo: args.repo.clone(),
        max_sessions: args.max_sessions.max(1),
    }
}

fn doctor(args: CommonArgs) -> Result<()> {
    let options = snapshot_options(&args);
    let snapshot = build_snapshot(&options);
    println!("Axiom Dashboard doctor");
    println!("  trace root : {}", snapshot.trace_root);
    println!(
        "  repository : {}",
        snapshot.repo.as_deref().unwrap_or("not detected")
    );
    println!("  sessions   : {}", snapshot.sessions.len());
    if snapshot.warnings.is_empty() {
        println!("  status     : ready");
    } else {
        println!("  status     : attention");
        for warning in snapshot.warnings {
            println!("  warning    : {warning}");
        }
    }
    Ok(())
}

fn snapshot(args: CommonArgs) -> Result<()> {
    let options = snapshot_options(&args);
    let snapshot = build_snapshot(&options);
    println!("{}", serde_json::to_string_pretty(&snapshot)?);
    Ok(())
}

async fn serve(args: ServeArgs) -> Result<()> {
    if !args.bind.is_loopback() && !args.allow_remote {
        bail!(
            "refusing to bind to {} without --allow-remote; the dashboard has no authentication",
            args.bind
        );
    }

    let options = snapshot_options(&args.common);
    let mut cache = SnapshotCache::default();
    let initial = build_snapshot_cached(&options, &mut cache);
    let (updates, _) = broadcast::channel(32);
    let state = AppState {
        snapshot: Arc::new(RwLock::new(initial)),
        updates,
    };

    spawn_refresh_loop(
        state.clone(),
        options,
        cache,
        Duration::from_millis(args.refresh_ms.max(250)),
    );

    let app = Router::new()
        .route("/", get(index))
        .route("/app.js", get(app_js))
        .route("/styles.css", get(styles_css))
        .route("/vendor/react.production.min.js", get(react_js))
        .route(
            "/vendor/react-dom.production.min.js",
            get(react_dom_js),
        )
        .route("/api/health", get(health))
        .route("/api/state", get(api_state))
        .route("/api/events", get(api_events))
        .fallback(not_found)
        .with_state(state);

    let (listener, address) = bind_with_fallback(args.bind, args.port).await?;
    let url = format!("http://{address}");
    println!("Axiom Dashboard: {url}");
    println!("Trace root: {}", default_or_display(args.common.trace_root.as_ref()));
    println!("Read-only repository observation; no telemetry; Ctrl-C to stop.");

    if args.open {
        if let Err(error) = open_browser(&url) {
            eprintln!("Could not open the browser automatically: {error:#}");
        }
    }

    axum::serve(listener, app)
        .with_graceful_shutdown(async {
            let _ = tokio::signal::ctrl_c().await;
        })
        .await
        .context("dashboard server failed")?;
    Ok(())
}

fn spawn_refresh_loop(
    state: AppState,
    options: SnapshotOptions,
    mut cache: SnapshotCache,
    interval: Duration,
) {
    tokio::spawn(async move {
        let mut previous = Vec::new();
        loop {
            let options_for_build = options.clone();
            let next = tokio::task::block_in_place(|| {
                build_snapshot_cached(&options_for_build, &mut cache)
            });
            let serialized = snapshot_material_bytes(&next);
            if serialized != previous {
                previous = serialized;
                *state.snapshot.write().await = next;
                let _ = state.updates.send("refresh".to_owned());
            }
            tokio::time::sleep(interval).await;
        }
    });
}

fn snapshot_material_bytes(snapshot: &DashboardSnapshot) -> Vec<u8> {
    let mut value = serde_json::to_value(snapshot).unwrap_or_default();
    if let Some(object) = value.as_object_mut() {
        object.insert("generated_at_unix_ms".to_owned(), serde_json::Value::from(0));
    }
    if let Some(sessions) = value.get_mut("sessions").and_then(|value| value.as_array_mut()) {
        for session in sessions {
            if session.get("ended_at_unix_ms").is_some_and(|value| value.is_null()) {
                if let Some(object) = session.as_object_mut() {
                    object.insert("duration_ms".to_owned(), serde_json::Value::from(0));
                }
            }
            if let Some(agents) = session.get_mut("agents").and_then(|value| value.as_array_mut()) {
                for agent in agents {
                    if agent.get("ended_at_unix_ms").is_some_and(|value| value.is_null()) {
                        if let Some(object) = agent.as_object_mut() {
                            object.insert("duration_ms".to_owned(), serde_json::Value::from(0));
                        }
                    }
                }
            }
        }
    }
    serde_json::to_vec(&value).unwrap_or_default()
}

async fn bind_with_fallback(bind: IpAddr, preferred_port: u16) -> Result<(TcpListener, SocketAddr)> {
    let mut last_error = None;
    for offset in 0..20u16 {
        let port = preferred_port.saturating_add(offset);
        let address = SocketAddr::new(bind, port);
        match TcpListener::bind(address).await {
            Ok(listener) => {
                let actual = listener.local_addr()?;
                return Ok((listener, actual));
            }
            Err(error) => last_error = Some(error),
        }
    }
    Err(last_error
        .map(anyhow::Error::from)
        .unwrap_or_else(|| anyhow::anyhow!("no dashboard port was attempted")))
}

async fn index() -> Html<&'static str> {
    Html(INDEX_HTML)
}

async fn app_js() -> Response {
    static_response("application/javascript; charset=utf-8", APP_JS)
}

async fn styles_css() -> Response {
    static_response("text/css; charset=utf-8", STYLES_CSS)
}

async fn react_js() -> Response {
    static_response("application/javascript; charset=utf-8", REACT_JS)
}

async fn react_dom_js() -> Response {
    static_response("application/javascript; charset=utf-8", REACT_DOM_JS)
}

fn static_response(content_type: &'static str, body: &'static str) -> Response {
    let mut response = body.into_response();
    response
        .headers_mut()
        .insert(header::CONTENT_TYPE, HeaderValue::from_static(content_type));
    response.headers_mut().insert(
        header::CACHE_CONTROL,
        HeaderValue::from_static("no-store, max-age=0"),
    );
    response
}

async fn health() -> Json<serde_json::Value> {
    Json(serde_json::json!({"status": "ok", "version": env!("CARGO_PKG_VERSION")}))
}

async fn api_state(State(state): State<AppState>) -> Json<DashboardSnapshot> {
    Json(state.snapshot.read().await.clone())
}

async fn api_events(
    State(state): State<AppState>,
) -> Sse<impl futures_util::Stream<Item = std::result::Result<Event, Infallible>>> {
    let stream = BroadcastStream::new(state.updates.subscribe()).filter_map(|message| async move {
        match message {
            Ok(message) => Some(Ok::<Event, Infallible>(Event::default().event("refresh").data(message))),
            Err(_) => None,
        }
    });
    Sse::new(stream).keep_alive(
        KeepAlive::new()
            .interval(Duration::from_secs(15))
            .text("keep-alive"),
    )
}

async fn not_found() -> impl IntoResponse {
    (StatusCode::NOT_FOUND, "Not found")
}

fn default_trace_root() -> PathBuf {
    if let Ok(value) = std::env::var("CODEX_ROLLOUT_TRACE_ROOT") {
        if !value.trim().is_empty() {
            return PathBuf::from(value);
        }
    }
    home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".codex")
        .join("axiom-traces")
}

fn home_dir() -> Option<PathBuf> {
    std::env::var_os("HOME")
        .map(PathBuf::from)
        .or_else(|| std::env::var_os("USERPROFILE").map(PathBuf::from))
}

fn default_or_display(value: Option<&PathBuf>) -> String {
    value
        .cloned()
        .unwrap_or_else(default_trace_root)
        .display()
        .to_string()
}

fn open_browser(url: &str) -> Result<()> {
    #[cfg(target_os = "macos")]
    let status = ProcessCommand::new("open").arg(url).status()?;

    #[cfg(target_os = "windows")]
    let status = ProcessCommand::new("cmd")
        .args(["/C", "start", "", url])
        .status()?;

    #[cfg(all(unix, not(target_os = "macos")))]
    let status = ProcessCommand::new("xdg-open").arg(url).status()?;

    #[cfg(not(any(unix, target_os = "windows")))]
    let status = {
        let _ = url;
        bail!("automatic browser opening is not supported on this platform")
    };

    if status.success() {
        Ok(())
    } else {
        bail!("browser opener exited with {status}")
    }
}
