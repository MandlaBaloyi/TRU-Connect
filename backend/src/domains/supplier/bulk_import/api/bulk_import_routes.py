"""
Bulk Import routes. URL prefix /api/v1/supplier-discovery/imports --
same namespace-independence reasoning as products_routes.py/
inventory_routes.py's own docstrings.

Upload is multipart/form-data, not JSON -- a spreadsheet file (field
name "spreadsheet") plus an optional images ZIP (field name "zip"),
matching how a real file upload actually arrives over HTTP.
"""
from __future__ import annotations

from flask import Blueprint, request

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import error_response, success_response
from src.domains.security.rate_limit.limiter import limiter
from src.domains.supplier.bulk_import.config import is_bulk_import_enabled
from src.domains.supplier.bulk_import.rate_limit import policies as rate_limit_policies
from src.domains.supplier.bulk_import.services import abuse_tracking, import_service
from src.domains.supplier.bulk_import.services.errors import ImportUploadValidationError
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import SupplierProfileRepository

bulk_import_bp = Blueprint("bulk_import", __name__)


def _supplier_profile_id():
    from flask_jwt_extended import get_jwt_identity
    from src.core.exceptions import NotFoundError

    user_id = get_jwt_identity()
    profile = SupplierProfileRepository.get_by_supplier_id(user_id)
    if not profile:
        raise NotFoundError("Supplier profile not found.", code="SUPPLIER_PROFILE_NOT_FOUND")
    return profile.id


def _job_to_dto(job) -> dict:
    return {
        "id": str(job.id),
        "status": job.status.value,
        "source_filename": job.source_filename,
        "has_images_zip": job.has_images_zip,
        "total_rows": job.total_rows,
        "valid_rows": job.valid_rows,
        "error_rows": job.error_rows,
        "created_rows": job.created_rows,
        "images_total": job.images_total,
        "images_matched": job.images_matched,
        "failure_reason": job.failure_reason,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


@bulk_import_bp.route("/api/v1/supplier-discovery/imports", methods=["POST"])
@fully_authenticated
@role_required("supplier")
@limiter.limit(rate_limit_policies.BULK_IMPORT_SUBMIT, key_func=rate_limit_policies.supplier_key_func)
def submit_import():
    # The real "worse scenario" safety valve -- see config.py's own
    # docstring. Checked before anything else in this function, so a
    # platform-wide emergency disable never even reads the uploaded
    # file, let alone processes it.
    if not is_bulk_import_enabled():
        return error_response(
            message="Bulk import is temporarily unavailable. Please try again later.", status_code=503
        )

    supplier_profile_id = _supplier_profile_id()

    # Checked before any file is even read -- see abuse_tracking.py's
    # own docstring. Locks the FEATURE, not the account: everything
    # else in the app stays fully usable.
    if abuse_tracking.is_locked_out(supplier_profile_id):
        return error_response(
            message="Bulk import is temporarily locked for this account due to repeated suspicious files. "
            "Please try again later, or add products individually in the meantime.",
            status_code=403,
        )

    spreadsheet_file = request.files.get("spreadsheet")
    if spreadsheet_file is None or not spreadsheet_file.filename:
        return error_response(
            message="Validation failed", errors=["A spreadsheet file is required."], status_code=422
        )

    zip_file = request.files.get("zip")
    zip_filename = zip_file.filename if zip_file and zip_file.filename else None
    zip_bytes = zip_file.read() if zip_file and zip_file.filename else None

    try:
        job = import_service.submit_import(
            supplier_profile_id=supplier_profile_id,
            spreadsheet_filename=spreadsheet_file.filename,
            spreadsheet_bytes=spreadsheet_file.read(),
            zip_filename=zip_filename,
            zip_bytes=zip_bytes,
        )
    except ImportUploadValidationError as exc:
        return error_response(message=exc.message, errors=exc.errors, status_code=422)

    return success_response(data=_job_to_dto(job), status_code=202)


@bulk_import_bp.route("/api/v1/supplier-discovery/imports", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def list_imports():
    jobs = import_service.list_import_jobs(_supplier_profile_id())
    return success_response(data={"results": [_job_to_dto(j) for j in jobs]})


@bulk_import_bp.route("/api/v1/supplier-discovery/imports/<job_id>", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_import(job_id: str):
    job = import_service.get_import_job(job_id, _supplier_profile_id())
    return success_response(data=_job_to_dto(job))


@bulk_import_bp.route("/api/v1/supplier-discovery/imports/<job_id>/errors", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_import_errors(job_id: str):
    errors = import_service.get_import_errors(job_id, _supplier_profile_id())
    return success_response(
        data={"results": [{"row_number": e.row_number, "field": e.field, "message": e.message} for e in errors]}
    )
