import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # MSSQL LocalDB example:
    # Server=(localdb)\MSSQLLocalDB;Database=QualysCertDB;Trusted_Connection=yes;TrustServerCertificate=yes;
    MSSQL_ODBC_CONN_STR = os.getenv(
        "MSSQL_ODBC_CONN_STR",
        r"DRIVER={ODBC Driver 18 for SQL Server};"
        r"SERVER=(localdb)\MSSQLLocalDB;"
        r"DATABASE=QualysCertDB;"
        r"Trusted_Connection=yes;"
        r"TrustServerCertificate=yes;"
    )

    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect=" + MSSQL_ODBC_CONN_STR.replace(";", "%3B").replace("=", "%3D")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    QUALYS_BASE_URL = os.getenv("QUALYS_BASE_URL", "https://qualys_base_url")
    #QUALYS_JWT = os.getenv("QUALYS_JWT", "")
    QUALYS_PAGE_SIZE = int(os.getenv("QUALYS_PAGE_SIZE", "100"))  # adjust as needed
    QUALYS_TIMEOUT_SECS = int(os.getenv("QUALYS_TIMEOUT_SECS", "60"))
    QUALYS_USERNAME = os.getenv("QUALYS_USERNAME", "")
    QUALYS_PASSWORD = os.getenv("QUALYS_PASSWORD", "")
    QUALYS_AUTH_URL = os.getenv("QUALYS_AUTH_URL", "https://gateway.qg3.apps.qualys.com/auth")
