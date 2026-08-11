from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yaml


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs.jsonl"
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"

st.set_page_config(
    page_title="AI Observability Control Center",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1500px;}
    [data-testid="stMetric"] {background: rgba(128,128,128,.06); border: 1px solid rgba(128,128,128,.18); border-radius: 12px; padding: 12px 14px;}
    [data-testid="stMetricLabel"] {font-size: .78rem; color: #7b8495;}
    [data-testid="stMetricValue"] {font-size: 1.65rem; font-weight: 700;}
    .dashboard-kicker {color:#657085; font-size:.78rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase;}
    .dashboard-title {font-size:2rem; font-weight:760; line-height:1.15; margin:.2rem 0;}
    .dashboard-meta {color:#7b8495; font-size:.9rem;}
    .status-ok, .status-bad {display:inline-block; padding:.28rem .65rem; border-radius:999px; font-size:.78rem; font-weight:700;}
    .status-ok {background:#dcfce7; color:#166534;}
    .status-bad {background:#fee2e2; color:#991b1b;}
    .panel-heading {font-size:1rem; font-weight:720; margin-bottom:0;}
    .panel-subtitle {font-size:.76rem; color:#7b8495; margin-bottom:.45rem;}
    div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=30)
def load_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]


@st.cache_data(ttl=30)
def load_logs() -> tuple[pd.DataFrame, int]:
    if not LOG_PATH.exists():
        return pd.DataFrame(), 0
    rows: list[dict] = []
    rejected = 0
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rejected += 1
    frame = pd.DataFrame(rows)
    if not frame.empty and "ts" in frame:
        frame["ts"] = pd.to_datetime(frame["ts"], utc=True, errors="coerce")
        frame = frame.dropna(subset=["ts"])
    return frame, rejected


def panel_config(config: dict, panel_id: str) -> dict:
    return next(panel for panel in config["panels"] if panel["id"] == panel_id)


def compact_chart(fig, *, percent: bool = False) -> None:
    fig.update_layout(
        height=220,
        margin=dict(l=8, r=8, t=12, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.12, x=0),
        hovermode="x unified",
        font=dict(size=11),
    )
    fig.update_xaxes(title=None, gridcolor="rgba(128,128,128,.12)")
    fig.update_yaxes(title=None, gridcolor="rgba(128,128,128,.12)")
    if percent:
        fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def heading(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="panel-heading">{title}</div><div class="panel-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


config = load_config()
df, rejected_lines = load_logs()

with st.sidebar:
    st.markdown("### View controls")
    options = [15, 30, 60]
    default_window = config["time_range_minutes"]
    window_minutes = st.selectbox(
        "Time range",
        options,
        index=options.index(default_window),
        format_func=lambda value: f"Last {value} minutes",
    )
    auto_refresh = st.toggle("Auto refresh", value=True)
    st.caption(f"Refresh interval: {config['refresh_seconds']} seconds")
    st.divider()
    st.caption("SOURCE")
    st.code("data/logs.jsonl", language=None)
    st.caption("Dashboard contract: config/dashboard.yaml")

if auto_refresh:
    st_autorefresh(
        interval=config["refresh_seconds"] * 1000,
        limit=None,
        key="dashboard-data-refresh",
    )

now = pd.Timestamp.now(tz="UTC")
cutoff = now - pd.Timedelta(minutes=window_minutes)
window_df = df[df["ts"] >= cutoff].copy() if not df.empty and "ts" in df else pd.DataFrame()

if window_df.empty and not df.empty:
    latest = df["ts"].max()
    cutoff = latest - pd.Timedelta(minutes=window_minutes)
    window_df = df[df["ts"] >= cutoff].copy()
    data_mode = "latest available data"
else:
    data_mode = "live window"

responses = window_df[window_df.get("event", pd.Series(dtype=str)) == "response_sent"].copy()
requests = window_df[window_df.get("event", pd.Series(dtype=str)) == "request_received"].copy()
failures = window_df[window_df.get("event", pd.Series(dtype=str)) == "request_failed"].copy()

for frame in (responses, requests, failures):
    if not frame.empty:
        frame["minute"] = frame["ts"].dt.floor("min")

latency_cfg = panel_config(config, "latency")
traffic_cfg = panel_config(config, "traffic")
errors_cfg = panel_config(config, "errors")
cost_cfg = panel_config(config, "cost")
tokens_cfg = panel_config(config, "tokens")
quality_cfg = panel_config(config, "quality")

p50 = responses["latency_ms"].quantile(.50) if "latency_ms" in responses else 0.0
p95 = responses["latency_ms"].quantile(.95) if "latency_ms" in responses else 0.0
p99 = responses["latency_ms"].quantile(.99) if "latency_ms" in responses else 0.0
request_count = len(requests)
error_count = len(failures)
error_rate = (error_count / request_count * 100) if request_count else 0.0
duration_minutes = max(window_minutes, 1)
request_rate = request_count / duration_minutes
total_cost = float(responses.get("cost_usd", pd.Series(dtype=float)).sum())
tokens_in = int(responses.get("tokens_in", pd.Series(dtype=float)).sum())
tokens_out = int(responses.get("tokens_out", pd.Series(dtype=float)).sum())
quality = float(responses.get("quality_score", pd.Series(dtype=float)).mean()) if not responses.empty else 0.0

breaches = {
    "Latency": bool(request_count and p95 > latency_cfg["threshold"]["value"]),
    "Errors": bool(request_count and error_rate > errors_cfg["threshold"]["value"]),
    "Cost": total_cost > cost_cfg["threshold"]["value"],
    "Tokens": max(tokens_in, tokens_out) > tokens_cfg["threshold"]["value"],
    "Quality": bool(request_count and quality < quality_cfg["threshold"]["value"]),
}
active_breaches = [name for name, breached in breaches.items() if breached]
status_class = "status-bad" if active_breaches else "status-ok"
status_text = f"{len(active_breaches)} threshold breach" if active_breaches else "All systems nominal"
last_event = window_df["ts"].max().strftime("%Y-%m-%d %H:%M UTC") if not window_df.empty else "No data"

header_left, header_right = st.columns([5, 1.4], vertical_alignment="center")
with header_left:
    st.markdown('<div class="dashboard-kicker">Operations / AI service</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-title">Observability Control Center</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="dashboard-meta">Last {window_minutes} minutes · {data_mode} · Updated {last_event}</div>',
        unsafe_allow_html=True,
    )
with header_right:
    st.markdown(f'<span class="{status_class}">{status_text}</span>', unsafe_allow_html=True)

if rejected_lines:
    st.warning(f"Skipped {rejected_lines} malformed log line(s).", icon="⚠️")
if window_df.empty:
    st.warning("No events are available for the selected time range. Run the load test and refresh.")
    st.stop()

st.write("")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Requests", f"{request_count:,}", f"{request_rate:.2f} req/min")
k2.metric("P95 latency", f"{p95:,.0f} ms", f"SLO ≤ {latency_cfg['threshold']['value']:,} ms", delta_color="off")
k3.metric("Error rate", f"{error_rate:.2f}%", f"SLO ≤ {errors_cfg['threshold']['value']}%", delta_color="off")
k4.metric("Window cost", f"${total_cost:.4f}", f"Budget ≤ ${cost_cfg['threshold']['value']}", delta_color="off")
k5.metric("Quality", f"{quality:.2f}", f"Floor ≥ {quality_cfg['threshold']['value']}", delta_color="off")

st.write("")
row1_left, row1_right = st.columns(2)
with row1_left:
    with st.container(border=True):
        heading("Latency percentiles", f"P50 {p50:,.0f} ms · P95 {p95:,.0f} ms · P99 {p99:,.0f} ms · SLO ≤ 3,000 ms")
        if not responses.empty and "latency_ms" in responses:
            latency = responses.groupby("minute")["latency_ms"].quantile([.5, .95, .99]).unstack().reset_index()
            latency.columns = ["minute", "P50", "P95", "P99"]
            latency = latency.melt("minute", var_name="Percentile", value_name="Latency (ms)")
            fig = px.line(latency, x="minute", y="Latency (ms)", color="Percentile", markers=True)
            fig.add_hline(y=latency_cfg["threshold"]["value"], line_dash="dash", line_color="#ef4444", annotation_text="SLO")
            compact_chart(fig)
        else:
            st.info("No response latency data")

with row1_right:
    with st.container(border=True):
        heading("Request traffic", f"{request_count} requests · {request_rate:.2f} requests/min · signal floor ≥ 1 request/min")
        traffic = requests.groupby("minute").size().reset_index(name="Requests") if not requests.empty else pd.DataFrame()
        if not traffic.empty:
            fig = px.area(traffic, x="minute", y="Requests", markers=True)
            fig.add_hline(y=traffic_cfg["threshold"]["value"], line_dash="dash", line_color="#f59e0b", annotation_text="Signal floor")
            compact_chart(fig)
        else:
            st.info("No request data")

row2_left, row2_right = st.columns(2)
with row2_left:
    with st.container(border=True):
        heading("Errors", f"{error_rate:.2f}% error rate · {error_count} failures · SLO ≤ 2%")
        if not requests.empty:
            req_by_minute = requests.groupby("minute").size().rename("requests")
            err_by_minute = failures.groupby("minute").size().rename("errors") if not failures.empty else pd.Series(dtype=float)
            errors = pd.concat([req_by_minute, err_by_minute], axis=1).fillna(0)
            errors["Error rate (%)"] = errors["errors"] / errors["requests"] * 100
            errors = errors.reset_index()
            fig = px.line(errors, x="minute", y="Error rate (%)", markers=True)
            fig.add_hline(y=errors_cfg["threshold"]["value"], line_dash="dash", line_color="#ef4444", annotation_text="SLO")
            compact_chart(fig, percent=True)
        else:
            st.info("No request data")

with row2_right:
    with st.container(border=True):
        heading("Cost", f"${total_cost:.4f} in selected window · budget ≤ ${cost_cfg['threshold']['value']}")
        if not responses.empty and "cost_usd" in responses:
            cost = responses.groupby("minute")["cost_usd"].sum().cumsum().reset_index(name="Cumulative cost (USD)")
            fig = px.line(cost, x="minute", y="Cumulative cost (USD)", markers=True)
            fig.add_hline(y=cost_cfg["threshold"]["value"], line_dash="dash", line_color="#ef4444", annotation_text="Budget")
            compact_chart(fig)
        else:
            st.info("No cost data")

row3_left, row3_right = st.columns(2)
with row3_left:
    with st.container(border=True):
        heading("Token usage", f"Input {tokens_in:,} · Output {tokens_out:,} · per-field limit ≤ {tokens_cfg['threshold']['value']:,}")
        token_frame = pd.DataFrame({"Token type": ["Input", "Output"], "Tokens": [tokens_in, tokens_out]})
        fig = px.bar(token_frame, x="Token type", y="Tokens", color="Token type", text_auto=",")
        fig.add_hline(y=tokens_cfg["threshold"]["value"], line_dash="dash", line_color="#ef4444", annotation_text="Per-field limit")
        compact_chart(fig)

with row3_right:
    with st.container(border=True):
        heading("Quality proxy", f"Mean score {quality:.2f} · quality floor ≥ {quality_cfg['threshold']['value']}")
        if not responses.empty and "quality_score" in responses:
            quality_trend = responses.groupby("minute")["quality_score"].mean().reset_index(name="Quality score")
            fig = px.line(quality_trend, x="minute", y="Quality score", markers=True)
            fig.add_hline(y=quality_cfg["threshold"]["value"], line_dash="dash", line_color="#ef4444", annotation_text="Quality floor")
            fig.update_yaxes(range=[0, 1])
            compact_chart(fig)
        else:
            st.info("No quality data")

st.caption("Six-panel operational view · Source: data/logs.jsonl · Thresholds: config/dashboard.yaml")
