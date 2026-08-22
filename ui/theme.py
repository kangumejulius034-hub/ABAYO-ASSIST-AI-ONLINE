"""One responsive visual theme shared by every Streamlit page."""

from __future__ import annotations

import streamlit as st


def apply_theme(*, max_width: int = 1380) -> None:
    """Apply the ABAYO design system after ``st.set_page_config``."""

    st.html(
        f"""
        <style>
        :root {{
            --abayo-navy: #041126;
            --abayo-navy-light: #0a1d3a;
            --abayo-blue: #0b63f6;
            --abayo-blue-2: #1687f8;
            --abayo-cyan: #16b8ee;
            --abayo-violet: #6d4aff;
            --abayo-blue-light: #edf5ff;
            --abayo-blue-soft: #173055;
            --abayo-blue-hover: #1b365d;
            --abayo-green: #039855;
            --abayo-green-light: #ecfdf3;
            --abayo-orange: #f79009;
            --abayo-orange-light: #fffaeb;
            --abayo-red: #d92d20;
            --abayo-red-light: #fef3f2;
            --abayo-text: #0f1f3d;
            --abayo-muted: #667085;
            --abayo-border: #e0e7f0;
            --abayo-background: #f5f8fd;
            --abayo-shadow: 0 10px 30px rgba(21, 54, 99, .08);
        }}

        html {{ scroll-behavior: smooth; }}
        .stApp {{
            background:
                radial-gradient(circle at 84% -10%, rgba(22, 135, 248, .08), transparent 30%),
                linear-gradient(180deg, #fbfdff 0%, var(--abayo-background) 100%);
        }}

        .block-container {{
            max-width: {max_width}px;
            padding-top: 4.35rem;
            padding-bottom: 3rem;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--abayo-navy) 0%, var(--abayo-navy-light) 100%);
            border-right: 1px solid rgba(255, 255, 255, .06);
        }}
        [data-testid="stSidebar"] * {{ color: white; }}

        [data-testid="stSidebar"] [data-testid="stPageLink"] a {{
            border-radius: 9px;
            padding: .66rem .78rem;
            margin-bottom: .16rem;
            text-decoration: none;
        }}
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{ background: rgba(37, 99, 235, .24); }}
        [data-testid="stSidebar"] .stButton button {{
            width: 100%; min-height: 42px;
            border: 1px solid rgba(255, 255, 255, .14);
            background: rgba(255, 255, 255, .05);
            border-radius: 9px;
        }}
        [data-testid="stSidebar"] .stButton button:hover {{
            background: rgba(37, 99, 235, .28);
            border-color: #3b82f6;
        }}

        [data-testid="stSidebar"] [data-testid="stSelectbox"] label,
        [data-testid="stSidebar"] .stSelectbox label {{ color: #ffffff !important; font-weight: 700 !important; }}
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {{
            background: var(--abayo-blue-soft) !important;
            border: 1px solid rgba(147, 197, 253, .5) !important;
            border-radius: 12px !important;
            min-height: 48px !important;
            box-shadow: 0 0 0 1px rgba(37, 99, 235, .08) !important;
        }}
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div:hover {{
            background: var(--abayo-blue-hover) !important;
            border-color: #60a5fa !important;
        }}
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] input,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] input {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-weight: 650 !important;
            caret-color: #ffffff !important;
        }}
        [data-testid="stSidebar"] [data-testid="stSelectbox"] input::placeholder,
        [data-testid="stSidebar"] .stSelectbox input::placeholder {{
            color: #bfdbfe !important; -webkit-text-fill-color: #bfdbfe !important; opacity: 1 !important;
        }}
        [data-testid="stSidebar"] [data-testid="stSelectbox"] svg,
        [data-testid="stSidebar"] .stSelectbox svg {{ color: #ffffff !important; fill: currentColor !important; }}

        div[data-baseweb="popover"] div[role="listbox"] {{
            background: #10213c !important;
            border: 1px solid rgba(147, 197, 253, .28) !important;
            border-radius: 12px !important;
            box-shadow: 0 14px 34px rgba(7, 20, 38, .28) !important;
            overflow: hidden !important;
        }}
        div[data-baseweb="popover"] div[role="option"] {{ color: #ffffff !important; background: #10213c !important; }}
        div[data-baseweb="popover"] div[role="option"]:hover {{ background: #173055 !important; }}
        div[data-baseweb="popover"] div[role="option"][aria-selected="true"] {{
            background: var(--abayo-blue) !important; color: #ffffff !important; font-weight: 700 !important;
        }}

        #MainMenu, footer, [data-testid="stDecoration"],
        [data-testid="stStatusWidget"], [data-testid="stToolbarActions"],
        [data-testid="stMainMenu"], [data-testid="stAppDeployButton"] {{ display: none !important; }}
        header {{ background: transparent; }}
        [data-testid="stToolbar"] {{ display: flex !important; background: transparent !important; }}
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapsedControl"] {{
            display: flex !important; visibility: visible !important; opacity: 1 !important; z-index: 999999 !important;
        }}
        [data-testid="stExpandSidebarButton"] {{
            background: linear-gradient(135deg, #06162e, #0d3266) !important;
            color: white !important; border-radius: 10px !important; padding: .32rem !important;
            box-shadow: 0 7px 18px rgba(4,17,38,.18);
        }}
        [data-testid="stExpandSidebarButton"] svg,
        [data-testid="stSidebarCollapsedControl"] svg {{ color: white !important; fill: currentColor !important; }}

        .page-heading {{
            color: var(--abayo-text);
            font-size: clamp(1.7rem, 3vw, 2.15rem);
            line-height: 1.18;
            font-weight: 850;
            margin: 0;
            letter-spacing: -.025em;
            overflow: visible;
        }}
        .page-subtitle {{ color: var(--abayo-muted); font-size: .94rem; margin: .36rem 0 1.3rem; }}
        .section-heading {{
            color: var(--abayo-text);
            font-size: 1.16rem;
            font-weight: 850;
            margin: 1.45rem 0 .7rem;
            letter-spacing: -.015em;
        }}

        .metric-card, .machine-card, .action-card, .info-card, .section-card {{
            background: white;
            border: 1px solid var(--abayo-border);
            border-radius: 14px;
            box-shadow: 0 5px 18px rgba(16, 24, 40, .05);
        }}
        .metric-card {{ padding: 1.15rem; min-height: 145px; }}
        .metric-icon {{
            width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center;
            font-size: 1.35rem; margin-bottom: .7rem;
        }}
        .green-icon {{ background: var(--abayo-green-light); }}
        .red-icon {{ background: var(--abayo-red-light); }}
        .orange-icon {{ background: var(--abayo-orange-light); }}
        .blue-icon {{ background: var(--abayo-blue-light); }}
        .metric-label {{ color: #344054; font-size: .87rem; font-weight: 700; }}
        .metric-value {{ color: var(--abayo-text); font-size: 1.8rem; font-weight: 800; margin-top: .25rem; }}
        .metric-value.connected {{ color: var(--abayo-green); font-size: 1.4rem; }}
        .metric-value.offline {{ color: var(--abayo-red); font-size: 1.4rem; }}
        .metric-note {{ color: var(--abayo-muted); font-size: .8rem; margin-top: .25rem; }}

        .machine-card {{ padding: 1.35rem; }}
        .machine-header {{ display: flex; align-items: center; gap: .9rem; }}
        .machine-icon {{
            width: 58px; height: 58px; border-radius: 50%; background: var(--abayo-green-light);
            display: flex; align-items: center; justify-content: center; font-size: 1.8rem; flex-shrink: 0;
        }}
        .machine-name {{ color: var(--abayo-text); font-size: 1.4rem; font-weight: 800; }}
        .machine-description {{ color: var(--abayo-muted); font-size: .9rem; margin-top: .25rem; }}
        .machine-details {{
            display: grid; grid-template-columns: repeat(3, 1fr); margin-top: 1.3rem;
            border-top: 1px solid #f0f2f5; padding-top: 1rem;
        }}
        .machine-detail {{ padding-right: 1rem; }}
        .machine-detail + .machine-detail {{ border-left: 1px solid #f0f2f5; padding-left: 1rem; }}
        .detail-label {{ color: var(--abayo-muted); font-size: .75rem; margin-bottom: .3rem; }}
        .detail-value {{ color: var(--abayo-text); font-size: .94rem; font-weight: 700; }}
        .machine-status {{
            display: inline-flex; align-items: center; border-radius: 20px; padding: .42rem .8rem; margin-top: 1rem;
            font-size: .85rem; font-weight: 700;
        }}
        .machine-status.online {{ background: var(--abayo-green-light); color: var(--abayo-green); }}
        .machine-status.offline {{ background: var(--abayo-red-light); color: var(--abayo-red); }}
        .machine-status.maintenance {{ background: var(--abayo-orange-light); color: #b54708; }}

        .action-card {{ padding: 1.05rem; min-height: 130px; margin-bottom: .4rem; }}
        .action-icon {{ font-size: 1.5rem; margin-bottom: .55rem; }}
        .action-title {{ color: var(--abayo-text); font-size: .95rem; font-weight: 800; }}
        .action-note {{ color: var(--abayo-muted); font-size: .82rem; margin-top: .3rem; line-height: 1.45; }}
        .app-footer {{ color: #98a2b3; text-align: center; margin-top: 2rem; font-size: .74rem; }}

        /* Pic 3 direction: strong machine hero + bright industrial copilot. */
        .command-hero {{
            padding: 1.45rem 1.55rem !important;
            min-height: 250px !important;
            border: 0 !important;
            border-radius: 18px !important;
            background:
                radial-gradient(circle at 82% 28%, rgba(56,189,248,.22), transparent 28%),
                linear-gradient(128deg, #061a45 0%, #0849b5 50%, #118cf7 100%) !important;
            box-shadow: 0 18px 42px rgba(11,99,246,.19) !important;
            overflow: hidden;
            position: relative;
        }}
        .command-hero::after {{
            content: ""; position: absolute; width: 190px; height: 190px; right: -62px; bottom: -90px;
            border: 1px solid rgba(255,255,255,.14); border-radius: 50%; box-shadow: 0 0 0 24px rgba(255,255,255,.035);
        }}
        .command-hero .eyebrow {{ color: #a8cdfc !important; }}
        .command-machine-name {{ color: #ffffff !important; font-size: clamp(1.75rem, 3.2vw, 2.35rem) !important; }}
        .command-machine-meta {{ color: #d7e8ff !important; }}
        .command-hero .status-pill {{ border: 1px solid rgba(255,255,255,.12) !important; backdrop-filter: blur(5px); }}
        .command-hero .status-pill.online {{ background: rgba(4,199,118,.20) !important; color: #d6ffec !important; }}
        .command-hero .status-pill.offline {{ background: rgba(248,113,113,.18) !important; color: #ffe1e1 !important; }}
        .command-hero .status-pill.maintenance {{ background: rgba(251,191,36,.18) !important; color: #fff0bf !important; }}
        .command-hero .hero-details {{ border-color: rgba(255,255,255,.15) !important; position: relative; z-index: 1; }}
        .command-hero .hero-detail-label {{ color: #9fc7f6 !important; }}
        .command-hero .hero-detail-value {{ color: #ffffff !important; }}

        .ai-command-card {{
            min-height: 250px !important;
            padding: 1.45rem !important;
            border: 0 !important;
            border-radius: 18px !important;
            background:
                radial-gradient(circle at 92% 12%, rgba(103,232,249,.28), transparent 26%),
                linear-gradient(135deg, #0b46d8 0%, #126ef2 57%, #13b6e9 100%) !important;
            box-shadow: 0 18px 42px rgba(11,99,246,.16) !important;
        }}
        .ai-command-card .eyebrow {{ color: #c9e2ff !important; }}
        .ai-command-title {{ color: white !important; font-size: 1.3rem !important; }}
        .ai-command-copy {{ color: #eaf5ff !important; }}
        .ai-command-scope {{ color: #c5e4ff !important; }}
        .ai-icon {{ background: rgba(255,255,255,.16) !important; box-shadow: inset 0 1px 0 rgba(255,255,255,.15); }}

        .snapshot-card {{
            padding: 1rem 1.05rem !important;
            border-radius: 14px !important;
            border-color: #dfe8f5 !important;
            box-shadow: 0 7px 20px rgba(32,72,125,.055) !important;
        }}
        .snapshot-icon {{
            width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center;
            background: #edf5ff; font-size: 1.08rem !important; margin-bottom: .55rem !important;
        }}
        .snapshot-value {{ color: #102a56 !important; }}

        .knowledge-card {{
            border-radius: 14px !important;
            border-color: #dfe8f5 !important;
            box-shadow: 0 7px 20px rgba(32,72,125,.05) !important;
        }}
        .knowledge-number {{ color: #123c79 !important; }}

        .insight-card {{
            padding: 1.18rem 1.25rem !important;
            border-radius: 16px !important;
            border: 1px solid #fed7aa !important;
            background: linear-gradient(135deg, #fffdf7 0%, #fff8e8 100%) !important;
            box-shadow: 0 9px 25px rgba(245,158,11,.08) !important;
        }}
        .insight-kicker {{ color: #b45309 !important; }}
        .insight-title {{ color: #7c3e0a !important; }}
        .insight-copy {{ color: #76552e !important; }}

        .activity-card {{
            border-radius: 12px !important;
            border-color: #e2e9f3 !important;
            box-shadow: 0 5px 16px rgba(32,72,125,.04) !important;
        }}
        .activity-icon {{ background: #edf5ff !important; }}

        [data-testid="stMain"] [data-testid="stPageLink"] a {{
            min-height: 42px;
            display: flex;
            align-items: center;
            border: 1px solid #dce6f3 !important;
            border-radius: 11px !important;
            background: #ffffff !important;
            color: #123c79 !important;
            font-weight: 720 !important;
            box-shadow: 0 5px 14px rgba(32,72,125,.04);
            transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
        }}
        [data-testid="stMain"] [data-testid="stPageLink"] a:hover {{
            transform: translateY(-1px);
            border-color: #9ec5ff !important;
            box-shadow: 0 9px 20px rgba(11,99,246,.08);
        }}

        [data-testid="stMain"] .stButton button[kind="primary"],
        [data-testid="stMain"] .stButton button[data-testid="stBaseButton-primary"] {{
            background: linear-gradient(100deg, #0757e8, #1387f6) !important;
            border-color: #0b63f6 !important;
            box-shadow: 0 8px 18px rgba(11,99,246,.16) !important;
        }}

        @media (max-width: 800px) {{
            .block-container {{
                padding-top: 3.95rem;
                padding-left: .72rem;
                padding-right: .72rem;
                padding-bottom: 2rem;
            }}

            .page-heading {{ font-size: 1.48rem; line-height: 1.16; }}
            .page-heading::before {{
                content: "ABAYO  /  MACHINE INTELLIGENCE";
                display: block;
                color: #0b63f6;
                font-size: .62rem;
                line-height: 1;
                font-weight: 850;
                letter-spacing: .11em;
                margin-bottom: .46rem;
            }}
            .page-subtitle {{ font-size: .82rem; margin-bottom: .92rem; }}
            .section-heading {{ font-size: 1rem; margin: 1.12rem 0 .56rem; }}

            [data-testid="stMain"] div[data-testid="stHorizontalBlock"] {{
                gap: .58rem !important;
                align-items: stretch !important;
            }}

            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.command-hero),
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.activity-card) {{
                flex-wrap: wrap !important;
            }}
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.command-hero) > div[data-testid="column"],
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.activity-card) > div[data-testid="column"] {{
                flex: 1 1 100% !important;
                width: 100% !important;
                min-width: 100% !important;
            }}

            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.snapshot-card),
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.knowledge-card) {{
                flex-wrap: wrap !important;
            }}
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.snapshot-card) > div[data-testid="column"],
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.knowledge-card) > div[data-testid="column"] {{
                flex: 1 1 calc(50% - .35rem) !important;
                width: calc(50% - .35rem) !important;
                min-width: calc(50% - .35rem) !important;
            }}

            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has([data-testid="stSelectbox"]) {{ flex-wrap: wrap !important; }}
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has([data-testid="stSelectbox"]) > div[data-testid="column"]:first-child {{
                flex: 1 1 100% !important; width: 100% !important; min-width: 100% !important;
            }}
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has([data-testid="stSelectbox"]) > div[data-testid="column"]:not(:first-child) {{
                flex: 1 1 calc(50% - .35rem) !important; min-width: calc(50% - .35rem) !important;
            }}

            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"] [data-testid="stPageLink"]) {{
                flex-wrap: wrap !important;
            }}
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"] [data-testid="stPageLink"]) > div[data-testid="column"] {{
                flex: 1 1 calc(50% - .35rem) !important;
                min-width: calc(50% - .35rem) !important;
            }}
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.command-hero) > div[data-testid="column"] {{
                flex: 1 1 100% !important; min-width: 100% !important;
            }}

            [data-testid="stForm"] div[data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; }}
            [data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
                flex: 1 1 100% !important; width: 100% !important; min-width: 100% !important;
            }}

            .command-caption {{ font-size: .69rem !important; margin-bottom: .5rem !important; }}
            .command-hero {{ min-height: 0 !important; padding: 1.15rem !important; border-radius: 15px !important; }}
            .command-machine-name {{ font-size: 1.58rem !important; }}
            .command-machine-meta {{ font-size: .8rem !important; }}
            .command-hero .hero-details {{ grid-template-columns: repeat(2, minmax(0,1fr)) !important; gap: .55rem !important; }}
            .command-hero .hero-details > div:last-child {{ grid-column: 1 / -1; }}
            .ai-command-card {{ min-height: 0 !important; padding: 1.15rem !important; border-radius: 15px !important; }}
            .ai-command-title {{ font-size: 1.14rem !important; }}
            .ai-command-copy {{ font-size: .8rem !important; }}

            .snapshot-card {{ min-height: 0 !important; padding: .82rem !important; }}
            .snapshot-value {{ font-size: 1.18rem !important; }}
            .snapshot-note {{ font-size: .64rem !important; }}
            .knowledge-card {{ min-height: 0 !important; padding: .78rem .82rem !important; }}
            .knowledge-number {{ font-size: 1.2rem !important; }}
            .knowledge-note {{ font-size: .62rem !important; }}
            .insight-card {{ padding: .95rem 1rem !important; }}
            .insight-title {{ font-size: .94rem !important; }}
            .insight-copy {{ font-size: .77rem !important; }}
            .activity-card {{ padding: .68rem .72rem !important; margin-bottom: .4rem !important; }}

            [data-testid="stMain"] [data-testid="stPageLink"] a {{
                min-height: 44px !important;
                padding: .52rem .56rem !important;
                font-size: .78rem !important;
            }}
            [data-testid="stMain"] .stButton button {{ min-height: 43px !important; border-radius: 10px !important; }}

            .machine-details {{ grid-template-columns: 1fr; gap: .8rem; }}
            .machine-detail, .machine-detail + .machine-detail {{ border-left: 0; padding: 0; }}
            .metric-card {{ min-height: 0; }}
        }}

        @media (max-width: 430px) {{
            .block-container {{ padding-left: .58rem; padding-right: .58rem; }}
            .page-heading {{ font-size: 1.38rem; }}
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.snapshot-card) > div[data-testid="column"],
            [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.knowledge-card) > div[data-testid="column"] {{
                flex-basis: calc(50% - .3rem) !important;
                min-width: calc(50% - .3rem) !important;
            }}
            .snapshot-label, .knowledge-name {{ font-size: .68rem !important; }}
        }}
        </style>
        """
    )
