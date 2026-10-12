# Supermarket Sales Analytics Dashboard
An end-to-end data analytics and machine learning solution built for the **Data Analytics Masterclass Internship**. This project covers dataset cleaning, exploratory data analysis (EDA), customer segmentation using RFM (Recency, Frequency, Monetary) features, a predictive churn classifier (Logistic Regression), and an interactive Streamlit dashboard.

---

## 1. Project Description
The primary objective of this project is to analyze transaction patterns across a retail supermarket dataset, identify revenue drivers and seasonal risks, and construct a predictive customer retention model to flag churn risks before buyers stop purchasing.

### Key Objectives:
* **Data Ingestion &amp; Cleaning:** Standardize dates, numeric fields, currency strings, and handle missing values across 1,000 transaction records.
* **Exploratory Data Analysis (EDA):** Analyze monthly trends, category performance, regional distribution, and top profit drivers using visual charts.
* **4-Step Analytical Framework:** Formulate 5 Observations, 5 Insights, 3 Hypotheses, and 3 Actionable Recommendations (5-5-3-3 framework).
* **Predictive Churn Modeling:** Engineer RFM metrics, establish inactivity thresholds (\\(\ge\\)180 days), train a Logistic Regression model, and segment customers into risk tiers.
* **Interactive UI Dashboard:** Build a multi-tab Streamlit web application (`app.py`) for dynamic metric filtering and executive reporting.

---

## 2. Dataset Information
* **Dataset File Path / Name:** `supermarket_sales_cleaned.csv`
* **Total Transactions:** 1,000 orders
* **Total Unique Customers:** 363 buyers
* **Total Revenue:** ₹890,816.73
* **Total Net Profit:** ₹162,931.85 (18.29% net profit margin)
* **Average Order Value (AOV):** ₹890.82
* **Columns Included:** `Invoice ID`, `Order Date`, `Customer ID`, `Product Category`, `Product`, `Region`, `Quantity`, `Unit Price`, `Revenue`, `Profit`.

---

## 3. Key Business Information &amp; Findings (5-5-3-3 Framework)

### Key Analytical Observations (Facts):
1. **Peak Sales:** October 2025 generated the highest monthly sales (₹98,310.45), while August 2025 hit the lowest slump (₹55,376.09)—a **43.7% seasonal gap**.
2. **Category Leader:** **Electronics** is the primary driver, accounting for **45.98% of total revenue** (₹409,629.62) and **51.26% of total profit** (₹83,522.75).
3. **Customer Loyalty:** **76.03% (276 buyers)** are repeat customers, while **23.97% (87 buyers)** are single-order shoppers.
4. **Top Region:** The **East region** leads overall branch sales at ₹196,254.33, while the West region ranks lowest at ₹159,384.67.
5. **Top Product Drivers:** **Power Banks** (₹38,995.11 profit) and **Earphones** (₹25,125.53 profit) yield the highest absolute profit margins.

### Key Strategic Decisions:
* **Peak Cash Reserves:** Set aside profits from peak months (October/December) to buffer fixed operating costs during quiet months (August/April).
* **Automated Re-Engagement:** Deploy automated email/SMS win-back offers for customers reaching 90+ days of inactivity.
* **Cross-Category Bundling:** Bundle high-margin Electronics accessories with fast-moving, lower-margin Groceries.

---

## 4. Technologies Used
* **Programming Language:** Python 3.12
* **Data Processing &amp; Math:** Pandas, NumPy
* **Data Visualisation:** Matplotlib, Seaborn
* **Machine Learning:** Scikit-Learn (Logistic Regression, Confusion Matrix, Train/Test Split)
* **Interactive Web UI:** Streamlit
* **Document &amp; Report Generation:** Python-Docx

---

## 5. Setup and Run Instructions

### Step 1: Install Dependencies
Ensure Python 3.9+ is installed, then run the following command in your terminal:
```bash
pip install -r requirements.txt

```

### Step 2: Run the Streamlit Dashboard

Launch the interactive web interface locally:

```
streamlit run app.py

```

Open `http://localhost:8501` in your browser to view the dashboard.

## Files
- `app.py`: Streamlit dashboard
- `requirements.txt`: Python dependencies
- `supermarket_sales_cleaned.csv`: place your cleaned dataset here

## Run on Windows
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, open Command Prompt and run `.venv\Scripts\activate.bat` instead.

The dashboard expects these columns:
`Invoice ID`, `Order Date`, `Customer ID`, `Product Category`, `Product`, `Region`, `Quantity`, `Unit Price`, `Revenue`, `Profit`.

Churn note: the 180-day inactivity group is a rule-based risk flag calculated relative to the latest order date in the dataset. It is not a validated predictive model.
