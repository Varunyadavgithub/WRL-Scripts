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

# Supports multiple comma-separated emails
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

# --- Fetch Today’s Data ---
query = """
SELECT TankCode, WeightValue, LevelValue, TempValue, CapDate
FROM (
    SELECT TankCode, WeightValue, LevelValue, TempValue, CapDate,
           ROW_NUMBER() OVER (PARTITION BY TankCode ORDER BY CapDate ASC) AS rn
    FROM ChemTankReadings
    WHERE CAST(CapDate AS TIME) >= '09:00:00'
      AND CAST(CapDate AS DATE) = CAST(GETDATE() AS DATE)
) t
WHERE rn = 1
ORDER BY 
    CASE WHEN TankCode LIKE 'ISO%' THEN 1 ELSE 2 END,
    CAST(RIGHT(TankCode, 1) AS INT);
"""
cursor.execute(query)
data = cursor.fetchall()
columns = [column[0] for column in cursor.description]
df = pd.DataFrame([tuple(t) for t in data], columns=columns)

# --- Convert numeric columns ---
numeric_cols = ['WeightValue', 'LevelValue', 'TempValue']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# --- Format CapDate nicely ---
df['CapDate'] = pd.to_datetime(df['CapDate']).dt.strftime('%d-%m-%Y %H:%M')

# --- Split ISO & POLY groups ---
iso_df = df[df['TankCode'].str.contains('ISO')]
poly_df = df[df['TankCode'].str.contains('Poly')]

# --- Build HTML ---
html = """
<html>
  <body>
    <h2 style="font-family: Arial, sans-serif;">Daily Chemical Tank Report</h2>
"""

def build_table(df_group, title, color):
    table_html = f"""
    <h3 style="background-color:{color}; color:white; padding:5px;">{title}</h3>
    <table border="1" cellpadding="5" cellspacing="0" 
           style="border-collapse: collapse; font-family: Arial, sans-serif; width:60%;">
      <tr style="background-color:#f2f2f2; text-align:center;">
    """
    for col in ['TankCode', 'WeightValue', 'LevelValue', 'CapDate']:
        table_html += f"<th>{col}</th>"
    table_html += "</tr>"

    for index, row in df_group.iterrows():
        table_html += "<tr>"
        for col in ['TankCode', 'WeightValue', 'LevelValue', 'CapDate']:
            table_html += f"<td>{row[col]}</td>"
        table_html += "</tr>"

    table_html += "</table><br>"
    return table_html

# Add tables
html += build_table(iso_df, "ISOCYANTE CHEMICAL DATA", "#e74c3c")
html += build_table(poly_df, "RAW POLYOL CHEMICAL DATA", "#27ae60")

html += "</body></html>"

# --- Save CSV ---
filename = f"DailyReport_{date.today()}.csv"
df.to_csv(filename, index=False)

# --- Send Email ---
msg = MIMEMultipart("alternative")
msg['From'] = EMAIL_SENDER
msg['To'] = ", ".join(EMAIL_RECEIVERS)
msg['Subject'] = "Daily Chemical Tank Report"

# Attach text & HTML
msg.attach(MIMEText("Please find today's ChemTank report attached and below.", 'plain'))
msg.attach(MIMEText(html, 'html'))

# Attach CSV file
with open(filename, "rb") as attachment:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename={filename}")
    msg.attach(part)

# --- Send Email via SMTP ---
server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
server.ehlo()
server.starttls()
server.login(EMAIL_SENDER, EMAIL_PASSWORD)
server.send_message(msg)
server.quit()

print("Email sent successfully with formatted HTML tables and CSV attachment!")