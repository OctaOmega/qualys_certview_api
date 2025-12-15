from flask import Blueprint, render_template, request
from ..services.sync_service import sync_all_certificates
from ..models import ApiLog

bp = Blueprint("sync", __name__, url_prefix="/sync")

@bp.get("")
def sync_page():
    logs = ApiLog.query.order_by(ApiLog.id.desc()).limit(200).all()
    return render_template("sync.html", logs=logs)

@bp.post("")
def run_sync():
    # Optional overrides from form
    filter_value = request.form.get("filter_value", "root")
    asset_type = request.form.get("asset_type", "MANAGED")

    result = sync_all_certificates(filter_value=filter_value, asset_type=asset_type)
    logs = ApiLog.query.order_by(ApiLog.id.desc()).limit(200).all()
    return render_template("sync.html", logs=logs, result=result)
