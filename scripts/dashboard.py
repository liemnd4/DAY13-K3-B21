from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yaml


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs.jsonl"
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"
DISPLAY_TIMEZONE = "Asia/Ho_Chi_Minh"

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
    fig.update_xaxes(
        title=None,
        gridcolor="rgba(128,128,128,.12)",
        tickformat="%H:%M",
        hoverformat="%Y-%m-%d %H:%M:%S",
        range=[window_start, now],
        tick0=window_start.ceil(f"{axis_tick_seconds}s"),
        dtick=axis_tick_seconds * 1000,
    )
    fig.update_yaxes(
        title=None,
        gridcolor="rgba(128,128,128,.12)",
        rangemode="tozero",
    )
    if percent:
        fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def add_threshold_badge(fig, text: str) -> None:
    """Show a threshold without letting it expand the numeric Y-axis range."""
    fig.add_annotation(
        text=text,
        xref="paper",
        yref="paper",
        x=.99,
        y=.98,
        xanchor="right",
        yanchor="top",
        showarrow=False,
        bgcolor="rgba(239,68,68,.12)",
        bordercolor="rgba(239,68,68,.45)",
        borderpad=5,
        font=dict(color="#ef4444", size=10),
    )


def empty_time_chart(message: str, *, percent: bool = False) -> None:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=.5,
        y=.5,
        showarrow=False,
        font=dict(color="#7b8495", size=13),
    )
    compact_chart(fig, percent=percent)


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
    refresh_options = [15, 30, 60]
    refresh_seconds = st.selectbox(
        "Refresh every",
        refresh_options,
        index=refresh_options.index(config["refresh_seconds"]),
        format_func=lambda value: f"{value} seconds",
        disabled=not auto_refresh,
    )
    bucket_options = [30, 60, 300]
    bucket_seconds = st.selectbox(
        "Data interval",
        bucket_options,
        index=0,
        format_func=lambda value: f"{value} seconds" if value < 60 else f"{value // 60} minute(s)",
    )
    hold_last_value = st.toggle(
        "Hold last value",
        value=True,
        help="Grafana-style last-not-null: extend the latest observation until a new value arrives.",
    )
    st.caption("Axis labels adapt to the selected time range; hover shows exact seconds.")
    st.divider()
    st.caption("SOURCE")
    st.code("data/logs.jsonl", language=None)
    st.caption("Dashboard contract: config/dashboard.yaml")

if auto_refresh:
    st_autorefresh(
        interval=refresh_seconds * 1000,
        limit=None,
        key="dashboard-data-refresh",
    )

if not df.empty and "ts" in df:
    df["ts"] = df["ts"].dt.tz_convert(DISPLAY_TIMEZONE)

now = pd.Timestamp.now(tz=DISPLAY_TIMEZONE)
window_start = now - pd.Timedelta(minutes=window_minutes)
window_df = df[df["ts"].between(window_start, now)].copy() if not df.empty and "ts" in df else pd.DataFrame()
bucket_frequency = f"{bucket_seconds}s"
timeline = pd.date_range(
    start=window_start.floor(bucket_frequency),
    end=now.ceil(bucket_frequency),
    freq=bucket_frequency,
)
desired_tick_seconds = max(bucket_seconds, window_minutes * 60 / 6)
axis_tick_seconds = next(
    step for step in [30, 60, 120, 300, 600, 900, 1800, 3600]
    if step >= desired_tick_seconds
)

responses = window_df[window_df.get("event", pd.Series(dtype=str)) == "response_sent"].copy()
requests = window_df[window_df.get("event", pd.Series(dtype=str)) == "request_received"].copy()
failures = window_df[window_df.get("event", pd.Series(dtype=str)) == "request_failed"].copy()

for frame in (responses, requests, failures):
    if not frame.empty:
        frame["bucket"] = frame["ts"].dt.floor(bucket_frequency)

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
    "Traffic": request_rate < traffic_cfg["threshold"]["value"],
    "Errors": bool(request_count and error_rate > errors_cfg["threshold"]["value"]),
    "Cost": total_cost > cost_cfg["threshold"]["value"],
    "Tokens": max(tokens_in, tokens_out) > tokens_cfg["threshold"]["value"],
    "Quality": bool(request_count and quality < quality_cfg["threshold"]["value"]),
}
active_breaches = [name for name, breached in breaches.items() if breached]
breach_details = []
if breaches["Latency"]:
    breach_details.append(("Latency", "HighLatencyP95", f"P95 {p95:,.0f} ms > {latency_cfg['threshold']['value']:,} ms"))
