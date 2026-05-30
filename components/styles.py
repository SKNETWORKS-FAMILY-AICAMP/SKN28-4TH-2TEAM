import streamlit as st


def load_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        :root {
            --kaist-blue: #005bac;
            --kaist-blue-2: #0077e6;
            --kaist-light: #eef7ff;
            --ink: #102033;
            --muted: #5f7188;
            --line: #d8e8f8;
            --card: #ffffff;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 18% 8%, rgba(0, 91, 172, 0.08), transparent 28%),
                radial-gradient(circle at 88% 12%, rgba(0, 119, 230, 0.08), transparent 30%),
                linear-gradient(180deg, #ffffff 0%, #f8fbff 48%, #ffffff 100%);
            color: var(--ink);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.2rem;
            padding-bottom: 3rem;
        }

        [data-testid="stHeader"] {
            height: 0rem;
            background: transparent;
        }

        [data-testid="stDecoration"],
        [data-testid="stToolbar"],
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"] {
            display: none;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--ink);
            letter-spacing: -0.035em;
        }

        p {
            color: var(--muted);
            line-height: 1.75;
        }

        a {
            text-decoration: none !important;
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.6rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }

        .brand-mark {
            width: 48px;
            height: 48px;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--kaist-blue), var(--kaist-blue-2));
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            box-shadow: 0 12px 28px rgba(0, 91, 172, 0.22);
        }

        .brand-title {
            font-weight: 900;
            color: var(--ink);
            font-size: 1.02rem;
            line-height: 1.1;
        }

        .brand-subtitle {
            color: var(--muted);
            font-size: 0.82rem;
            margin-top: 0.18rem;
        }

        .demo-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.55rem 0.95rem;
            border-radius: 999px;
            background: #f0f8ff;
            border: 1px solid var(--line);
            color: var(--kaist-blue);
            font-weight: 800;
            font-size: 0.86rem;
        }

        .hero-card {
            display: grid;
            grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
            gap: 2rem;
            align-items: center;
            padding: 2.7rem;
            border-radius: 28px;
            background: linear-gradient(135deg, #ffffff 0%, #eef7ff 100%);
            border: 1px solid var(--line);
            box-shadow: 0 24px 70px rgba(0, 91, 172, 0.12);
            margin-bottom: 2rem;
        }

        .hero-copy {
            min-width: 0;
        }

        .hero-kicker {
            color: var(--kaist-blue);
            font-weight: 900;
            font-size: 0.82rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 1rem;
        }

        .hero-title {
            font-size: 3.15rem;
            line-height: 1.05;
            font-weight: 900;
            color: var(--ink);
            margin-bottom: 1.15rem;
        }

        .blue-text {
            color: var(--kaist-blue);
        }

        .hero-desc {
            font-size: 1.02rem;
            color: var(--muted);
            line-height: 1.8;
            max-width: 620px;
            margin-bottom: 1.25rem;
        }

        .badge-row {
            display: flex;
            gap: 0.6rem;
            flex-wrap: wrap;
        }

        .badge {
            padding: 0.48rem 0.78rem;
            border-radius: 999px;
            background: white;
            color: var(--kaist-blue);
            border: 1px solid var(--line);
            font-size: 0.83rem;
            font-weight: 800;
        }

        .hero-image-wrap {
            width: 100%;
            height: 260px;
            border-radius: 24px;
            background: #ffffff;
            border: 1px solid #dbeafe;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            box-shadow:
                inset 0 0 0 1px rgba(255,255,255,0.7),
                0 18px 42px rgba(0, 91, 172, 0.08);
        }

        .hero-image-wrap img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            object-position: center;
            padding: 24px;
            display: block;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 900;
            color: var(--ink);
            margin: 2rem 0 1rem 0;
            letter-spacing: -0.04em;
        }

        .info-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1.35rem;
            box-shadow: 0 14px 34px rgba(0, 91, 172, 0.07);
            min-height: 150px;
        }

        .start-card {
            text-align: left;
            margin-bottom: 0.65rem;
        }

        .info-card h3 {
            margin: 0 0 0.7rem 0;
            color: var(--ink);
            font-size: 1.02rem;
            font-weight: 900;
        }

        .info-card p {
            margin: 0;
            color: var(--muted);
            font-size: 0.94rem;
        }

        .icon-box {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            background: var(--kaist-light);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }

        .mini-card {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1.2rem;
            box-shadow: 0 10px 28px rgba(0, 91, 172, 0.06);
            min-height: 150px;
        }

        .mini-card h3 {
            margin: 0 0 0.6rem 0;
            font-size: 1rem;
            color: var(--ink);
        }

        .mini-card p {
            margin: 0;
            font-size: 0.92rem;
            color: var(--muted);
        }

        .page-header {
            padding: 2.2rem;
            border-radius: 28px;
            background: linear-gradient(135deg, #ffffff 0%, #eef7ff 100%);
            border: 1px solid var(--line);
            box-shadow: 0 18px 54px rgba(0, 91, 172, 0.1);
            margin-bottom: 1.6rem;
        }

        .page-header h1 {
            font-size: 2.4rem;
            font-weight: 900;
            color: var(--ink);
            margin: 0 0 0.6rem 0;
        }

        .page-header p {
            max-width: 760px;
            margin: 0;
            color: var(--muted);
            font-size: 1rem;
        }

        .source-wrap {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 18px;
            background: #f7fbff;
            border: 1px solid var(--line);
        }

        .source-card {
            padding: 0.85rem;
            border-radius: 14px;
            background: #ffffff;
            border: 1px solid var(--line);
            margin-top: 0.55rem;
        }

        .source-title {
            color: var(--ink);
            font-weight: 800;
            font-size: 0.9rem;
        }

        .source-title a {
            color: var(--kaist-blue);
            font-weight: 900;
        }

        .source-meta {
            color: var(--muted);
            font-size: 0.78rem;
            margin-top: 0.25rem;
        }

        .stMetric {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 1rem;
            box-shadow: 0 10px 28px rgba(0, 91, 172, 0.06);
        }

        .stChatMessage {
            background: #ffffff !important;
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem;
            box-shadow: 0 8px 24px rgba(0, 91, 172, 0.05);
        }

        .stChatInput {
            background: #ffffff;
        }

        .stChatInput textarea {
            border-radius: 18px !important;
            border: 1px solid var(--line) !important;
        }

        button[kind="secondary"] {
            border-radius: 14px !important;
            border: 1px solid var(--line) !important;
            background: #ffffff !important;
            color: var(--kaist-blue) !important;
            font-weight: 800 !important;
            transition: all 0.22s ease;
        }

        button[kind="secondary"]:hover {
            border-color: var(--kaist-blue) !important;
            background: #f0f8ff !important;
            transform: translateY(-1px);
        }

        div[data-testid="stPageLink"] {
            width: 100% !important;
        }

        .stPageLink a,
        div[data-testid="stPageLink"] a {
            width: 100% !important;
            min-height: 52px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;

            background: linear-gradient(135deg, #005bac 0%, #0077e6 100%) !important;
            color: #ffffff !important;

            border-radius: 14px !important;
            border: none !important;

            padding: 0.75rem 1rem !important;
            font-weight: 800 !important;
            font-size: 0.95rem !important;

            box-shadow: 0 8px 20px rgba(0, 91, 172, 0.18);
            transition: all 0.25s ease;
        }

        .stPageLink a:hover,
        div[data-testid="stPageLink"] a:hover {
            background: linear-gradient(135deg, #004a91 0%, #006fd6 100%) !important;
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(0, 91, 172, 0.28);
            color: #ffffff !important;
        }

        .stPageLink a *,
        div[data-testid="stPageLink"] a * {
            color: #ffffff !important;
            opacity: 1 !important;
            text-align: center !important;
            justify-content: center !important;
        }

        .stPageLink a span,
        div[data-testid="stPageLink"] a span {
            width: 100% !important;
            text-align: center !important;
        }

        .stPageLink a svg,
        div[data-testid="stPageLink"] a svg {
            color: #ffffff !important;
            fill: #ffffff !important;
            stroke: #ffffff !important;
        }

        hr {
            border-color: var(--line);
        }

        @media (max-width: 900px) {
            .hero-card {
                grid-template-columns: 1fr;
                padding: 1.7rem;
            }

            .hero-title {
                font-size: 2.15rem;
            }

            .topbar {
                align-items: flex-start;
                gap: 1rem;
                flex-direction: column;
            }

            .hero-image-wrap {
                height: 220px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )