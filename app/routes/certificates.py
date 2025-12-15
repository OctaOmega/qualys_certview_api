import csv
import io
from flask import Blueprint, request, render_template, Response
from ..models import Certificate
from ..extensions import db

bp = Blueprint("certificates", __name__, url_prefix="/certificates")

@bp.get("")
def list_certificates():
    q = Certificate.query

    # simple search
    certhash = request.args.get("certhash")
    serial = request.args.get("serial")
    dn = request.args.get("dn")
    cert_type = request.args.get("type")
    mapped = request.args.get("mapped")  # "true"/"false"

    if certhash:
        q = q.filter(Certificate.certhash.ilike(f"%{certhash}%"))
    if serial:
        q = q.filter(Certificate.serial_number.ilike(f"%{serial}%"))
    if dn:
        q = q.filter(Certificate.dn.ilike(f"%{dn}%"))
    if cert_type:
        q = q.filter(Certificate.cert_type.ilike(f"%{cert_type}%"))
    if mapped in ("true", "false"):
        q = q.filter(Certificate.mapped_to_inventory.is_(mapped == "true"))

    q = q.order_by(Certificate.id.desc())

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    results = q.paginate(page=page, per_page=per_page, error_out=False)

    return render_template("certificates.html", results=results, args=request.args)

@bp.get("export.csv")
def export_certificates_csv():
    q = Certificate.query.order_by(Certificate.id.desc()).limit(200000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id","certhash","serial_number","dn","cert_type","key_size","signature_algorithm",
        "self_signed","valid_from_date","valid_to_date","page_range","mapped_to_inventory"
    ])

    for c in q:
        writer.writerow([
            c.id, c.certhash, c.serial_number, c.dn, c.cert_type, c.key_size,
            c.signature_algorithm, c.self_signed, c.valid_from_date, c.valid_to_date,
            c.page_range, c.mapped_to_inventory
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=certificates.csv"},
    )
