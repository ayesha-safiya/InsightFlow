import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ──
st.set_page_config(
    page_title="Workflow Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# ── Title ──
st.title("📊 Workflow Intelligence – Analytics & Decision Engine")
st.markdown("**InsightFlow**")
st.divider()

# ── File Upload ──
st.subheader("📂 Upload Your Dataset")
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:

    # ── Load file ──
    if uploaded_file.name.endswith(".csv"):
        try:
            df_raw = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df_raw = pd.read_csv(uploaded_file, encoding='latin1')
    else:
        df_raw = pd.read_excel(uploaded_file)

    st.success(f"✅ File uploaded! Found {len(df_raw)} records and {len(df_raw.columns)} columns.")
    st.divider()

    # ── Data Cleaning ──
    def clean_data(df):
        df = df.copy()
        df.columns = df.columns.str.strip()
        duplicates_removed = df.duplicated().sum()
        df = df.drop_duplicates()
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    converted = pd.to_datetime(df[col], errors='coerce')
                    if converted.notna().sum() > len(df) * 0.5:
                        df[col] = converted
                except:
                    pass
        missing_before = df.isnull().sum().sum()
        num_cols_clean = df.select_dtypes(include='number').columns
        for col in num_cols_clean:
            df[col] = df[col].fillna(df[col].mean())
        cat_cols_clean = df.select_dtypes(include='object').columns
        for col in cat_cols_clean:
            df[col] = df[col].fillna('Unknown')
        missing_after = df.isnull().sum().sum()
        return df, duplicates_removed, missing_before, missing_after

    df_clean, dupes, missing_before, missing_after = clean_data(df_raw)

    # ── Cleaning Summary ──
    st.subheader("🧹 Data Cleaning Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 Total Records", f"{len(df_clean):,}")
    col2.metric("🗂️ Total Columns", len(df_clean.columns))
    col3.metric("🔧 Missing Values Fixed", int(missing_before - missing_after))
    col4.metric("🗑️ Duplicates Removed", int(dupes))
    st.success("✅ Data cleaned successfully!")
    st.divider()

    # ── Column Type Editor ──
    st.subheader("🔧 Column Type Editor")
    st.caption("Optionally change how columns are treated before analysis.")

    if "col_types" not in st.session_state or st.session_state.get("last_file") != uploaded_file.name:
        st.session_state.last_file = uploaded_file.name
        st.session_state.col_types = {}
        for col in df_clean.columns:
            if pd.api.types.is_numeric_dtype(df_clean[col]):
                st.session_state.col_types[col] = "Numeric"
            elif pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                st.session_state.col_types[col] = "Date"
            else:
                st.session_state.col_types[col] = "Text"
        st.session_state.hidden_auto_kpis = []
        st.session_state.hidden_auto_charts = []
        st.session_state.kpi_list = []
        st.session_state.cat_kpi_list = []
        st.session_state.chart_list = []

    with st.expander("📋 Edit Column Types (optional)", expanded=False):
        col_list = list(df_clean.columns)
        for i in range(0, len(col_list), 4):
            row_cols = st.columns(4)
            for j, col in enumerate(col_list[i:i+4]):
                with row_cols[j]:
                    st.session_state.col_types[col] = st.selectbox(
                        col, ["Numeric", "Text", "Date"],
                        index=["Numeric", "Text", "Date"].index(
                            st.session_state.col_types.get(col, "Text")
                        ),
                        key=f"coltype_{col}"
                    )

    # Apply types
    df_typed = df_clean.copy()
    for col, ctype in st.session_state.col_types.items():
        if col not in df_typed.columns:
            continue
        if ctype == "Numeric":
            df_typed[col] = pd.to_numeric(df_typed[col], errors='coerce').fillna(0)
        elif ctype == "Text":
            df_typed[col] = df_typed[col].astype(str)
        elif ctype == "Date":
            df_typed[col] = pd.to_datetime(df_typed[col], errors='coerce')

    num_cols = [c for c, t in st.session_state.col_types.items() if t == "Numeric" and c in df_typed.columns]
    cat_cols = [c for c, t in st.session_state.col_types.items() if t == "Text" and c in df_typed.columns]
    date_cols = [c for c, t in st.session_state.col_types.items() if t == "Date" and c in df_typed.columns]

    st.divider()

    # ── Cleaned Data Preview ──
    st.subheader("📂 Cleaned Data Preview")
    st.dataframe(df_typed)
    csv_download = df_typed.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Cleaned CSV", data=csv_download,
                       file_name="cleaned_data.csv", mime="text/csv")
    st.divider()

    # ── Helper Functions ──
    AGG_OPTIONS = ["Mean", "Sum", "Min", "Max", "Median", "Count", "Std Dev"]

    def compute_agg(series, agg):
        if agg == "Mean":      return series.mean()
        elif agg == "Sum":     return series.sum()
        elif agg == "Min":     return series.min()
        elif agg == "Max":     return series.max()
        elif agg == "Median":  return series.median()
        elif agg == "Count":   return series.count()
        elif agg == "Std Dev": return series.std()
        return 0

    def format_value(value, decimals, use_comma):
        if use_comma:
            return f"{value:,.{decimals}f}"
        else:
            return f"{value:.{decimals}f}"

    top_num_cols = num_cols[:4] if len(num_cols) >= 4 else num_cols
    top_cat_col = cat_cols[0] if cat_cols else None
    top_num_col = num_cols[0] if num_cols else None
    total_cells = df_raw.shape[0] * df_raw.shape[1]
    missing_cells = df_raw.isnull().sum().sum()
    quality_score = ((total_cells - missing_cells) / total_cells) * 100

    # ──────────────────────────────────────────
    # ── AUTO KPI GENERATION ──
    # ──────────────────────────────────────────
    st.subheader("📊 Auto-Generated KPIs")
    st.caption("12 KPIs automatically generated. Click 🗑️ on any individual KPI to remove it.")

    if "hidden_auto_kpis" not in st.session_state:
        st.session_state.hidden_auto_kpis = []

    # ── Group 1: Numeric Summary ──
    st.markdown("#### 🔢 Numeric Summary")
    auto_aggs = ["Mean", "Sum", "Max", "Min"]
    visible_num = [(i, col) for i, col in enumerate(top_num_cols)
                   if f"num_{i}" not in st.session_state.hidden_auto_kpis]

    if visible_num:
        g1_cols = st.columns(len(visible_num))
        for j, (i, col) in enumerate(visible_num):
            agg = auto_aggs[i % len(auto_aggs)]
            selected_agg = g1_cols[j].selectbox(
                f"{col}", AGG_OPTIONS,
                index=AGG_OPTIONS.index(agg),
                key=f"auto_kpi_agg_{i}"
            )
            dec = g1_cols[j].selectbox("Decimals", [0,1,2,3,4], index=2, key=f"auto_kpi_dec_{i}")
            use_comma = g1_cols[j].checkbox("Commas", value=True, key=f"auto_kpi_comma_{i}")
            val = compute_agg(df_typed[col], selected_agg)
            g1_cols[j].metric(f"{selected_agg} of {col}", format_value(val, dec, use_comma))
            if g1_cols[j].button("🗑️", key=f"hide_num_{i}", help="Remove this KPI"):
                st.session_state.hidden_auto_kpis.append(f"num_{i}")
                st.rerun()
    else:
        st.info("All Numeric Summary KPIs removed.")

    if any(k.startswith("num_") for k in st.session_state.hidden_auto_kpis):
        if st.button("↩️ Restore Numeric KPIs"):
            st.session_state.hidden_auto_kpis = [k for k in st.session_state.hidden_auto_kpis if not k.startswith("num_")]
            st.rerun()

    st.divider()

    # ── Group 2: Top & Bottom + Category ──
    st.markdown("#### 🏆 Top, Bottom & Category")

    if top_num_col:
        top_row = df_typed.loc[df_typed[top_num_col].idxmax()]
        bot_row = df_typed.loc[df_typed[top_num_col].idxmin()]
        label = cat_cols[0] if cat_cols else top_num_col

    tb_kpis = []
    if top_num_col:
        tb_kpis.append(("tb_top", f"🥇 Highest {top_num_col}"))
        tb_kpis.append(("tb_bot", f"🔻 Lowest {top_num_col}"))
    if top_cat_col:
        tb_kpis.append(("tb_common", f"🏅 Most Common {top_cat_col}"))
        tb_kpis.append(("tb_unique", f"🔤 Unique {top_cat_col}"))

    visible_tb = [(key, lbl) for key, lbl in tb_kpis
                  if key not in st.session_state.hidden_auto_kpis]

    if visible_tb:
        g2_cols = st.columns(len(visible_tb))
        for j, (key, lbl) in enumerate(visible_tb):
            if key == "tb_top" and top_num_col:
                dec = g2_cols[j].selectbox("Decimals", [0,1,2,3,4], index=2, key="top_dec")
                use_comma = g2_cols[j].checkbox("Commas", value=True, key="top_comma")
                g2_cols[j].metric(lbl, format_value(top_row[top_num_col], dec, use_comma),
                                  delta=str(top_row[label]) if label in top_row else "")
            elif key == "tb_bot" and top_num_col:
                dec = g2_cols[j].selectbox("Decimals", [0,1,2,3,4], index=2, key="bot_dec")
                use_comma = g2_cols[j].checkbox("Commas", value=True, key="bot_comma")
                g2_cols[j].metric(lbl, format_value(bot_row[top_num_col], dec, use_comma),
                                  delta=str(bot_row[label]) if label in bot_row else "",
                                  delta_color="inverse")
            elif key == "tb_common" and top_cat_col:
                vc = df_typed[top_cat_col].value_counts()
                g2_cols[j].metric(lbl, vc.idxmax())
                g2_cols[j].caption(f"{vc.max():,} occurrences")
            elif key == "tb_unique" and top_cat_col:
                g2_cols[j].metric(lbl, df_typed[top_cat_col].nunique())
                g2_cols[j].caption("unique values")

            if g2_cols[j].button("🗑️", key=f"hide_{key}", help="Remove this KPI"):
                st.session_state.hidden_auto_kpis.append(key)
                st.rerun()
    else:
        st.info("All Top & Bottom KPIs removed.")

    if any(k.startswith("tb_") for k in st.session_state.hidden_auto_kpis):
        if st.button("↩️ Restore Top & Bottom KPIs"):
            st.session_state.hidden_auto_kpis = [k for k in st.session_state.hidden_auto_kpis if not k.startswith("tb_")]
            st.rerun()

    st.divider()

    # ── Group 3: Data Quality ──
    st.markdown("#### 📋 Data Quality")
    dq_kpis = [
        ("dq_records", "📋 Total Records",        f"{len(df_typed):,}"),
        ("dq_columns", "🗂️ Total Columns",         str(len(df_typed.columns))),
        ("dq_missing", "🔧 Missing Values Fixed",  str(int(missing_before - missing_after))),
        ("dq_quality", "✅ Data Quality Score",    f"{quality_score:.1f}%"),
    ]
    visible_dq = [(key, lbl, val) for key, lbl, val in dq_kpis
                  if key not in st.session_state.hidden_auto_kpis]

    if visible_dq:
        g3_cols = st.columns(len(visible_dq))
        for j, (key, lbl, val) in enumerate(visible_dq):
            g3_cols[j].metric(lbl, val)
            if g3_cols[j].button("🗑️", key=f"hide_{key}", help="Remove this KPI"):
                st.session_state.hidden_auto_kpis.append(key)
                st.rerun()
    else:
        st.info("All Data Quality KPIs removed.")

    if any(k.startswith("dq_") for k in st.session_state.hidden_auto_kpis):
        if st.button("↩️ Restore Data Quality KPIs"):
            st.session_state.hidden_auto_kpis = [k for k in st.session_state.hidden_auto_kpis if not k.startswith("dq_")]
            st.rerun()

    st.divider()

    # ── Custom KPI Builder ──
    st.markdown("#### ➕ Add Custom KPIs")

    with st.expander("🔢 Add Custom Numeric KPIs", expanded=False):
        for idx, kpi in enumerate(st.session_state.kpi_list):
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            with c1:
                st.session_state.kpi_list[idx]["col"] = st.selectbox(
                    f"KPI {idx+1} – Column", num_cols,
                    index=num_cols.index(kpi["col"]) if kpi["col"] in num_cols else 0,
                    key=f"kpi_col_{idx}"
                )
            with c2:
                st.session_state.kpi_list[idx]["agg"] = st.selectbox(
                    f"KPI {idx+1} – Aggregation", AGG_OPTIONS,
                    index=AGG_OPTIONS.index(kpi["agg"]) if kpi["agg"] in AGG_OPTIONS else 0,
                    key=f"kpi_agg_{idx}"
                )
            with c3:
                st.session_state.kpi_list[idx]["decimals"] = st.selectbox(
                    f"KPI {idx+1} – Decimals", [0,1,2,3,4],
                    index=kpi.get("decimals", 2),
                    key=f"kpi_dec_{idx}"
                )
            with c4:
                st.session_state.kpi_list[idx]["comma"] = st.checkbox(
                    f"KPI {idx+1} – Commas",
                    value=kpi.get("comma", True),
                    key=f"kpi_comma_{idx}"
                )
            with c5:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"remove_kpi_{idx}"):
                    st.session_state.kpi_list.pop(idx)
                    st.rerun()

        if num_cols and st.button("➕ Add Numeric KPI"):
            st.session_state.kpi_list.append({"col": num_cols[0], "agg": "Mean", "decimals": 2, "comma": True})
            st.rerun()

        if st.session_state.kpi_list:
            chunks = [st.session_state.kpi_list[i:i+4] for i in range(0, len(st.session_state.kpi_list), 4)]
            for chunk in chunks:
                cols = st.columns(4)
                for j, kpi in enumerate(chunk):
                    col = kpi["col"]
                    agg = kpi["agg"]
                    dec = kpi.get("decimals", 2)
                    comma = kpi.get("comma", True)
                    if col in df_typed.columns:
                        value = compute_agg(df_typed[col], agg)
                        cols[j].metric(f"{agg} of {col}", format_value(value, dec, comma))

    with st.expander("🔤 Add Custom Categorical KPIs", expanded=False):
        CAT_METRICS = ["Most Common", "Least Common", "Unique Count", "Top 3 Values"]
        for idx, ckpi in enumerate(st.session_state.cat_kpi_list):
            c1, c2, c3 = st.columns([3, 3, 1])
            with c1:
                st.session_state.cat_kpi_list[idx]["col"] = st.selectbox(
                    f"Cat KPI {idx+1} – Column", cat_cols,
                    index=cat_cols.index(ckpi["col"]) if ckpi["col"] in cat_cols else 0,
                    key=f"cat_kpi_col_{idx}"
                )
            with c2:
                st.session_state.cat_kpi_list[idx]["metric"] = st.selectbox(
                    f"Cat KPI {idx+1} – Metric", CAT_METRICS,
                    index=CAT_METRICS.index(ckpi["metric"]) if ckpi["metric"] in CAT_METRICS else 0,
                    key=f"cat_kpi_metric_{idx}"
                )
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"remove_cat_kpi_{idx}"):
                    st.session_state.cat_kpi_list.pop(idx)
                    st.rerun()

        if cat_cols and st.button("➕ Add Categorical KPI"):
            st.session_state.cat_kpi_list.append({"col": cat_cols[0], "metric": "Most Common"})
            st.rerun()

        if st.session_state.cat_kpi_list:
            cat_chunks = [st.session_state.cat_kpi_list[i:i+4] for i in range(0, len(st.session_state.cat_kpi_list), 4)]
            for chunk in cat_chunks:
                cols = st.columns(4)
                for j, ckpi in enumerate(chunk):
                    col = ckpi["col"]
                    metric = ckpi["metric"]
                    if col in df_typed.columns:
                        vc = df_typed[col].value_counts()
                        if metric == "Most Common":
                            cols[j].metric(f"Most Common {col}", vc.idxmax())
                            cols[j].caption(f"{vc.max():,} occurrences")
                        elif metric == "Least Common":
                            cols[j].metric(f"Least Common {col}", vc.idxmin())
                            cols[j].caption(f"{vc.min()} occurrences")
                        elif metric == "Unique Count":
                            cols[j].metric(f"Unique {col}", df_typed[col].nunique())
                        elif metric == "Top 3 Values":
                            top3 = ", ".join(vc.head(3).index.astype(str).tolist())
                            cols[j].metric(f"Top 3 {col}", "")
                            cols[j].caption(top3)

    st.divider()

    # ──────────────────────────────────────────
    # ── AUTO CHART GENERATION ──
    # ──────────────────────────────────────────
    st.subheader("📈 Auto-Generated Charts")
    st.caption("4 charts automatically generated. Click 🗑️ Remove to hide any chart.")

    if "hidden_auto_charts" not in st.session_state:
        st.session_state.hidden_auto_charts = []

    CHART_TYPES = [
        "Bar Chart", "Horizontal Bar", "Line Chart", "Area Chart",
        "Pie Chart", "Donut Chart", "Scatter Plot", "Box Plot",
        "Histogram", "Heatmap (Correlation)"
    ]

    # ── Auto Chart 1 — Bar Chart ──
    if cat_cols and num_cols:
        c_head, c_del = st.columns([6, 1])
        c_head.markdown("#### 📊 Chart 1 — Top 10 Bar Chart")
        if c_del.button("🗑️ Remove", key="del_auto_chart1"):
            if "chart1" in st.session_state.hidden_auto_charts:
                st.session_state.hidden_auto_charts.remove("chart1")
            else:
                st.session_state.hidden_auto_charts.append("chart1")
            st.rerun()

        if "chart1" not in st.session_state.hidden_auto_charts:
            c1, c2, c3 = st.columns(3)
            bar_cat = c1.selectbox("Category (X axis)", cat_cols, key="auto_bar_cat")
            bar_num = c2.selectbox("Numeric (Y axis)", num_cols, key="auto_bar_num")
            bar_agg = c3.selectbox("Aggregation", AGG_OPTIONS, key="auto_bar_agg")
            bar_data = df_typed.groupby(bar_cat)[bar_num].agg(
                lambda x: compute_agg(x, bar_agg)
            ).nlargest(10).reset_index()
            fig_bar = px.bar(bar_data, x=bar_cat, y=bar_num,
                             title=f"Top 10 {bar_cat} by {bar_agg} of {bar_num}",
                             color=bar_num, color_continuous_scale="Blues")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Bar Chart hidden. Click 🗑️ Remove again to restore.")
        st.divider()

    # ── Auto Chart 2 — Pie Chart ──
    if cat_cols and num_cols:
        c_head, c_del = st.columns([6, 1])
        c_head.markdown("#### 🥧 Chart 2 — Category Breakdown")
        if c_del.button("🗑️ Remove", key="del_auto_chart2"):
            if "chart2" in st.session_state.hidden_auto_charts:
                st.session_state.hidden_auto_charts.remove("chart2")
            else:
                st.session_state.hidden_auto_charts.append("chart2")
            st.rerun()

        if "chart2" not in st.session_state.hidden_auto_charts:
            c1, c2 = st.columns(2)
            pie_cat = c1.selectbox("Category column", cat_cols, key="auto_pie_cat")
            pie_num = c2.selectbox("Numeric column", num_cols, key="auto_pie_num")
            pie_data = df_typed.groupby(pie_cat)[pie_num].sum().nlargest(10).reset_index()
            fig_pie = px.pie(pie_data, names=pie_cat, values=pie_num,
                             title=f"Top 10 {pie_cat} by {pie_num}")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Pie Chart hidden. Click 🗑️ Remove again to restore.")
        st.divider()

    # ── Auto Chart 3 — Histogram ──
    if num_cols:
        c_head, c_del = st.columns([6, 1])
        c_head.markdown("#### 📉 Chart 3 — Distribution")
        if c_del.button("🗑️ Remove", key="del_auto_chart3"):
            if "chart3" in st.session_state.hidden_auto_charts:
                st.session_state.hidden_auto_charts.remove("chart3")
            else:
                st.session_state.hidden_auto_charts.append("chart3")
            st.rerun()

        if "chart3" not in st.session_state.hidden_auto_charts:
            c1, c2 = st.columns(2)
            hist_col = c1.selectbox("Numeric column", num_cols, key="auto_hist_col")
            hist_bins = c2.slider("Number of bins", 5, 100, 20, key="auto_hist_bins")
            fig_hist = px.histogram(df_typed, x=hist_col, nbins=hist_bins,
                                    title=f"Distribution of {hist_col}",
                                    color_discrete_sequence=["#1F77B4"])
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Histogram hidden. Click 🗑️ Remove again to restore.")
        st.divider()

    # ── Auto Chart 4 — Heatmap ──
    if len(num_cols) >= 2:
        c_head, c_del = st.columns([6, 1])
        c_head.markdown("#### 🌡️ Chart 4 — Correlation Heatmap")
        if c_del.button("🗑️ Remove", key="del_auto_chart4"):
            if "chart4" in st.session_state.hidden_auto_charts:
                st.session_state.hidden_auto_charts.remove("chart4")
            else:
                st.session_state.hidden_auto_charts.append("chart4")
            st.rerun()

        if "chart4" not in st.session_state.hidden_auto_charts:
            default_cols = num_cols[:8]
            selected_heat = st.multiselect("Select numeric columns", num_cols,
                                           default=default_cols, key="auto_heat_cols")
            if len(selected_heat) >= 2:
                corr = df_typed[selected_heat].corr()
                fig_heat = px.imshow(corr, text_auto=True,
                                     color_continuous_scale="RdBu",
                                     title="Correlation Heatmap")
                st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Heatmap hidden. Click 🗑️ Remove again to restore.")
        st.divider()

    # ── Custom Chart Builder ──
    st.markdown("#### ➕ Add Custom Charts")

    def render_chart(chart_cfg, idx):
        ctype = chart_cfg["type"]

        if ctype in ["Bar Chart", "Horizontal Bar"]:
            c1, c2, c3 = st.columns(3)
            x_col = c1.selectbox("X axis (Text)", cat_cols, key=f"chart_x_{idx}")
            y_col = c2.selectbox("Y axis (Numeric)", num_cols, key=f"chart_y_{idx}")
            agg = c3.selectbox("Aggregation", AGG_OPTIONS, key=f"chart_agg_{idx}")
            top_n = c1.slider("Top N", 5, 30, 10, key=f"chart_n_{idx}")
            data = df_typed.groupby(x_col)[y_col].agg(lambda x: compute_agg(x, agg)).nlargest(top_n).reset_index()
            if ctype == "Bar Chart":
                fig = px.bar(data, x=x_col, y=y_col, color=y_col,
                             title=f"{agg} of {y_col} by {x_col}",
                             color_continuous_scale="Blues")
            else:
                fig = px.bar(data, x=y_col, y=x_col, orientation='h',
                             color=y_col, title=f"{agg} of {y_col} by {x_col}",
                             color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)

        elif ctype in ["Line Chart", "Area Chart"]:
            c1, c2 = st.columns(2)
            x_col = c1.selectbox("X axis", list(df_typed.columns), key=f"chart_x_{idx}")
            y_col = c2.selectbox("Y axis (Numeric)", num_cols, key=f"chart_y_{idx}")
            if ctype == "Line Chart":
                fig = px.line(df_typed, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
            else:
                fig = px.area(df_typed, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
            st.plotly_chart(fig, use_container_width=True)

        elif ctype in ["Pie Chart", "Donut Chart"]:
            c1, c2 = st.columns(2)
            name_col = c1.selectbox("Category", cat_cols, key=f"chart_x_{idx}")
            val_col = c2.selectbox("Value (Numeric)", num_cols, key=f"chart_y_{idx}")
            top_n = c1.slider("Top N", 5, 20, 10, key=f"chart_n_{idx}")
            data = df_typed.groupby(name_col)[val_col].sum().nlargest(top_n).reset_index()
            hole = 0.4 if ctype == "Donut Chart" else 0
            fig = px.pie(data, names=name_col, values=val_col,
                         title=f"{val_col} by {name_col}", hole=hole)
            st.plotly_chart(fig, use_container_width=True)

        elif ctype == "Scatter Plot":
            c1, c2, c3 = st.columns(3)
            x_col = c1.selectbox("X axis (Numeric)", num_cols, key=f"chart_x_{idx}")
            y_col = c2.selectbox("Y axis (Numeric)", num_cols, key=f"chart_y_{idx}")
            color_col = c3.selectbox("Color by", ["None"] + cat_cols, key=f"chart_c_{idx}")
            fig = px.scatter(df_typed, x=x_col, y=y_col,
                             color=None if color_col == "None" else color_col,
                             title=f"{x_col} vs {y_col}")
            st.plotly_chart(fig, use_container_width=True)

        elif ctype == "Box Plot":
            c1, c2 = st.columns(2)
            y_col = c1.selectbox("Numeric column", num_cols, key=f"chart_y_{idx}")
            group_col = c2.selectbox("Group by", ["None"] + cat_cols, key=f"chart_x_{idx}")
            fig = px.box(df_typed, y=y_col,
                         x=None if group_col == "None" else group_col,
                         title=f"Distribution of {y_col}")
            st.plotly_chart(fig, use_container_width=True)

        elif ctype == "Histogram":
            c1, c2 = st.columns(2)
            col = c1.selectbox("Numeric column", num_cols, key=f"chart_x_{idx}")
            bins = c2.slider("Bins", 5, 100, 20, key=f"chart_n_{idx}")
            fig = px.histogram(df_typed, x=col, nbins=bins,
                               title=f"Distribution of {col}",
                               color_discrete_sequence=["#1F77B4"])
            st.plotly_chart(fig, use_container_width=True)

        elif ctype == "Heatmap (Correlation)":
            if len(num_cols) < 2:
                st.warning("Need at least 2 numeric columns.")
            else:
                selected = st.multiselect("Select columns", num_cols,
                                          default=num_cols[:6], key=f"chart_x_{idx}")
                if len(selected) >= 2:
                    corr = df_typed[selected].corr()
                    fig = px.imshow(corr, text_auto=True,
                                    color_continuous_scale="RdBu",
                                    title="Correlation Heatmap")
                    st.plotly_chart(fig, use_container_width=True)

    with st.expander("➕ Add Custom Charts", expanded=False):
        for idx, chart_cfg in enumerate(st.session_state.chart_list):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.session_state.chart_list[idx]["type"] = st.selectbox(
                    f"Chart {idx+1} Type", CHART_TYPES,
                    index=CHART_TYPES.index(chart_cfg["type"]) if chart_cfg["type"] in CHART_TYPES else 0,
                    key=f"chart_type_{idx}"
                )
            with c2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Remove", key=f"remove_chart_{idx}"):
                    st.session_state.chart_list.pop(idx)
                    st.rerun()
            render_chart(st.session_state.chart_list[idx], idx)
            st.divider()

        if st.button("➕ Add Chart"):
            st.session_state.chart_list.append({"type": "Bar Chart"})
            st.rerun()

    st.divider()

    # ──────────────────────────────────────────
    # ── AUTO INSIGHTS & EXCEPTIONS ──
    # ──────────────────────────────────────────
    st.subheader("🧠 Auto-Generated Insights & Exceptions")

    insights = []
    warnings = []
    positives = []

    missing_pct = (df_raw.isnull().sum() / len(df_raw) * 100)
    for col in missing_pct[missing_pct > 10].index:
        warnings.append(f"⚠️ Column **{col}** had {missing_pct[col]:.1f}% missing values — filled with column average.")

    for col in num_cols:
        if col in df_typed.columns:
            Q1 = df_typed[col].quantile(0.25)
            Q3 = df_typed[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df_typed[(df_typed[col] < Q1 - 1.5 * IQR) | (df_typed[col] > Q3 + 1.5 * IQR)]
            if len(outliers) > 0:
                warnings.append(f"⚠️ Column **{col}** has {len(outliers):,} outlier(s) detected outside normal range.")

    for col in num_cols:
        if col in df_typed.columns:
            skew = df_typed[col].skew()
            if abs(skew) > 1.5:
                warnings.append(f"⚠️ Column **{col}** is heavily skewed (skew={skew:.2f}) — data is unevenly distributed.")

    if num_cols and cat_cols:
        top_col = num_cols[0]
        if top_col in df_typed.columns:
            top_row2 = df_typed.loc[df_typed[top_col].idxmax()]
            low_row2 = df_typed.loc[df_typed[top_col].idxmin()]
            positives.append(f"🏆 Highest **{top_col}**: **{top_row2[cat_cols[0]]}** with {top_row2[top_col]:,.2f}")
            warnings.append(f"🔻 Lowest **{top_col}**: **{low_row2[cat_cols[0]]}** with {low_row2[top_col]:,.2f}")

    if quality_score >= 90:
        positives.append(f"✅ Data quality score is **{quality_score:.1f}%** — excellent dataset quality!")
    elif quality_score >= 70:
        insights.append(f"ℹ️ Data quality score is **{quality_score:.1f}%** — acceptable but some gaps exist.")
    else:
        warnings.append(f"⚠️ Data quality score is **{quality_score:.1f}%** — dataset has significant missing data.")

    if len(df_typed) < 50:
        warnings.append(f"⚠️ Dataset is small ({len(df_typed)} records) — insights may not be fully reliable.")
    elif len(df_typed) >= 100:
        positives.append(f"✅ Dataset has {len(df_typed):,} records — sufficient for reliable analysis.")

    if dupes > 0:
        warnings.append(f"⚠️ {int(dupes):,} duplicate rows were found and removed from the dataset.")
    else:
        positives.append("✅ No duplicate records found — dataset is clean.")

    if positives:
        st.markdown("### 🟢 Positives")
        for p in positives:
            st.success(p)
    if insights:
        st.markdown("### 🔵 Insights")
        for i in insights:
            st.info(i)
    if warnings:
        st.markdown("### 🔴 Warnings & Exceptions")
        for w in warnings:
            st.warning(w)
    if not positives and not insights and not warnings:
        st.info("ℹ️ No significant insights detected for this dataset.")

else:
    st.info("👆 Please upload a CSV or Excel file to get started.")
