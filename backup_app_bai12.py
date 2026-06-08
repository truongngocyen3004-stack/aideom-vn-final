"""Dashboard Streamlit tích hợp AIDEOM-VN - Bài 12."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules import (
    allocate_budget,
    assess_regional_readiness,
    assess_risks,
    forecast_economy,
    get_scenario_shares,
    scenario_catalog,
    simulate_labor_market,
)
from modules.scenarios import (
    scenario_description,
    scenario_name,
)


st.set_page_config(
    page_title="AIDEOM-VN | Bài 12",
    page_icon="🇻🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }
    .hero {
        padding: 1.4rem 1.6rem;
        border-radius: 18px;
        background: linear-gradient(120deg, #0b3d91 0%, #0e7490 55%, #0f766e 100%);
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 8px 30px rgba(15, 23, 42, .18);
    }
    .hero h1 {
        margin: 0;
        font-size: 2.1rem;
    }
    .hero p {
        margin: .45rem 0 0;
        opacity: .93;
    }
    .note-card {
        padding: .9rem 1rem;
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, .35);
        background: rgba(248, 250, 252, .7);
        margin-bottom: .8rem;
    }
    [data-testid="stMetric"] {
        border: 1px solid rgba(148, 163, 184, .35);
        border-radius: 14px;
        padding: .8rem;
        background: rgba(255,255,255,.72);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(
    show_spinner=False
)
def run_scenario(
    scenario_code: str,
    total_budget: float,
    cyber_threshold: float,
    emission_threshold: float,
    dependency_threshold: float,
) -> dict:
    """Chạy toàn bộ M1-M5 cho một kịch bản."""

    shares = get_scenario_shares(
        scenario_code
    )

    forecast = forecast_economy(
        total_budget=total_budget,
        shares=shares,
    )

    readiness = assess_regional_readiness(
        total_budget=total_budget,
        shares=shares,
    )

    regional_allocation, category_summary = (
        allocate_budget(
            total_budget=total_budget,
            shares=shares,
        )
    )

    labor_table, labor_summary = (
        simulate_labor_market(
            total_budget=total_budget,
            shares=shares,
        )
    )

    risk_table, alerts, overall_risk = (
        assess_risks(
            shares=shares,
            regional_allocation=regional_allocation,
            labor_summary=labor_summary,
            cyber_threshold=cyber_threshold,
            emission_threshold=emission_threshold,
            dependency_threshold=dependency_threshold,
        )
    )

    return {
        "code": scenario_code,
        "name": scenario_name(
            scenario_code
        ),
        "description": scenario_description(
            scenario_code
        ),
        "shares": shares,
        "forecast": forecast,
        "readiness": readiness,
        "allocation": regional_allocation,
        "category_summary": category_summary,
        "labor": labor_table,
        "labor_summary": labor_summary,
        "risks": risk_table,
        "alerts": alerts,
        "overall_risk": overall_risk,
    }


def comparison_table(
    results: dict[str, dict]
) -> pd.DataFrame:
    """Tổng hợp KPI 2030 của năm kịch bản."""

    rows = []

    for code, result in results.items():
        forecast_2030 = (
            result["forecast"]
            .loc[
                result["forecast"][
                    "Năm"
                ] == 2030
            ]
            .iloc[0]
        )

        labor = result[
            "labor_summary"
        ]

        rows.append({
            "Mã": code,
            "Kịch bản": result["name"],
            "GDP 2030": forecast_2030["GDP"],
            "Tăng trưởng 2030 (%)": forecast_2030[
                "Tăng trưởng GDP (%)"
            ],
            "Digital Index bình quân": result[
                "readiness"
            ]["Digital Index 2030"].mean(),
            "AI Readiness bình quân": result[
                "readiness"
            ]["AI Readiness 2030"].mean(),
            "NetJob": labor["net_jobs"],
            "DisplacedJob": labor[
                "displaced_jobs"
            ],
            "Retraining gap": labor[
                "retraining_gap"
            ],
            "Rủi ro tổng hợp": result[
                "overall_risk"
            ],
            "Số cảnh báo": len(
                result["alerts"]
            ),
        })

    table = pd.DataFrame(rows)

    # Chỉ số chính sách tổng hợp: càng cao càng tốt.
    def benefit_scale(
        series: pd.Series
    ) -> pd.Series:
        low = float(series.min())
        high = float(series.max())

        if np.isclose(high, low):
            return pd.Series(
                np.ones(len(series)),
                index=series.index,
            )

        return (
            series - low
        ) / (
            high - low
        )

    def cost_scale(
        series: pd.Series
    ) -> pd.Series:
        return 1.0 - benefit_scale(
            series
        )

    table[
        "Điểm chính sách"
    ] = 100.0 * (
        0.40
        * benefit_scale(
            table["GDP 2030"]
        )
        + 0.25
        * benefit_scale(
            table["NetJob"]
        )
        + 0.15
        * benefit_scale(
            table[
                "Digital Index bình quân"
            ]
        )
        + 0.20
        * cost_scale(
            table["Rủi ro tổng hợp"]
        )
    )

    return table.sort_values(
        "Điểm chính sách",
        ascending=False,
    ).reset_index(drop=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("⚙️ Tham số đồ án")

    total_budget = st.slider(
        "Tổng ngân sách 2026-2030 (tỷ VND)",
        min_value=100_000,
        max_value=500_000,
        value=250_000,
        step=10_000,
    )

    selected_code = st.selectbox(
        "Kịch bản đang phân tích",
        options=[
            "S1", "S2", "S3", "S4", "S5"
        ],
        index=4,
        format_func=lambda code: (
            f"{code} - {scenario_name(code)}"
        ),
    )

    st.divider()

    st.caption(
        "Ngưỡng cảnh báo rủi ro"
    )

    cyber_threshold = st.slider(
        "Cyber",
        30.0,
        90.0,
        60.0,
        5.0,
    )

    emission_threshold = st.slider(
        "Phát thải",
        30.0,
        90.0,
        60.0,
        5.0,
    )

    dependency_threshold = st.slider(
        "Phụ thuộc công nghệ",
        30.0,
        90.0,
        60.0,
        5.0,
    )

    st.divider()

    st.caption(
        "Sản phẩm Bài 12: M1-M5 + M6 Dashboard"
    )


# ============================================================
# CHẠY 5 KỊCH BẢN
# ============================================================

all_results = {}

for code in (
    "S1", "S2", "S3", "S4", "S5"
):
    all_results[code] = run_scenario(
        scenario_code=code,
        total_budget=float(
            total_budget
        ),
        cyber_threshold=cyber_threshold,
        emission_threshold=emission_threshold,
        dependency_threshold=dependency_threshold,
    )

selected = all_results[
    selected_code
]

scenario_comparison = comparison_table(
    all_results
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>🇻🇳 AIDEOM-VN — Phòng điều hành chính sách số</h1>
        <p>
            Đồ án tích hợp Bài 12: dự báo kinh tế, sẵn sàng số,
            tối ưu phân bổ, thị trường lao động, rủi ro và so sánh
            năm kịch bản chính sách đến năm 2030.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    f"Đang xem **{selected_code} - {selected['name']}**. "
    f"{selected['description']}"
)


tabs = st.tabs([
    "🏠 Tổng quan",
    "💰 Phân bổ",
    "📊 Kịch bản so sánh",
    "👥 Lao động & sẵn sàng",
    "⚠️ Cảnh báo rủi ro",
    "📦 Bàn giao & kiểm thử",
])


# ============================================================
# TAB 1 - TỔNG QUAN
# ============================================================

with tabs[0]:
    forecast_2030 = (
        selected["forecast"]
        .loc[
            selected["forecast"][
                "Năm"
            ] == 2030
        ]
        .iloc[0]
    )

    kpi1, kpi2, kpi3, kpi4 = (
        st.columns(4)
    )

    kpi1.metric(
        "GDP 2030",
        f"{forecast_2030['GDP']:,.1f} nghìn tỷ VND",
    )

    kpi2.metric(
        "NetJob",
        f"{selected['labor_summary']['net_jobs']:,.0f} việc làm",
    )

    kpi3.metric(
        "Digital Index bình quân",
        (
            f"{selected['readiness']['Digital Index 2030'].mean():.1f}"
        ),
    )

    kpi4.metric(
        "Rủi ro tổng hợp",
        f"{selected['overall_risk']:.1f}/100",
        f"{len(selected['alerts'])} cảnh báo",
        delta_color="inverse",
    )

    col_left, col_right = (
        st.columns(
            [1.35, 1.0]
        )
    )

    with col_left:
        st.subheader(
            "Quỹ đạo GDP 2025-2030"
        )

        fig_gdp = px.line(
            selected["forecast"],
            x="Năm",
            y="GDP",
            markers=True,
            title=None,
        )

        fig_gdp.update_layout(
            yaxis_title=(
                "GDP, nghìn tỷ VND"
            ),
            height=390,
        )

        st.plotly_chart(
            fig_gdp,
            use_container_width=True,
        )

    with col_right:
        st.subheader(
            "Cơ cấu chính sách"
        )

        fig_shares = px.pie(
            selected[
                "category_summary"
            ],
            names="Hạng mục",
            values="Ngân sách",
            hole=0.54,
        )

        fig_shares.update_layout(
            height=390,
        )

        st.plotly_chart(
            fig_shares,
            use_container_width=True,
        )

    st.subheader(
        "Kết quả dự báo chi tiết"
    )

    st.dataframe(
        selected["forecast"].round(2),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 2 - PHÂN BỔ
# ============================================================

with tabs[1]:
    st.subheader(
        "Phân bổ ngân sách theo vùng và hạng mục"
    )

    allocation_long = (
        selected["allocation"]
        .melt(
            id_vars=[
                "Vùng",
                "Tổng ngân sách",
            ],
            value_vars=[
                "Vốn vật chất",
                "Số hóa",
                "AI",
                "Nhân lực số",
            ],
            var_name="Hạng mục",
            value_name="Ngân sách",
        )
    )

    fig_allocation = px.bar(
        allocation_long,
        x="Vùng",
        y="Ngân sách",
        color="Hạng mục",
        barmode="stack",
        title=(
            "Ngân sách 2026-2030 "
            "theo 6 vùng"
        ),
    )

    fig_allocation.update_layout(
        xaxis_tickangle=-18,
        height=470,
        yaxis_title="Tỷ VND",
    )

    st.plotly_chart(
        fig_allocation,
        use_container_width=True,
    )

    col_table, col_heatmap = (
        st.columns(
            [1.15, 1.0]
        )
    )

    with col_table:
        st.dataframe(
            selected[
                "allocation"
            ].round(1),
            use_container_width=True,
            hide_index=True,
        )

    with col_heatmap:
        heatmap_matrix = (
            selected["allocation"]
            .set_index("Vùng")
            [[
                "Vốn vật chất",
                "Số hóa",
                "AI",
                "Nhân lực số",
            ]]
        )

        fig_heat = px.imshow(
            heatmap_matrix,
            text_auto=".0f",
            aspect="auto",
            labels={
                "color": "Tỷ VND"
            },
        )

        fig_heat.update_layout(
            height=440,
        )

        st.plotly_chart(
            fig_heat,
            use_container_width=True,
        )


# ============================================================
# TAB 3 - SO SÁNH KỊCH BẢN
# ============================================================

with tabs[2]:
    st.subheader(
        "Bảng tổng hợp kết quả 2030 của năm kịch bản"
    )

    display_comparison = (
        scenario_comparison.copy()
    )

    st.dataframe(
        display_comparison.round(2),
        use_container_width=True,
        hide_index=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        fig_compare_gdp = px.bar(
            scenario_comparison,
            x="Mã",
            y="GDP 2030",
            color="Kịch bản",
            text_auto=".0f",
            title="GDP năm 2030",
        )

        fig_compare_gdp.update_layout(
            showlegend=False,
            height=410,
        )

        st.plotly_chart(
            fig_compare_gdp,
            use_container_width=True,
        )

    with col2:
        fig_compare_job = px.scatter(
            scenario_comparison,
            x="Rủi ro tổng hợp",
            y="NetJob",
            size="GDP 2030",
            color="Mã",
            hover_name="Kịch bản",
            text="Mã",
            title=(
                "Đánh đổi NetJob - rủi ro "
                "(kích thước = GDP)"
            ),
        )

        fig_compare_job.update_traces(
            textposition="top center"
        )

        fig_compare_job.update_layout(
            height=410,
        )

        st.plotly_chart(
            fig_compare_job,
            use_container_width=True,
        )

    best_row = (
        scenario_comparison.iloc[0]
    )

    st.success(
        f"Theo chỉ số tổng hợp của dashboard, phương án có điểm cao nhất là "
        f"**{best_row['Mã']} - {best_row['Kịch bản']}** "
        f"với {best_row['Điểm chính sách']:.1f}/100."
    )

    st.caption(
        "Chỉ số tổng hợp chỉ là công cụ hỗ trợ. Quyết định cuối cùng cần "
        "kết hợp mục tiêu chính trị, khả năng thực thi, tài khóa và mức chấp nhận rủi ro."
    )


# ============================================================
# TAB 4 - LAO ĐỘNG VÀ SẴN SÀNG
# ============================================================

with tabs[3]:
    labor_left, labor_right = (
        st.columns(2)
    )

    with labor_left:
        st.subheader(
            "Việc làm ròng theo ngành"
        )

        labor_plot = (
            selected["labor"]
            .sort_values(
                "NetJob",
                ascending=True,
            )
        )

        fig_labor = px.bar(
            labor_plot,
            x="NetJob",
            y="Ngành",
            orientation="h",
            title=None,
        )

        fig_labor.update_layout(
            height=480,
        )

        st.plotly_chart(
            fig_labor,
            use_container_width=True,
        )

    with labor_right:
        st.subheader(
            "Xếp hạng sẵn sàng số 2030"
        )

        readiness_plot = (
            selected["readiness"]
            .sort_values(
                "Điểm sẵn sàng 2030",
                ascending=True,
            )
        )

        fig_ready = px.bar(
            readiness_plot,
            x="Điểm sẵn sàng 2030",
            y="Vùng",
            orientation="h",
            text_auto=".3f",
            title=None,
        )

        fig_ready.update_layout(
            height=480,
        )

        st.plotly_chart(
            fig_ready,
            use_container_width=True,
        )

    st.subheader(
        "Bảng lao động và đào tạo lại"
    )

    st.dataframe(
        selected["labor"].round(1),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader(
        "Bảng chỉ số vùng"
    )

    st.dataframe(
        selected["readiness"].round(2),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 5 - RỦI RO
# ============================================================

with tabs[4]:
    st.subheader(
        "Hệ thống cảnh báo sớm"
    )

    fig_risk = go.Figure()

    fig_risk.add_trace(
        go.Bar(
            x=selected[
                "risks"
            ]["Rủi ro"],
            y=selected[
                "risks"
            ]["Điểm"],
            name="Điểm rủi ro",
            text=selected[
                "risks"
            ]["Điểm"].round(1),
            textposition="outside",
        )
    )

    fig_risk.add_trace(
        go.Scatter(
            x=selected[
                "risks"
            ]["Rủi ro"],
            y=selected[
                "risks"
            ]["Ngưỡng cảnh báo"],
            mode="lines+markers",
            name="Ngưỡng",
        )
    )

    fig_risk.update_layout(
        height=470,
        yaxis_title="Điểm 0-100",
        yaxis_range=[0, 110],
    )

    st.plotly_chart(
        fig_risk,
        use_container_width=True,
    )

    st.dataframe(
        selected["risks"].round(1),
        use_container_width=True,
        hide_index=True,
    )

    if selected["alerts"]:
        for alert in (
            selected["alerts"]
        ):
            st.warning(
                f"⚠️ {alert}"
            )
    else:
        st.success(
            "Không có chỉ tiêu nào vượt ngưỡng cảnh báo hiện tại."
        )

    st.subheader(
        "Khuyến nghị tự động"
    )

    recommendations = []

    if (
        selected["shares"][2]
        > 0.35
    ):
        recommendations.append(
            "Tăng đầu tư nhân lực, an ninh dữ liệu và năng lực giám sát "
            "để kiểm soát rủi ro của chiến lược AI cao."
        )

    if (
        selected[
            "labor_summary"
        ]["retraining_gap"]
        > 0
    ):
        recommendations.append(
            "Thiết lập quỹ đào tạo lại có mục tiêu cho các ngành có "
            "khoảng trống hấp thụ lao động."
        )

    if (
        selected["overall_risk"]
        > 60
    ):
        recommendations.append(
            "Áp dụng triển khai theo giai đoạn, kèm ngưỡng dừng và đánh giá độc lập."
        )

    if not recommendations:
        recommendations.append(
            "Duy trì cơ cấu hiện tại, nhưng cần cập nhật dữ liệu hằng năm "
            "và kiểm thử lại khi điều kiện vĩ mô thay đổi."
        )

    for item in recommendations:
        st.info(
            f"💡 {item}"
        )


# ============================================================
# TAB 6 - BÀN GIAO
# ============================================================

with tabs[5]:
    st.subheader(
        "Kiểm tra sản phẩm theo yêu cầu Bài 12"
    )

    checklist = pd.DataFrame({
        "Hạng mục": [
            "M1-M5 độc lập",
            "M6 Streamlit",
            "Tối thiểu 4 tab",
            "Chạy S1, S3, S5",
            "Unit test pytest",
            "README",
            "requirements.txt",
            "Báo cáo 15-25 trang",
            "Slide 15 trang",
            "Video demo 3-5 phút",
            "GitHub",
        ],
        "Trạng thái trong bộ code": [
            "Có",
            "Có",
            "Có 6 tab",
            "Có đủ 5 kịch bản",
            "Có",
            "Có",
            "Có",
            "Người học hoàn thiện",
            "Người học hoàn thiện",
            "Người học thực hiện",
            "Người học đẩy mã nguồn",
        ],
    })

    st.dataframe(
        checklist,
        use_container_width=True,
        hide_index=True,
    )

    st.code(
        "pytest -q",
        language="bash",
    )

    st.code(
        "streamlit run app.py",
        language="bash",
    )

    st.markdown(
        """
        **Cấu trúc module**

        - `M1`: dự báo GDP, TFP và trạng thái kinh tế đến 2030.
        - `M2`: đánh giá Digital Index và AI Readiness của sáu vùng.
        - `M3`: phân bổ ngân sách vùng × hạng mục.
        - `M4`: mô phỏng việc làm mới, nâng cấp, bị thay thế và đào tạo lại.
        - `M5`: đánh giá rủi ro cyber, phát thải, phụ thuộc, vùng và lao động.
        - `M6`: dashboard Streamlit tổng hợp và hỗ trợ quyết định.
        """
    )

    csv_data = scenario_comparison.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "⬇️ Tải bảng so sánh 5 kịch bản",
        data=csv_data,
        file_name=(
            "AIDEOM_VN_so_sanh_5_kich_ban.csv"
        ),
        mime="text/csv",
    )
