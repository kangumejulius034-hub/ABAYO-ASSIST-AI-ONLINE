"""One responsive visual theme shared by every Streamlit page."""

from __future__ import annotations

import streamlit as st


def apply_theme(*, max_width: int = 1250) -> None:
    """Apply the ABAYO design system after ``st.set_page_config``."""

    st.html(
        f"""
        <style>
        :root {{
            --abayo-navy: #071426;
            --abayo-navy-light: #10213c;
            --abayo-blue: #2563eb;
            --abayo-blue-light: #eff6ff;
            --abayo-green: #039855;
            --abayo-green-light: #ecfdf3;
            --abayo-orange: #f79009;
            --abayo-orange-light: #fffaeb;
            --abayo-red: #d92d20;
            --abayo-red-light: #fef3f2;
            --abayo-text: #101828;
            --abayo-muted: #667085;
            --abayo-border: #e4e7ec;
            --abayo-background: #f6f8fc;
        }}

        .stApp {{ background: var(--abayo-background); }}

        .block-container {{
            max-width: {max_width}px;
            padding-top: 2.25rem;
            padding-bottom: 3rem;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(
                180deg,
                var(--abayo-navy) 0%,
                var(--abayo-navy-light) 100%
            );
            border-right: 1px solid rgba(255, 255, 255, .06);
        }}

        [data-testid="stSidebar"] * {{ color: white; }}

        [data-testid="stSidebar"] [data-testid="stPageLink"] a {{
            border-radius: 9px;
            padding: .66rem .78rem;
            margin-bottom: .16rem;
            text-decoration: none;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
            background: rgba(37, 99, 235, .24);
        }}

        [data-testid="stSidebar"] .stButton button {{
            width: 100%;
            min-height: 42px;
            border: 1px solid rgba(255, 255, 255, .14);
            background: rgba(255, 255, 255, .05);
            border-radius: 9px;
        }}

        [data-testid="stSidebar"] .stButton button:hover {{
            background: rgba(37, 99, 235, .28);
            border-color: #3b82f6;
        }}

        #MainMenu, footer, [data-testid="stDecoration"],
        [data-testid="stStatusWidget"], [data-testid="stToolbarActions"],
        [data-testid="stMainMenu"], [data-testid="stAppDeployButton"] {{
            display: none !important;
        }}

        header {{ background: transparent; }}
        [data-testid="stToolbar"] {{
            display: flex !important;
            background: transparent !important;
        }}

        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapsedControl"] {{
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 999999 !important;
        }}

        [data-testid="stExpandSidebarButton"] {{
            background: var(--abayo-navy) !important;
            color: white !important;
            border-radius: 9px !important;
            padding: .3rem !important;
        }}

        [data-testid="stExpandSidebarButton"] svg,
        [data-testid="stSidebarCollapsedControl"] svg {{
            color: white !important;
            fill: currentColor !important;
        }}

        .page-heading {{
            color: var(--abayo-text);
            font-size: clamp(1.65rem, 3vw, 2rem);
            line-height: 1.2;
            font-weight: 800;
            margin: 0;
        }}

        .page-subtitle {{
            color: var(--abayo-muted);
            font-size: .95rem;
            margin: .4rem 0 1.5rem;
        }}

        .section-heading {{
            color: var(--abayo-text);
            font-size: 1.3rem;
            font-weight: 800;
            margin: 1.65rem 0 .8rem;
        }}

        .metric-card, .machine-card, .action-card, .info-card,
        .section-card {{
            background: white;
            border: 1px solid var(--abayo-border);
            border-radius: 14px;
            box-shadow: 0 4px 16px rgba(16, 24, 40, .045);
        }}

        .metric-card {{ padding: 1.15rem; min-height: 145px; }}
        .metric-icon {{
            width: 42px;
            height: 42px;
            border-radius: 11px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.35rem;
            margin-bottom: .7rem;
        }}
        .green-icon {{ background: var(--abayo-green-light); }}
        .red-icon {{ background: var(--abayo-red-light); }}
        .orange-icon {{ background: var(--abayo-orange-light); }}
        .blue-icon {{ background: var(--abayo-blue-light); }}
        .metric-label {{ color: #344054; font-size: .87rem; font-weight: 700; }}
        .metric-value {{
            color: var(--abayo-text);
            font-size: 1.8rem;
            font-weight: 800;
            margin-top: .25rem;
        }}
        .metric-value.connected {{ color: var(--abayo-green); font-size: 1.4rem; }}
        .metric-value.offline {{ color: var(--abayo-red); font-size: 1.4rem; }}
        .metric-note {{ color: var(--abayo-muted); font-size: .8rem; margin-top: .25rem; }}

        .machine-card {{ padding: 1.35rem; }}
        .machine-header {{ display: flex; align-items: center; gap: .9rem; }}
        .machine-icon {{
            width: 58px;
            height: 58px;
            border-radius: 50%;
            background: var(--abayo-green-light);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            flex-shrink: 0;
        }}
        .machine-name {{ color: var(--abayo-text); font-size: 1.4rem; font-weight: 800; }}
        .machine-description {{ color: var(--abayo-muted); font-size: .9rem; margin-top: .25rem; }}
        .machine-details {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            margin-top: 1.3rem;
            border-top: 1px solid #f0f2f5;
            padding-top: 1rem;
        }}
        .machine-detail {{ padding-right: 1rem; }}
        .machine-detail + .machine-detail {{
            border-left: 1px solid #f0f2f5;
            padding-left: 1rem;
        }}
        .detail-label {{ color: var(--abayo-muted); font-size: .75rem; margin-bottom: .3rem; }}
        .detail-value {{ color: var(--abayo-text); font-size: .94rem; font-weight: 700; }}
        .machine-status {{
            display: inline-flex;
            align-items: center;
            border-radius: 20px;
            padding: .42rem .8rem;
            margin-top: 1rem;
            font-size: .85rem;
            font-weight: 700;
        }}
        .machine-status.online {{ background: var(--abayo-green-light); color: var(--abayo-green); }}
        .machine-status.offline {{ background: var(--abayo-red-light); color: var(--abayo-red); }}
        .machine-status.maintenance {{ background: var(--abayo-orange-light); color: #b54708; }}

        .action-card {{ padding: 1.05rem; min-height: 130px; margin-bottom: .4rem; }}
        .action-icon {{ font-size: 1.5rem; margin-bottom: .55rem; }}
        .action-title {{ color: var(--abayo-text); font-size: .95rem; font-weight: 800; }}
        .action-note {{ color: var(--abayo-muted); font-size: .82rem; margin-top: .3rem; line-height: 1.45; }}
        .app-footer {{ color: #98a2b3; text-align: center; margin-top: 2.2rem; font-size: .75rem; }}

        @media (max-width: 800px) {{
            .block-container {{ padding-top: 3.6rem; padding-left: 1rem; padding-right: 1rem; }}
            .machine-details {{ grid-template-columns: 1fr; gap: .8rem; }}
            .machine-detail, .machine-detail + .machine-detail {{
                border-left: 0;
                padding: 0;
            }}
            .metric-card {{ min-height: 0; }}
        }}
        </style>
        """
    )
