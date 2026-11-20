import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    # Default meter configuration by Asset Category
    create_custom_fields({
        "Asset Category": [
            {
                "fieldname": "custom_meter_type",
                "label": "Meter Type",
                "fieldtype": "Select",
                "options": "\nOperating Hours\nKilometres",
                "insert_after": "asset_category_name",
            },
            {
                "fieldname": "custom_meter_reading_frequency",
                "label": "Meter Reading Frequency",
                "fieldtype": "Select",
                "options": "\nDaily\nWeekly\nMonthly",
                "insert_after": "custom_meter_type",
            },
        ]
    }, update=True)

    # Create the meter-reading document
    if not frappe.db.exists("DocType", "Asset Meter Reading"):
        frappe.get_doc({
            "doctype": "DocType",
            "name": "Asset Meter Reading",
            "module": "Metagest Maintenance",
            "custom": 1,
            "is_submittable": 1,
            "track_changes": 1,
            "autoname": "AMR-.YYYY.-.#####",
            "fields": [
                {
                    "fieldname": "asset",
                    "label": "Asset",
                    "fieldtype": "Link",
                    "options": "Asset",
                    "reqd": 1,
                    "in_list_view": 1,
                },
                {
                    "fieldname": "reading_date",
                    "label": "Reading Date",
                    "fieldtype": "Date",
                    "reqd": 1,
                    "in_list_view": 1,
                },
                {
                    "fieldname": "meter_type",
                    "label": "Meter Type",
                    "fieldtype": "Select",
                    "options": "Operating Hours\nKilometres",
                    "reqd": 1,
                },
                {
                    "fieldname": "meter_reading",
                    "label": "Meter Reading",
                    "fieldtype": "Float",
                    "reqd": 1,
                    "in_list_view": 1,
                },
                {
                    "fieldname": "recorded_by",
                    "label": "Recorded By",
                    "fieldtype": "Link",
                    "options": "User",
                    "default": "__user",
                    "reqd": 1,
                },
                {
                    "fieldname": "notes",
                    "label": "Notes",
                    "fieldtype": "Small Text",
                },
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "submit": 1,
                    "cancel": 0,
                    "delete": 0,
                    "report": 1,
                    "export": 1,
                }
            ],
        }).insert(ignore_permissions=True)

    frappe.clear_cache(doctype="Asset Category")
    frappe.clear_cache(doctype="Asset Meter Reading")
