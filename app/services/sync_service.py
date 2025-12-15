import json
from datetime import datetime
from flask import current_app
from ..extensions import db
from ..models import Certificate, Asset, ApiLog
from .external_jwt_qualys_client import QualysClient

def _parse_dt(dt_str: str):
    # example: "2038-01-15T12:00:00.000+00:00"
    if not dt_str:
        return None
    try:
        # Python can parse ISO with offset using fromisoformat in most cases
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None

def _page_range(page_number: int, page_size: int) -> str:
    start = page_number * page_size
    end = start + page_size - 1
    return f"{start}-{end}"

def sync_all_certificates(filter_value="root", includes=None, asset_type="MANAGED"):
    includes = includes or ["ASSET_INTERFACES"]

    cfg = current_app.config
    #Used with External JWT
    #client = QualysClient(cfg["QUALYS_BASE_URL"], cfg["QUALYS_JWT"], cfg["QUALYS_TIMEOUT_SECS"])

    client = QualysClient(
    cfg["QUALYS_BASE_URL"],
    cfg["QUALYS_AUTH_URL"],
    cfg["QUALYS_USERNAME"],
    cfg["QUALYS_PASSWORD"],
    cfg["QUALYS_TIMEOUT_SECS"],
    )
    
    page_size = cfg["QUALYS_PAGE_SIZE"]

    page_number = 0
    total_inserted = 0

    while True:
        page_range = _page_range(page_number, page_size)

        payload = {
            "filter": {
                "filters": [
                    {"field": "certificate.type", "value": filter_value, "operator": "EQUALS"}
                ],
                "operation": "AND",
            },
            "pageNumber": page_number,
            "pageSize": page_size,
            "includes": includes,
            "assetType": asset_type,
        }

        log = ApiLog(
            endpoint="/certview/v1/certificates",
            page_number=page_number,
            page_size=page_size,
            page_range=page_range,
            request_body_json=json.dumps(payload),
        )
        db.session.add(log)
        db.session.flush()  # get log id

        try:
            resp = client.list_certificates(payload)
            log.status_code = resp.status_code

            if resp.status_code != 200:
                log.error_message = f"Non-200 response: {resp.text[:2000]}"
                db.session.commit()
                break

            data = resp.json()
            if not isinstance(data, list) or len(data) == 0:
                log.response_count = 0
                db.session.commit()
                break

            log.response_count = len(data)

            # Insert certificates + assets
            inserted_this_page = 0

            for item in data:
                cert_id = item.get("id")
                if cert_id is None:
                    continue

                cert = db.session.get(Certificate, cert_id)
                if cert is None:
                    cert = Certificate(id=cert_id)

                cert.certhash = item.get("certhash")
                cert.serial_number = item.get("serialNumber")
                cert.dn = item.get("dn")
                cert.cert_type = item.get("type")
                cert.signature_algorithm = item.get("signatureAlgorithm")
                cert.key_size = item.get("keySize")
                cert.self_signed = bool(item.get("selfSigned"))
                cert.extended_validation = bool(item.get("extendedValidation"))

                cert.valid_from_date = _parse_dt(item.get("validFromDate"))
                cert.valid_to_date = _parse_dt(item.get("validToDate"))
                cert.created_date = _parse_dt(item.get("createdDate"))
                cert.update_date = _parse_dt(item.get("updateDate"))

                cert.issuer_category = item.get("issuerCategory")
                cert.instance_count = item.get("instanceCount")
                cert.asset_count = item.get("assetCount")

                cert.sources_json = json.dumps(item.get("sources")) if item.get("sources") is not None else None
                cert.subject_json = json.dumps(item.get("subject")) if item.get("subject") is not None else None
                cert.issuer_json = json.dumps(item.get("issuer")) if item.get("issuer") is not None else None

                cert.page_range = page_range  # required extra field
                if cert.mapped_to_inventory is None:
                    cert.mapped_to_inventory = False

                db.session.add(cert)

                # Assets (one cert -> many assets)
                assets = item.get("assets") or []
                for a in assets:
                    asset_id = a.get("id")
                    if asset_id is None:
                        continue

                    # uniqueness enforced per (certificate_id, asset_id)
                    existing = (
                        Asset.query.filter_by(certificate_id=cert.id, asset_id=asset_id).first()
                    )
                    if existing is None:
                        existing = Asset(certificate_id=cert.id, asset_id=asset_id)

                    existing.uuid = a.get("uuid")
                    existing.name = a.get("name")
                    existing.netbios_name = a.get("netbiosName")
                    existing.operating_system = a.get("operatingSystem")
                    existing.primary_ip = a.get("primaryIp")

                    existing.host_instances_json = json.dumps(a.get("hostInstances")) if a.get("hostInstances") is not None else None
                    existing.asset_interfaces_json = json.dumps(a.get("assetInterfaces")) if a.get("assetInterfaces") is not None else None

                    db.session.add(existing)

                inserted_this_page += 1

            # CRITICAL: commit BEFORE next call
            db.session.commit()

            total_inserted += inserted_this_page
            page_number += 1

        except Exception as e:
            log.error_message = str(e)
            db.session.commit()
            break

    return {"total_inserted": total_inserted, "last_page_number": page_number}
