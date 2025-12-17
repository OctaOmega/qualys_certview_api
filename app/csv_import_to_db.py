import csv
from typing import IO, Dict, Any, Optional
from sqlalchemy.orm import Session

# Your existing SQLAlchemy model
# from yourapp.models import QualysLeafCertificates


def _norm(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def import_leaf_certs_row_by_row(
    file_handle: IO[str],
    session: Session,
    Model,  # QualysLeafCertificates
    *,
    csv_to_model_map: Dict[str, str],
    serial_csv_col: str = "Serial Number",
    serial_model_field: str = "SerialNumber",
    commit_every: int = 2000,
) -> None:
    """
    Reads CSV row-by-row and:
      1) checks existence with: session.query(Model).filter_by(SerialNumber=...).first()
      2) inserts a new Model instance if not found

    - file_handle: already-open text file handler
    - session: active SQLAlchemy Session (DB connection already covered by you)
    - Model: your SQLAlchemy model class (QualysLeafCertificates)
    - csv_to_model_map: maps CSV column -> Model field, e.g. {"Serial Number": "SerialNumber"}
    - commit_every: commit in batches to avoid huge transactions
    """

    reader = csv.DictReader(file_handle)

    pending = 0
    for row in reader:
        serial_value = _norm(row.get(serial_csv_col))
        if not serial_value:
            continue

        # Existence check exactly as requested (filter_by per row)
        exists = (
            session.query(Model)
            .filter_by(**{serial_model_field: serial_value})
            .first()
        )
        if exists:
            continue

        obj = Model()

        # Populate model fields from CSV based on mapping
        for csv_col, model_field in csv_to_model_map.items():
            if csv_col not in row:
                continue
            setattr(obj, model_field, _norm(row.get(csv_col)))

        session.add(obj)
        pending += 1

        if pending >= commit_every:
            session.commit()
            pending = 0

    if pending:
        session.commit()


# -------------------------
# Example usage
# -------------------------
"""
csv_to_model_map = {
    "Serial Number": "SerialNumber",
    "Cert Name": "CertName",
    "Cert Hash": "CertHash",
    "Validity": "Validity",
    "Valid From": "ValidFromDate",
    "Valid To": "ValidToDate",
    # add all required CSV->Model mappings here
}

with open("leafcerts.csv", "r", encoding="utf-8", newline="") as f:
    import_leaf_certs_row_by_row(
        file_handle=f,
        session=db.session,  # your SQLAlchemy session
        Model=QualysLeafCertificates,
        csv_to_model_map=csv_to_model_map,
        serial_csv_col="Serial Number",
        serial_model_field="SerialNumber",
        commit_every=2000,
    )
"""
