from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Certificate

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.patch("/certificates/<int:cert_id>/mapped")
def update_certificate_mapped(cert_id: int):
    """
    Body JSON:
      { "mapped_to_inventory": true }  OR  { "mapped_to_inventory": false }
    """
    payload = request.get_json(silent=True) or {}
    if "mapped_to_inventory" not in payload:
        return jsonify({"error": "mapped_to_inventory is required (true/false)"}), 400

    mapped = payload["mapped_to_inventory"]
    if not isinstance(mapped, bool):
        return jsonify({"error": "mapped_to_inventory must be boolean"}), 400

    cert = db.session.get(Certificate, cert_id)
    if cert is None:
        return jsonify({"error": "certificate not found"}), 404

    cert.mapped_to_inventory = mapped
    db.session.commit()

    return jsonify({
        "id": cert.id,
        "mapped_to_inventory": cert.mapped_to_inventory
    }), 200
