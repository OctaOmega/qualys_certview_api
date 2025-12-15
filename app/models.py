from datetime import datetime
from sqlalchemy import UniqueConstraint
from .extensions import db

class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.BigInteger, primary_key=True)  # Qualys "id"
    certhash = db.Column(db.String(128), index=True)
    serial_number = db.Column(db.String(128), index=True)
    dn = db.Column(db.String(1024), index=True)
    cert_type = db.Column(db.String(64), index=True)  # "Root"
    signature_algorithm = db.Column(db.String(128))
    key_size = db.Column(db.Integer)
    self_signed = db.Column(db.Boolean)
    extended_validation = db.Column(db.Boolean)

    valid_from_date = db.Column(db.DateTime, nullable=True)
    valid_to_date = db.Column(db.DateTime, nullable=True)

    created_date = db.Column(db.DateTime, nullable=True)
    update_date = db.Column(db.DateTime, nullable=True)

    issuer_category = db.Column(db.String(128), nullable=True)
    instance_count = db.Column(db.Integer, nullable=True)
    asset_count = db.Column(db.Integer, nullable=True)

    sources_json = db.Column(db.Text, nullable=True)     # store list as JSON string
    subject_json = db.Column(db.Text, nullable=True)     # store dict as JSON string
    issuer_json = db.Column(db.Text, nullable=True)      # store dict as JSON string

    # REQUIRED extra fields:
    page_range = db.Column(db.String(32), nullable=False)          # e.g. "0-99"
    mapped_to_inventory = db.Column(db.Boolean, default=False)     # yes/no

    inserted_at = db.Column(db.DateTime, default=datetime.utcnow)

    assets = db.relationship("Asset", backref="certificate", cascade="all, delete-orphan", lazy=True)

class Asset(db.Model):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("certificate_id", "asset_id", name="uq_asset_per_cert"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    certificate_id = db.Column(db.BigInteger, db.ForeignKey("certificates.id"), nullable=False)

    # Qualys asset "id"
    asset_id = db.Column(db.BigInteger, nullable=False, index=True)
    uuid = db.Column(db.String(64), nullable=True, index=True)
    name = db.Column(db.String(512), nullable=True, index=True)
    netbios_name = db.Column(db.String(256), nullable=True, index=True)
    operating_system = db.Column(db.String(256), nullable=True)

    primary_ip = db.Column(db.String(64), nullable=True, index=True)

    host_instances_json = db.Column(db.Text, nullable=True)      # list of instances
    asset_interfaces_json = db.Column(db.Text, nullable=True)    # list of interfaces

    inserted_at = db.Column(db.DateTime, default=datetime.utcnow)

class ApiLog(db.Model):
    __tablename__ = "api_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    endpoint = db.Column(db.String(256), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    page_size = db.Column(db.Integer, nullable=False)
    page_range = db.Column(db.String(32), nullable=False)
    status_code = db.Column(db.Integer, nullable=True)

    request_body_json = db.Column(db.Text, nullable=False)
    response_count = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class QualysAuthToken(db.Model):
    __tablename__ = "qualys_auth_tokens"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    token_value = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    valid = db.Column(db.Boolean, nullable=False, default=True)

    # optional tracking
    auth_url = db.Column(db.String(512), nullable=True)
    status_code = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)