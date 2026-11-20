import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    if not frappe.db.exists("DocType", "Maintenance Usage Task"):
        frappe.get_doc({
            "doctype": "DocType",
            "name": "Maintenance Usage Task",
            "module": "Metagest Maintenance",
            "custom": 1,
            "istable": 1,
            "fields": [
                {
                    "fieldname": "maintenance_task",
                    "label": "Maintenance Task",
                    "fieldtype": "Data",
                    "reqd": 1
                },
                {
                    "fieldname": "meter_type",
                    "label": "Meter Type",
                    "fieldtype": "Select",
                    "options": "Operating Hours\nKilometres",
                    "reqd": 1
                },
                {
                    "fieldname": "usage_interval",
                    "label": "Maintenance Interval",
                    "fieldtype": "Float",
                    "reqd": 1
                },
                {
                    "fieldname": "last_service_reading",
                    "label": "Last Service Reading",
                    "fieldtype": "Float"
                },
                {
                    "fieldname": "next_service_reading",
                    "label": "Next Service Reading",
                    "fieldtype": "Float",
                    "read_only": 1
                },
                {
                    "fieldname": "assign_to",
                    "label": "Assigned Technician",
                    "fieldtype": "Link",
                    "options": "User"
                },
                {
                    "fieldname": "description",
                    "label": "Description",
                    "fieldtype": "Small Text"
                }
            ]
        }).insert(ignore_permissions=True)

    create_custom_fields({
        "Asset Maintenance": [
            {
                "fieldname": "custom_usage_maintenance_tasks",
                "label": "Usage-Based Maintenance",
                "fieldtype": "Table",
                "options": "Maintenance Usage Task",
                "insert_after": "asset_maintenance_tasks"
            }
        ]
    }, update=True)

    frappe.clear_cache(doctype="Asset Maintenance")
