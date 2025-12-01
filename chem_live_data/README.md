# 📧 Daily Chemical Tank Report Automation

This repository contains a Python automation script that connects to a SQL Server database, retrieves daily chemical tank readings, formats the data into HTML email tables, exports a CSV file, and sends the report via email.

The script is designed to run automatically (e.g., using Task Scheduler / Cron) and deliver neatly formatted chemical tank data for operational monitoring.

---

## 🚀 Features

* Connects to **SQL Server** using `pyodbc`
* Fetches **first tank reading after 9:00 AM** for the current day
* Splits data into two categories:

  * **ISO Chemical Data**
  * **Polyol Chemical Data**
* Cleans & formats dataset using **pandas**
* Generates:

  * **HTML email** with color-coded tables
  * **CSV report** saved locally
* Sends the report via **SMTP email** with:

  * HTML content
  * Plain text fallback
  * CSV attachment

---

## 📂 Workflow Overview

1. **Database Query**  
   Connects to SQL Server and runs a query to get tank readings grouped by `TankCode`.

2. **Data Processing**

   * Converts numeric columns  
   * Formats timestamps  
   * Splits into ISO and Poly groups  

3. **HTML Report Generation**  
   Creates color-coded, structured tables for readability.

4. **CSV Export**  
   Saves a local copy of the full dataset.

5. **Email Delivery**  
   Uses SMTP to send:

   * Email body (HTML + text)
   * CSV attachment

---

## 🛠️ Requirements

Install dependencies:

```bash
pip install pyodbc pandas python-dotenv
````

Built-in modules used:

* `smtplib`
* `email`
* `datetime`
* `os`

---

# ⚙️ Setup Instructions (Added Section)

Follow these steps to prepare and run the script:

---

## 1. Clone the Repository

```bash
git clone https://github.com/Varunyadavgithub/WRL-Scripts
cd chem_live_data
```

---

## 2. Create a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, run:

```bash
pip install pyodbc pandas python-dotenv
```

---

## 4. Create a `.env` File

Create a file named `.env` in the project directory with:

```
DB_DRIVER=SQL Server
DB_SERVER=your_server
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password

EMAIL_SENDER=your_email
EMAIL_PASSWORD=your_email_password
EMAIL_RECEIVERS=email1@example.com, email2@example.com

SMTP_SERVER=smtp_server_ip
SMTP_PORT=587
```



---

## 5. Run the Script

```bash
python daily_chem_reporta.py
```

---

# 🤖 Automation Setup (Added Section)

## 🔹 Windows Task Scheduler

1. Open **Task Scheduler**
2. Create a new task
3. Trigger → Daily at your chosen time
4. Action →

   * Program: `python.exe`
   * Add arguments: `path\to\daily_chem_report.py`

---

## 🔹 Linux Cron Job

Run:

```bash
crontab -e
```

Add:

```
0 9 * * * /usr/bin/python3 /path/to/daily_chem_report.py
```

---

# 📂 Folder Structure (Added Section)

```
/
├── daily_chem_report.py
├── .env                     # (Not committed)
├── .gitignore
├── README.md
├── requirements.txt         # optional
└── DailyReport_YYYY-MM-DD.csv   # auto-generated
```

---

## 📤 Output

### ✔ HTML Email

Includes formatted ISO (red) and Polyol (green) tables.

### ✔ CSV Report

Example name:

```
DailyReport_2025-01-12.csv
```

---

## 📞 Support / Contact

For improvements, issues, or automation help, feel free to update or open an issue in the repository.