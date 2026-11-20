import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate


def validate_meter_reading(doc, method=None):
    """Validate equipment readings before saving or submitting."""

    if flt(doc.meter_reading) < 0:
        frappe.throw(_("Meter reading cannot be negative."))

    if getdate(doc.reading_date) > getdate(nowdate()):
        frappe.throw(_("Reading date cannot be in the future."))

    category = frappe.db.get_value(
        "Asset", doc.asset, "asset_category"
    )

    expected_type = frappe.db.get_value(
        "Asset Category", category, "custom_meter_type"
    ) if category else None

    if expected_type and doc.meter_type != expected_type:
        frappe.throw(
            _("Meter type must match the Asset Category: {0}")
            .format(expected_type)
        )

    previous = frappe.get_all(
        "Asset Meter Reading",
        filters={
            "asset": doc.asset,
            "meter_type": doc.meter_type,
            "docstatus": 1,
            "reading_date": ["<=", doc.reading_date],
            "name": ["!=", doc.name],
        },
        fields=["name", "reading_date", "meter_reading"],
        order_by="reading_date desc, creation desc",
        limit_page_length=1,
    )

    if previous and flt(doc.meter_reading) < flt(previous[0].meter_reading):
        frappe.throw(
            _("Reading cannot be lower than the previous submitted reading.")
        )

    following = frappe.get_all(
        "Asset Meter Reading",
        filters={
            "asset": doc.asset,
            "meter_type": doc.meter_type,
            "docstatus": 1,
            "reading_date": [">", doc.reading_date],
            "name": ["!=", doc.name],
        },
        fields=["meter_reading"],
        order_by="reading_date asc",
        limit_page_length=1,
    )

    if following and flt(doc.meter_reading) > flt(following[0].meter_reading):
        frappe.throw(
            _("Reading cannot exceed a later submitted reading.")
        )