if breaches["Traffic"]:
    breach_details.append(("Traffic", "TrafficSignalLow", f"{request_rate:.2f} req/min < {traffic_cfg['threshold']['value']} req/min"))
if breaches["Errors"]:
    breach_details.append(("Errors", "HighErrorRate", f"{error_rate:.2f}% > {errors_cfg['threshold']['value']}%"))
if breaches["Cost"]:
    breach_details.append(("Cost", "CostGuardrail", f"${total_cost:.4f} > ${cost_cfg['threshold']['value']}"))
if breaches["Tokens"]:
    breach_details.append(("Tokens", "TokenGuardrail", f"{max(tokens_in, tokens_out):,} > {tokens_cfg['threshold']['value']:,} tokens"))
if breaches["Quality"]:
    breach_details.append(("Quality", "LowQualityScore", f"{quality:.2f} < {quality_cfg['threshold']['value']}"))
status_class = "status-bad" if active_breaches else "status-ok"
status_text = (
    f"{len(active_breaches)} threshold breach{'es' if len(active_breaches) != 1 else ''}"
    if active_breaches
    else "All systems nominal"
)
last_event = df["ts"].max().strftime("%H:%M:%S") if not df.empty and "ts" in df else "No data"

header_left, header_right = st.columns([5, 1.4], vertical_alignment="center")
with header_left:
    st.markdown('<div class="dashboard-kicker">Operations / AI service</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-title">Observability Control Center</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="dashboard-meta">{window_start:%H:%M} → {now:%H:%M} ICT (UTC+7) · refresh {refresh_seconds}s · data interval {bucket_seconds}s · latest event {last_event}</div>',
        unsafe_allow_html=True,
    )
with header_right:
    status_icon = "⚠" if active_breaches else "✓"
    st.markdown(f'<span class="{status_class}">{status_icon} {status_text}</span>', unsafe_allow_html=True)

with st.expander(f"{status_icon} {status_text} — click to inspect", expanded=False):
    if breach_details:
        st.markdown("#### Active threshold breaches")
        detail_columns = st.columns(min(len(breach_details), 3))
        for index, (metric, alert_name, condition) in enumerate(breach_details):
            with detail_columns[index % len(detail_columns)]:
                st.markdown(f"**{metric}**")
                st.code(alert_name, language=None)
                st.caption(condition)
        st.divider()
        st.caption("Runbook: docs/alerts.md · Threshold source: config/dashboard.yaml")
    else:
        st.success("All six panel thresholds are within their configured limits.")
        st.caption("Threshold source: config/dashboard.yaml")

if rejected_lines:
    st.warning(f"Skipped {rejected_lines} malformed log line(s).", icon="⚠️")
if window_df.empty:
    st.warning("No events in the live time window. The panels will keep moving and populate when new requests arrive.")

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
        heading("Latency percentiles", f"P50 {p50:,.0f} ms · P95 {p95:,.0f} ms · P99 {p99:,.0f} ms · SLO ≤ 3,000 ms · {'hold last value' if hold_last_value else 'show gaps'}")
        if not responses.empty and "latency_ms" in responses:
            latency = responses.groupby("bucket")["latency_ms"].quantile([.5, .95, .99]).unstack()
            latency.columns = ["P50", "P95", "P99"]
            latency = latency.reindex(timeline)
            if hold_last_value:
                latency = latency.ffill()
            latency = latency.rename_axis("bucket").reset_index()
            latency = latency.melt("bucket", var_name="Percentile", value_name="Latency (ms)")
            fig = px.line(latency, x="bucket", y="Latency (ms)", color="Percentile", line_shape="hv")
            add_threshold_badge(fig, f"SLO ≤ {latency_cfg['threshold']['value']:,} ms")
            compact_chart(fig)
        else:
            empty_time_chart("No response latency data in this window")

