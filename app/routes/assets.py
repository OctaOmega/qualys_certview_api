import csv
import io
from flask import Blueprint, request, render_template, Response
from ..models import Asset

bp = Blueprint("assets", __name__, url_prefix="/assets")

@bp.get("")
def list_assets():
    q = Asset.query

    name = request.args.get("name")
    uuid = request.args.get("uuid")
    ip = request.args.get("ip")
    os = request.args.get("os")
    cert_id = request.args.get("cert_id")

    if name:
        q = q.filter(Asset.name.ilike(f"%{name}%"))
    if uuid:
        q = q.filter(Asset.uuid.ilike(f"%{uuid}%"))
    if ip:
        q = q.filter(Asset.primary_ip.ilike(f"%{ip}%"))
    if os:
        q = q.filter(Asset.operating_system.ilike(f"%{os}%"))
    if cert_id:
        q = q.filter(Asset.certificate_id == cert_id)

    q = q.order_by(Asset.id.desc())

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    results = q.paginate(page=page, per_page=per_page, error_out=False)

    return render_template("assets.html", results=results, args=request.args)

@bp.get("export.csv")
def export_assets_csv():
    q = Asset.query.order_by(Asset.id.desc()).limit(200000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id","certificate_id","asset_id","uuid","name","netbios_name","operating_system","primary_ip"
    ])

    for a in q:
        writer.writerow([
            a.id, a.certificate_id, a.asset_id, a.uuid, a.name, a.netbios_name, a.operating_system, a.primary_ip
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=assets.csv"},
    )
