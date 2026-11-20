import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def get_usage_maintenance_status(asset):
    """Calculate usage-based maintenance status for an asset."""

    if not frappe.has_permission("Asset", "read", asset):
        frappe.throw(_("Not permitted to view this asset."), frappe.PermissionError)

    plans = frappe.get_all(
        "Asset Maintenance",
        filters={"asset_name": asset},
        pluck="name",
    )

    results = []

    for plan_name in plans:
        if not frappe.has_permission("Asset Maintenance", "read", plan_name):
            continue

        plan = frappe.get_doc("Asset Maintenance", plan_name)

        for task in plan.get("custom_usage_maintenance_tasks") or []:
            readings = frappe.get_all(
                "Asset Meter Reading",
                filters={
                    "asset": asset,
                    "meter_type": task.meter_type,
                    "docstatus": 1,
                },
                fields=["meter_reading", "reading_date"],
                order_by="reading_date desc, creation desc",
                limit_page_length=1,
            )

            if not readings:
                status = "No Reading"
                current = None
                remaining = None
            else:
                current = flt(readings[0].meter_reading)
                interval = flt(task.usage_interval)
                threshold = flt(task.next_service_reading)
                remaining = threshold - current

                if interval <= 0 or threshold <= 0:
                    status = "Not Configured"
                elif remaining <= 0:
                    status = "Due"
                elif remaining <= interval * 0.10:
                    status = "Approaching Due"
                else:
                    status = "Planned"

            results.append({
                "asset": asset,
                "maintenance_plan": plan.name,
                "task_id": task.name,
                "maintenance_task": task.maintenance_task,
                "meter_type": task.meter_type,
                "current_reading": current,
                "next_service_reading": task.next_service_reading,
                "remaining": remaining,
                "status": status,
            })

    return results
