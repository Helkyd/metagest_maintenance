import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Asset Maintenance Task": [
            {
                "fieldname": "custom_planning_basis",
                "label": "Planning Basis",
                "fieldtype": "Select",
                "options": "Calendar\nOperating Hours\nKilometres",
                "default": "Calendar",
                "insert_after": "periodicity",
                "in_list_view": 1,
            },
            {
                "fieldname": "custom_usage_interval",
                "label": "Maintenance Interval",
                "fieldtype": "Float",
                "insert_after": "custom_planning_basis",
                "depends_on": "eval:doc.custom_planning_basis!='Calendar'",
            },
            {
                "fieldname": "custom_last_service_reading",
                "label": "Last Service Reading",
                "fieldtype": "Float",
                "insert_after": "custom_usage_interval",
                "depends_on": "eval:doc.custom_planning_basis!='Calendar'",
            },
            {
                "fieldname": "custom_next_service_reading",
                "label": "Next Service Reading",
                "fieldtype": "Float",
                "insert_after": "custom_last_service_reading",
                "read_only": 1,
                "depends_on": "eval:doc.custom_planning_basis!='Calendar'",
            },
        ]
    }, update=True)

    frappe.clear_cache(doctype="Asset Maintenance Task")
