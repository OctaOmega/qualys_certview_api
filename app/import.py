import pandas as pd
from typing import Dict, List, Tuple, IO


def normalize_serial(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def normalize_value(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    return value


def fetch_existing_serials(
    cursor,
    table: str,
    serial_col: str,
    serials: List[str],
    batch_size: int = 1500,
) -> set[str]:
    existing = set()

    for i in range(0, len(serials), batch_size):
        batch = serials[i : i + batch_size]
        placeholders = ",".join("?" * len(batch))
        sql = f"""
            SELECT {serial_col}
            FROM {table}
            WHERE {serial_col} IN ({placeholders})
        """
        cursor.execute(sql, batch)
        existing.update(row[0] for row in cursor.fetchall())

    return existing


def import_leafcert_csv(
    file_handle: IO,
    cursor,
    table: str = "qualysLeafcertificates",
    serial_col: str = "serial_number",
    chunksize: int = 5000,
):
    """
    Reads CSV from file handler and inserts only new certificates
    based on serial number.
    """

    # DB column -> CSV column
    column_map: Dict[str, str] = {
        "serial_number": "Serial number",
        "cert_name": "Cert name",
        "certhash": "Cert hash",
        "valid_from_date": "Valid from",
        "valid_to_date": "Valid to",
        "certificate_status": "Cert status",
    }

    db_columns = list(column_map.keys())
    insert_sql = f"""
        INSERT INTO {table} ({",".join(db_columns)})
        VALUES ({",".join("?" * len(db_columns))})
    """

    reader = pd.read_csv(
        file_handle,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
    )

    cursor.fast_executemany = True

    for chunk in reader:
        serials = (
            chunk[column_map[serial_col]]
            .map(normalize_serial)
            .dropna()
            .tolist()
        )

        if not serials:
            continue

        existing_serials = fetch_existing_serials(
            cursor,
            table,
            serial_col,
            serials,
        )

        rows_to_insert: List[Tuple] = []

        for _, row in chunk.iterrows():
            serial = normalize_serial(row[column_map[serial_col]])
            if not serial or serial in existing_serials:
                continue

            values = tuple(
                normalize_value(row[column_map[col]])
                for col in db_columns
            )
            rows_to_insert.append(values)

        if rows_to_insert:
            cursor.executemany(insert_sql, rows_to_insert)



with open("leaf_certs.csv", "r", encoding="utf-8") as f:
    import_leafcert_csv(
        file_handle=f,
        cursor=mssql_cursor,   # already connected
    )

mssql_conn.commit()
