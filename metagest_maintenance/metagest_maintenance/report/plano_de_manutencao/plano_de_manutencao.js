frappe.query_reports["Plano de Manutencao"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Empresa"),
            fieldtype: "Link",
            options: "Company"
        },
        {
            fieldname: "location",
            label: __("Localização"),
            fieldtype: "Link",
            options: "Location"
        },
        {
            fieldname: "asset",
            label: __("Activo"),
            fieldtype: "Link",
            options: "Asset"
        },
        {
            fieldname: "basis",
            label: __("Base"),
            fieldtype: "Select",
            options: "\nCalendar\nUsage"
        },
        {
            fieldname: "from_date",
            label: __("De"),
            fieldtype: "Date",
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: __("Até"),
            fieldtype: "Date",
            default: frappe.datetime.month_end()
        }
    ]
};