with row1_right:
    with st.container(border=True):
        heading("Request traffic", f"{request_count} requests · {request_rate:.2f} requests/min · signal floor ≥ 1 request/min")
        traffic = requests.groupby("bucket").size().reindex(timeline, fill_value=0).rename_axis("bucket").reset_index(name="Requests/min") if not requests.empty else pd.DataFrame()
        if not traffic.empty:
            traffic["Requests/min"] = traffic["Requests/min"] * 60 / bucket_seconds
            fig = px.area(traffic, x="bucket", y="Requests/min", markers=True)
            add_threshold_badge(fig, f"Signal floor ≥ {traffic_cfg['threshold']['value']} req/min")
            compact_chart(fig)
        else:
            empty_time_chart("No request data in this window")

row2_left, row2_right = st.columns(2)
with row2_left:
    with st.container(border=True):
        heading("Errors", f"{error_rate:.2f}% error rate · {error_count} failures · SLO ≤ 2% · {'hold last value' if hold_last_value else 'show gaps'}")
        if not requests.empty:
            req_by_bucket = requests.groupby("bucket").size().reindex(timeline, fill_value=0).rename("requests")
            errors = req_by_bucket.to_frame()
            if failures.empty:
                errors["errors"] = 0
            else:
                errors["errors"] = (
                    failures.groupby("bucket")
                    .size()
                    .reindex(errors.index, fill_value=0)
                )
            errors["Error rate (%)"] = (errors["errors"] / errors["requests"] * 100).where(errors["requests"] > 0)
            if hold_last_value:
                errors["Error rate (%)"] = errors["Error rate (%)"].ffill()
            errors = errors.rename_axis("bucket").reset_index()
            fig = px.line(errors, x="bucket", y="Error rate (%)", line_shape="hv")
            fig.update_traces(line_width=3)
            add_threshold_badge(fig, f"SLO ≤ {errors_cfg['threshold']['value']}%")
            compact_chart(fig, percent=True)
        else:
            empty_time_chart("No request data in this window", percent=True)

with row2_right:
    with st.container(border=True):
        heading("Cost", f"${total_cost:.4f} in selected window · budget ≤ ${cost_cfg['threshold']['value']}")
        if not responses.empty and "cost_usd" in responses:
            cost = responses.groupby("bucket")["cost_usd"].sum().reindex(timeline, fill_value=0).cumsum().rename_axis("bucket").reset_index(name="Cumulative cost (USD)")
            fig = px.line(cost, x="bucket", y="Cumulative cost (USD)", markers=True)
            add_threshold_badge(fig, f"Budget ≤ ${cost_cfg['threshold']['value']}")
            compact_chart(fig)
        else:
            empty_time_chart("No cost data in this window")

row3_left, row3_right = st.columns(2)
with row3_left:
    with st.container(border=True):
        heading("Token usage", f"Input {tokens_in:,} · Output {tokens_out:,} · per-field limit ≤ {tokens_cfg['threshold']['value']:,}")
        if not responses.empty and {"tokens_in", "tokens_out"}.issubset(responses.columns):
            token_frame = responses.groupby("bucket")[["tokens_in", "tokens_out"]].sum().reindex(timeline, fill_value=0).rename_axis("bucket").reset_index()
            token_frame = token_frame.melt("bucket", var_name="Token type", value_name="Tokens")
            fig = px.area(token_frame, x="bucket", y="Tokens", color="Token type")
            add_threshold_badge(fig, f"Limit ≤ {tokens_cfg['threshold']['value']:,}")
            compact_chart(fig)
        else:
            empty_time_chart("No token data in this window")

with row3_right:
    with st.container(border=True):
        heading("Quality proxy", f"Mean score {quality:.2f} · quality floor ≥ {quality_cfg['threshold']['value']} · {'hold last value' if hold_last_value else 'show gaps'}")
        if not responses.empty and "quality_score" in responses:
            quality_trend = responses.groupby("bucket")["quality_score"].mean().reindex(timeline)
            if hold_last_value:
                quality_trend = quality_trend.ffill()
            quality_trend = quality_trend.rename_axis("bucket").reset_index(name="Quality score")
            fig = px.line(quality_trend, x="bucket", y="Quality score", line_shape="hv")
            add_threshold_badge(fig, f"Quality floor ≥ {quality_cfg['threshold']['value']}")
            fig.update_yaxes(range=[0, 1])
            compact_chart(fig)
        else:
            empty_time_chart("No quality data in this window")

st.caption("Six-panel operational view · Source: data/logs.jsonl · Thresholds: config/dashboard.yaml")
