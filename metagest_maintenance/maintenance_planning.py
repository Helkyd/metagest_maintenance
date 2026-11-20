import frappe
from frappe import _


@frappe.whitelist()
def create_work_order_from_log(maintenance_log):
    """
    Create a preventive Maintenance Work Order from
    an ERPNext Asset Maintenance Log.
    """

    log = frappe.get_doc("Asset Maintenance Log", maintenance_log)

    if log.maintenance_status not in ("Planned", "Overdue"):
        frappe.throw(
            _("Only Planned or Overdue maintenance logs can generate Work Orders.")
        )

    if not log.asset_maintenance:
        frappe.throw(_("Maintenance Log has no Asset Maintenance Plan."))

    if not log.task:
        frappe.throw(_("Maintenance Log has no scheduled maintenance task."))

    existing = frappe.db.exists(
        "Maintenance Work Order",
        {"maintenance_log": log.name}
    )

    if existing:
        frappe.throw(
            _("A Maintenance Work Order already exists: {0}").format(existing)
        )

    plan = frappe.get_doc("Asset Maintenance", log.asset_maintenance)
    task = frappe.get_doc("Asset Maintenance Task", log.task)

    if task.parent != plan.name:
        frappe.throw(_("Maintenance task does not belong to the selected plan."))

    if not plan.asset_name:
        frappe.throw(_("Maintenance Plan has no Asset."))

    asset = frappe.get_doc("Asset", plan.asset_name)

    work_order = frappe.get_doc({
        "doctype": "Maintenance Work Order",
        "asset": plan.asset_name,
        "company": plan.company,
        "maintenance_type": "Preventive Maintenance",
        "maintenance_log": log.name,
        "date_planned": log.due_date,
        "assigned_to": task.assign_to,
        "description": frappe.utils.strip_html(
            task.description or log.description or log.task_name or ""
        ),
        "status": "Draft"
    })

    if asset.location:
        work_order.asset_location = asset.location

    work_order.insert()

    return work_order.name
