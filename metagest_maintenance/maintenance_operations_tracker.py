"""Read-only, permission-respecting operational maintenance tracker."""
import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate


@frappe.whitelist()
def get_tracker(company=None, location=None, status=None, search=None):
    if not frappe.has_permission("Maintenance Work Order", "read"):
        frappe.throw(_("Not permitted to view Maintenance Work Orders"), frappe.PermissionError)

    filters = {}
    if company:
        filters["company"] = company
    if location:
        filters["asset_location"] = location
    if status:
        filters["status"] = status

    # get_list enforces record-level permissions; intentionally cap a demo-sized board.
    references = frappe.get_list(
        "Maintenance Work Order",
        filters=filters,
        fields=["name"],
        order_by="modified desc",
        limit_page_length=200,
    )

    records = []
    query = (search or "").strip().casefold()
    for ref in references:
        wo = frappe.get_doc("Maintenance Work Order", ref.name)
        if not frappe.has_permission("Maintenance Work Order", "read", wo):
            continue

        asset_label = wo.get("asset_name") or wo.get("asset") or ""
        if query and query not in (" ".join([
            wo.name or "", str(asset_label), wo.get("description") or ""
        ])).casefold():
            continue

        parts = wo.get("parts_and_materials") or []
        services = wo.get("custom_external_services") or []
        checklist = wo.get("table_beic") or []
        effective_status = wo.get("status") or "Draft"
        terminal = effective_status in ("Closed", "Cancelled")
        overdue = bool(
            wo.get("date_planned") and getdate(wo.date_planned) < getdate(nowdate())
            and effective_status not in ("Completed", "Closed", "Cancelled")
        )

        # Stages represent known checkpoints, not a fabricated % of work completed.
        stages = [
            {"key": "planning", "label": "Planeamento", "state": "done" if effective_status not in ("Draft", "Cancelled") else "waiting"},
            {"key": "materials", "label": "Materiais", "state": "na" if not parts else (
                "done" if all(flt(p.get("issued_quantity")) + 0.0001 >= flt(p.get("required_quantity")) for p in parts)
                else "waiting")},
            {"key": "external", "label": "Serviços ext.", "state": "na" if not services else (
                "done" if all(s.get("acceptance_status") == "Accepted" for s in services)
                else "waiting")},
            {"key": "execution", "label": "Execução", "state": "done" if effective_status in ("Completed", "Closed") else (
                "active" if effective_status == "In Progress" else "waiting")},
            {"key": "verification", "label": "Verificação", "state": "na" if not checklist else (
                "done" if all((not c.get("mandatory")) or c.get("completed") for c in checklist)
                else "waiting")},
            {"key": "closure", "label": "Fecho", "state": "done" if effective_status == "Closed" else "waiting"},
        ]
        if effective_status == "Cancelled":
            stages = [{**stage, "state": "na"} for stage in stages]

        blockers = []
        if parts:
            deficit = sum(max(0, flt(p.get("required_quantity")) - flt(p.get("issued_quantity"))) for p in parts)
            if deficit > 0.0001:
                blockers.append("Materiais pendentes")
        if services and any(s.get("acceptance_status") != "Accepted" for s in services):
            blockers.append("Serviços externos pendentes")
        if checklist and any(c.get("mandatory") and not c.get("completed") for c in checklist):
            blockers.append("Checklist pendente")
        if overdue:
            blockers.append("Em atraso")

        records.append({
            "name": wo.name,
            "asset": wo.get("asset"),
            "asset_name": asset_label,
            "company": wo.get("company"),
            "location": wo.get("asset_location"),
            "maintenance_type": wo.get("maintenance_type"),
            "priority": wo.get("priority"),
            "status": effective_status,
            "date_planned": str(wo.get("date_planned") or ""),
            "assigned_to": wo.get("assigned_to"),
            "description": (wo.get("description") or "")[:180],
            "overdue": overdue,
            "blockers": blockers,
            "stages": stages,
            "total_cost": flt(wo.get("total_maintenance_cost")),
        })

    kpis = {
        "open": sum(1 for r in records if r["status"] not in ("Closed", "Cancelled")),
        "in_progress": sum(1 for r in records if r["status"] == "In Progress"),
        "at_risk": sum(1 for r in records if r["blockers"] and not r["overdue"] and r["status"] not in ("Closed", "Cancelled")),
        "overdue": sum(1 for r in records if r["overdue"]),
        "completed": sum(1 for r in records if r["status"] == "Completed"),
        "closed": sum(1 for r in records if r["status"] == "Closed"),
    }
    return {"kpis": kpis, "rows": records, "limited": len(references) == 200}
