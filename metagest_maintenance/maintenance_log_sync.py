import frappe
from frappe import _


def sync_work_order_closure(doc, method=None):
    """Complete the ERPNext maintenance log when a preventive WO closes."""

    if doc.status != "Closed":
        return

    if doc.maintenance_type != "Preventive Maintenance":
        return

    if not doc.maintenance_log:
        return

    log = frappe.get_doc("Asset Maintenance Log", doc.maintenance_log)

    # Idempotency: an already submitted completion needs no further action.
    if log.docstatus == 1 and log.maintenance_status == "Completed":
        return

    if log.docstatus != 0:
        frappe.throw(_("Linked Maintenance Log is already submitted or cancelled."))

    if log.maintenance_status not in ("Planned", "Overdue"):
        frappe.throw(_("Linked Maintenance Log is not awaiting execution."))

    if not log.asset_maintenance or not log.task:
        frappe.throw(_("Linked Maintenance Log has no valid maintenance plan or task."))

    plan_asset = frappe.db.get_value(
        "Asset Maintenance", log.asset_maintenance, "asset_name"
    )

    if plan_asset != doc.asset:
        frappe.throw(_("Work Order asset does not match the maintenance plan."))

    if not doc.completion_date:
        frappe.throw(_("Completion date is required."))

    if not (doc.actions_performed or "").strip():
        frappe.throw(_("Actions performed are required."))

    log.maintenance_status = "Completed"
    log.completion_date = doc.completion_date
    log.actions_performed = doc.actions_performed

    # This is an automated lifecycle action initiated by WO closure.
    log.flags.ignore_permissions = True
    log.submit()
