# 📊 InsightFlow – Analytics & Decision Engine
**InsightFlow**
Developed by: Ashwath D. M. & Ayesha Safiya

---

## 📌 What This Project Does

InsightFlow is a lightweight data analytics application that transforms any business dataset (CSV or Excel) into meaningful KPIs, visual dashboards, and automated insights — with zero manual configuration required.

**Demo Flow:**
```
Upload File → Clean Data → Auto KPIs → Charts → Insights
```

---

## 🚀 How to Run the App

### Step 1 — Make sure Python is installed
Open Command Prompt and run:
```
python --version
```
You should see `Python 3.x.x`. If not, download Python from https://www.python.org

---

### Step 2 — Install dependencies
Navigate to the project folder and run:
```
cd C:\Projects\InsightFlow
pip install -r requirements.txt
```

---

### Step 3 — Run the app
```
streamlit run app.py
```
The app will automatically open in your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
InsightFlow/
│
├── InsightFlow_app_final.py   # Main application file
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── Car_sales.csv           # Sample dataset for testing
```

---

## ✅ Features

### 📂 Data Upload
- Supports CSV and Excel (.xlsx) files
- Auto-detects file encoding (handles UTF-8 and Latin-1)
- Displays record and column count on upload

### 🧹 Data Cleaning (Automatic)
- Removes duplicate rows
- Fills missing numeric values with column mean
- Fills missing text values with 'Unknown'
- Detects and converts date columns automatically
- Shows a cleaning summary (before vs after)

### 🔧 Column Type Editor
- View all columns and their detected types
- Manually change any column between Numeric, Text, or Date
- All KPIs and charts update based on your selection

### 📊 Auto-Generated KPIs (12 KPIs)
Automatically generated the moment a file is uploaded:
- **Numeric Summary** — Mean, Sum, Max, Min of top numeric columns
- **Top & Bottom** — Highest record, Lowest record, Most common category, Unique count
- **Data Quality** — Total records, Total columns, Missing values fixed, Quality score

Each KPI card supports:
- Changing aggregation (Mean / Sum / Min / Max / Median / Count / Std Dev)
- Adjusting decimal points (0–4)
- Toggling comma formatting on/off
- Removing individual KPI cards with 🗑️
- Restoring removed KPIs with ↩️ Restore

### ➕ Custom KPI Builder
- Add unlimited custom numeric KPIs
- Add custom categorical KPIs (Most Common, Least Common, Unique Count, Top 3 Values)
- Remove any custom KPI with 🗑️

### 📈 Auto-Generated Charts (4 Charts)
Automatically generated based on dataset columns:
1. **Bar Chart** — Top 10 records by any category and numeric column
2. **Pie Chart** — Category breakdown by value
3. **Histogram** — Distribution of any numeric column
4. **Correlation Heatmap** — Relationships between all numeric columns

Each chart can be hidden with 🗑️ Remove and restored by clicking again.

### ➕ Custom Chart Builder
Add unlimited additional charts from 10 available types:
- Bar Chart, Horizontal Bar
- Line Chart, Area Chart
- Pie Chart, Donut Chart
- Scatter Plot, Box Plot
- Histogram
- Heatmap (Correlation)

### 🧠 Auto-Generated Insights & Exceptions
Automatically flags:
- Columns with high missing data (>10%)
- Outliers detected outside normal range
- Heavily skewed distributions
- Top and bottom performing records
- Data quality score
- Duplicate row detection

### 📥 Download
- Download the fully cleaned dataset as a CSV at any time

---

## 🧪 Tested Datasets
The app has been tested with the following datasets:
1. **Car Sales Dataset** — 157 records, 16 columns
2. **DataCo Supply Chain Dataset** — Large dataset with mixed encoding
3. Additional dataset

All datasets loaded, cleaned, and generated KPIs and charts successfully.

---

## ⚙️ Tech Stack

| Tool | Purpose |
|---|---|
| Python 3 | Core programming language |
| Streamlit | Dashboard UI framework |
| Pandas | Data processing and cleaning |
| Plotly | Interactive charts and visualisations |
| OpenPyXL | Excel file support |

---

## 📋 Assumptions
1. The app supports CSV and Excel (.xlsx) files only
2. Missing numeric values are filled with the column mean
3. Missing text values are filled with 'Unknown'
4. The app runs locally
5. Insights are rule-based, not AI/ML based
6. No authentication or user management is required

---

## ❓ Known Limitations
- Very large datasets (500,000+ rows) may slow down the app slightly
- Date column auto-detection works best when dates are in standard formats
- Heatmap requires at least 2 numeric columns to render

---

---
*Created for educational and portfolio purposes.*
