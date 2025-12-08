import pyodbc
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import date
from dotenv import load_dotenv
import os

# --- Load environment variables ---
load_dotenv()

DB_DRIVER = os.getenv("DB_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

EMAIL_RECEIVERS = [email.strip() for email in os.getenv("EMAIL_RECEIVERS").split(",")]

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

# --- Database Connection ---
conn = pyodbc.connect(
    f"DRIVER={{{DB_DRIVER}}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD}"
)
cursor = conn.cursor()

# --- Updated SQL Query (9 AM logic & consumption calculation) ---
query = """
DECLARE @Today DATETIME = CAST(GETDATE() AS DATETIME);
DECLARE @Yesterday DATETIME = DATEADD(DAY, -1, @Today);

WITH Reading9AM AS (
    SELECT 
        TankCode,
        CAST(CAST(CapDate AS DATE) AS DATE) AS ReadingDate,
        ROUND(CAST(WeightValue AS FLOAT), 2) AS Weight_9AM,
        ROUND(CAST(LevelValue AS FLOAT), 2) AS Level_9AM,
        ROUND(CAST(TempValue AS FLOAT), 2) AS Temp_9AM,
        CapDate,
        ROW_NUMBER() OVER (
            PARTITION BY TankCode, CAST(CapDate AS DATE)
            ORDER BY ABS(DATEDIFF(SECOND, CapDate, 
                     DATEADD(HOUR, 9, CAST(CAST(CapDate AS DATE) AS DATETIME))))
        ) AS rn
    FROM ChemTankReadings
    WHERE 
        CAST(CapDate AS TIME) BETWEEN '06:00:00' AND '12:00:00'
        AND (TankCode LIKE 'ISO%' OR TankCode LIKE 'POLY%')
),

TodayData AS (
    SELECT TankCode, Weight_9AM, Level_9AM, Temp_9AM, CapDate
    FROM Reading9AM
    WHERE rn = 1 AND ReadingDate = CAST(@Today AS DATE)
),

YesterdayData AS (
    SELECT TankCode, Weight_9AM
    FROM Reading9AM
    WHERE rn = 1 AND ReadingDate = CAST(@Yesterday AS DATE)
)

SELECT 
    t.TankCode,
    FORMAT(t.CapDate, 'dd-MM-yyyy HH:mm:ss') AS ReadingTime_9AM,
    t.Weight_9AM,
    t.Level_9AM,
    t.Temp_9AM,
    ROUND(y.Weight_9AM - t.Weight_9AM, 2) AS Consumption
FROM TodayData t
LEFT JOIN YesterdayData y 
    ON t.TankCode = y.TankCode
ORDER BY 
    CASE WHEN t.TankCode LIKE 'ISO%' THEN 1 ELSE 2 END,
    t.TankCode;
"""

cursor.execute(query)
data = cursor.fetchall()
columns = [column[0] for column in cursor.description]
df = pd.DataFrame([tuple(t) for t in data], columns=columns)

# --- Convert numeric columns ---
numeric_cols = ['Weight_9AM', 'Level_9AM', 'Temp_9AM', 'Consumption']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').round(2)

# --- Format Date ---
df['ReadingTime_9AM'] = pd.to_datetime(df['ReadingTime_9AM']).dt.strftime('%d-%m-%Y %H:%M')

# --- Split ISO & POLY groups ---
iso_df = df[df['TankCode'].str.contains('ISO')]
poly_df = df[df['TankCode'].str.contains('Poly')]

# --- Build HTML formatted tables ---
html = """
<html>
  <body>
    <h2 style="font-family: Arial, sans-serif;">Daily Chemical Tank Report</h2>
"""

def build_table(df_group, title, color):
    table_html = f"""
    <h3 style="background-color:{color}; color:white; padding:5px;">{title}</h3>
    <table border="1" cellpadding="5" cellspacing="0"
           style="border-collapse: collapse; font-family: Arial; width:90%;">
      <tr style="background-color:#f2f2f2; text-align:center;">
        <th>Tank Code</th>
        <th>Weight @ 9 AM (kg)</th>
        <th>Level @ 9 AM (mm)</th>
        <th>Temp @ 9 AM (°C)</th>
        <th>Consumption (kg)</th>
        <th>Reading Time</th>
      </tr>
    """
    for _, row in df_group.iterrows():
        table_html += f"""
        <tr>
            <td>{row['TankCode']}</td>
            <td>{row['Weight_9AM']}</td>
            <td>{row['Level_9AM']}</td>
            <td>{row['Temp_9AM']}</td>
            <td>{row['Consumption']}</td>
            <td>{row['ReadingTime_9AM']}</td>
        </tr>
        """
    table_html += "</table><br>"
    return table_html

html += build_table(iso_df, "ISOCYANATE CHEMICAL DATA", "#e74c3c")
html += build_table(poly_df, "RAW POLYOL CHEMICAL DATA", "#27ae60")

html += "</body></html>"

# --- Save CSV ---
filename = f"DailyReport_{date.today()}.csv"
df.to_csv(filename, index=False)

# --- Prepare Email ---
msg = MIMEMultipart("alternative")
msg['From'] = EMAIL_SENDER
msg['To'] = ", ".join(EMAIL_RECEIVERS)
msg['Subject'] = "Daily Chemical Tank Report"

msg.attach(MIMEText("Please find today's ChemTank report attached and below.", 'plain'))
msg.attach(MIMEText(html, 'html'))

with open(filename, "rb") as attachment:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename={filename}")
    msg.attach(part)

# --- Send Email ---
server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
server.starttls()
server.login(EMAIL_SENDER, EMAIL_PASSWORD)
server.send_message(msg)
server.quit()

print("Email sent successfully with formatted HTML tables and CSV attachment!")