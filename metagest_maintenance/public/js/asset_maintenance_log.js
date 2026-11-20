frappe.ui.form.on("Asset Maintenance Log", {
    refresh(frm) {
        if (frm.is_new()) return;

        frappe.db.get_list("Maintenance Work Order", {
            filters: {
                maintenance_log: frm.doc.name
            },
            fields: ["name"],
            limit: 1
        }).then(records => {
            if (records.length) {
                frm.add_custom_button(__("Open Work Order"), () => {
                    frappe.set_route(
                        "Form",
                        "Maintenance Work Order",
                        records[0].name
                    );
                }, __("Maintenance"));

                return;
            }

            if (
                !["Planned", "Overdue"].includes(frm.doc.maintenance_status)
                || !frm.doc.asset_maintenance
                || !frm.doc.task
            ) {
                return;
            }

            frm.add_custom_button(__("Create Work Order"), () => {
                frappe.confirm(
                    __("Create a preventive Maintenance Work Order for this scheduled activity?"),
                    () => {
                        frappe.call({
                            method: "metagest_maintenance.maintenance_planning.create_work_order_from_log",
                            args: {
                                maintenance_log: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __("Creating Maintenance Work Order..."),
                            callback(r) {
                                if (r.message) {
                                    frappe.set_route(
                                        "Form",
                                        "Maintenance Work Order",
                                        r.message
                                    );
                                }
                            }
                        });
                    }
                );
            }, __("Maintenance"));
        });
    }
});
