import frappe
from frappe.utils import flt, getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = [
        {"label": "Activo", "fieldname": "asset", "fieldtype": "Link", "options": "Asset", "width": 170},
        {"label": "Designação", "fieldname": "asset_name", "fieldtype": "Data", "width": 190},
        {"label": "Localização", "fieldname": "location", "fieldtype": "Link", "options": "Location", "width": 145},
        {"label": "Actividade", "fieldname": "activity", "fieldtype": "Data", "width": 260},
        {"label": "Base", "fieldname": "basis", "fieldtype": "Data", "width": 125},
        {"label": "Data Prevista", "fieldname": "due_date", "fieldtype": "Date", "width": 115},
        {"label": "Leitura Actual", "fieldname": "current_reading", "fieldtype": "Float", "width": 115},
        {"label": "Próxima Revisão", "fieldname": "threshold", "fieldtype": "Float", "width": 125},
        {"label": "Restante", "fieldname": "remaining", "fieldtype": "Float", "width": 110},
        {"label": "Estado", "fieldname": "status", "fieldtype": "Data", "width": 135},
        {"label": "Plano", "fieldname": "plan", "fieldtype": "Link", "options": "Asset Maintenance", "width": 170},
    ]

    data = []
    asset_cache = {}

    def get_asset(asset_id):
        if asset_id not in asset_cache:
            if not frappe.has_permission("Asset", "read", asset_id):
                return None
            asset_cache[asset_id] = frappe.db.get_value(
                "Asset", asset_id, ["asset_name", "location"], as_dict=True
            )
        return asset_cache[asset_id]

    plan_filters = {}
    if filters.get("company"):
        plan_filters["company"] = filters.company
    if filters.get("asset"):
        plan_filters["asset_name"] = filters.asset

    plans = frappe.get_list(
        "Asset Maintenance",
        filters=plan_filters,
        fields=["name", "asset_name", "company"],
        limit_page_length=0,
    )

    for plan in plans:
        asset = get_asset(plan.asset_name)
        if not asset:
            continue

        if filters.get("location") and asset.location != filters.location:
            continue

        common = {
            "asset": plan.asset_name,
            "asset_name": asset.asset_name,
            "location": asset.location,
            "plan": plan.name,
        }

        if filters.get("basis") in (None, "", "Calendar"):
            logs = frappe.get_list(
                "Asset Maintenance Log",
                filters={
                    "asset_maintenance": plan.name,
                    "maintenance_status": ["in", ["Planned", "Overdue"]],
                },
                fields=["name", "task_name", "due_date", "maintenance_status"],
                limit_page_length=0,
            )

            for log in logs:
                if not log.due_date:
                    continue
                if filters.get("from_date") and getdate(log.due_date) < getdate(filters.from_date):
                    continue
                if filters.get("to_date") and getdate(log.due_date) > getdate(filters.to_date):
                    continue

                data.append({
                    **common,
                    "activity": log.task_name,
                    "basis": "Calendar",
                    "due_date": log.due_date,
                    "status": log.maintenance_status,
                })

        if filters.get("basis") not in (None, "", "Usage"):
            continue

        plan_doc = frappe.get_doc("Asset Maintenance", plan.name)
        for task in plan_doc.get("custom_usage_maintenance_tasks") or []:
            readings = frappe.get_list(
                "Asset Meter Reading",
                filters={
                    "asset": plan.asset_name,
                    "meter_type": task.meter_type,
                    "docstatus": 1,
                },
                fields=["meter_reading"],
                order_by="reading_date desc, creation desc",
                limit_page_length=1,
            )

            current = flt(readings[0].meter_reading) if readings else None
            threshold = flt(task.next_service_reading)
            interval = flt(task.usage_interval)
            remaining = threshold - current if current is not None else None

            if current is None:
                status = "Sem leitura"
            elif threshold <= 0 or interval <= 0:
                status = "Não configurado"
            elif remaining <= 0:
                status = "Devido"
            elif remaining <= interval * 0.10:
                status = "Próximo do limite"
            else:
                status = "Planeado"

            data.append({
                **common,
                "activity": task.maintenance_task,
                "basis": task.meter_type,
                "current_reading": current,
                "threshold": threshold,
                "remaining": remaining,
                "status": status,
            })

    data.sort(key=lambda r: (
        r.get("due_date") is None,
        str(r.get("due_date") or ""),
        r.get("asset_name") or "",
    ))

    return columns, data
