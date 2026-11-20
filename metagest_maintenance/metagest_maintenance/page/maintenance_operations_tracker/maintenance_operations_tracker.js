frappe.pages["maintenance-operations-tracker"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Maintenance Operations Tracker"),
        single_column: true
    });
    const root = $('<div class="mot-root"></div>').appendTo(page.body);
    const style = `
      .mot-root {padding: 16px 0; font-size: 13px;}
      .mot-kpis {display:grid; grid-template-columns:repeat(6,minmax(110px,1fr)); gap:10px; margin-bottom:16px}
      .mot-kpi {border:1px solid var(--border-color); border-radius:9px; padding:13px; background:var(--card-bg)}
      .mot-kpi small {display:block; color:var(--text-muted); margin-bottom:4px}
      .mot-kpi strong {font-size:25px}
      .mot-row {border:1px solid var(--border-color); border-radius:9px; background:var(--card-bg); padding:13px; margin-bottom:9px}
      .mot-head {display:flex; justify-content:space-between; gap:15px; align-items:start; margin-bottom:9px}
      .mot-title {font-weight:600; font-size:14px;}
      .mot-sub {font-size:11px; color:var(--text-muted); margin-top:4px}
      .mot-grid {display:grid; grid-template-columns:repeat(6,minmax(60px,1fr)); gap:5px}
      .mot-stage {min-width:0}
      .mot-stage span {display:block; height:12px; border-radius:3px; background:var(--control-bg)}
      .mot-stage small {display:block; margin-bottom:5px; font-size:10px; color:var(--text-muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
      .mot-stage .done {background:#269d6b} .mot-stage .active {background:#e6a23c}
      .mot-stage .waiting {background:#d5d9dd} .mot-stage .na {background:repeating-linear-gradient(45deg,#eee,#eee 4px,#fff 4px,#fff 8px)}
      .mot-warning {color:#ae7512} .mot-late {color:#c0392b} .mot-ok {color:#258c5e}
      @media(max-width:900px){.mot-kpis{grid-template-columns:repeat(3,minmax(100px,1fr))}}
      @media(max-width:550px){.mot-kpis{grid-template-columns:repeat(2,minmax(100px,1fr))}.mot-stage small{font-size:8px}}
    `;
    $('<style></style>').text(style).appendTo(root);
    const filters = $('<div class="row" style="margin-bottom:12px"></div>').appendTo(root);
    const body = $('<div class="mot-body"></div>').appendTo(root);

    const company = page.add_field({fieldtype:"Link", fieldname:"company", label:__("Empresa"), options:"Company", change: refresh});
    const location = page.add_field({fieldtype:"Link", fieldname:"location", label:__("Localização"), options:"Location", change: refresh});
    const status = page.add_field({fieldtype:"Select", fieldname:"status", label:__("Estado"), options:"\nDraft\nApproved\nIn Progress\nCompleted\nClosed\nCancelled", change: refresh});
    const search = $('<input type="search" class="form-control" placeholder="Pesquisar ordem ou activo" style="max-width:320px;margin:8px 0">').appendTo(filters);
    const searchButton = $('<button class="btn btn-default" style="margin:8px">Pesquisar</button>').appendTo(filters);
    searchButton.on('click', refresh);
    search.on('keydown', e => {if (e.key === 'Enter') refresh();});
    page.set_primary_action(__("Actualizar"), refresh, "refresh");

    function esc(value) {return frappe.utils.escape_html(String(value == null ? "" : value));}
    function refresh() {
        body.html('<p class="text-muted">A carregar ordens de trabalho...</p>');
        frappe.call({
            method: "metagest_maintenance.maintenance_operations_tracker.get_tracker",
            args: {company:company.get_value(), location:location.get_value(), status:status.get_value(), search:search.val()},
            callback(r) {render(r.message || {kpis:{}, rows:[]});},
            error() {body.html('<p class="text-danger">Não foi possível carregar o tracker.</p>');}
        });
    }
    function render(result) {
        const metrics = [
            ["Ordens abertas", "open"], ["Em execução", "in_progress"],
            ["Em risco", "at_risk"], ["Em atraso", "overdue"],
            ["Concluídas", "completed"], ["Fechadas", "closed"]
        ];
        const kpis = '<div class="mot-kpis">' + metrics.map(([title,key]) =>
            `<div class="mot-kpi"><small>${esc(title)}</small><strong>${Number(result.kpis[key]||0)}</strong></div>`
        ).join('') + '</div>';
        const rows = (result.rows || []).map(wo => {
            const stages = wo.stages.map(s => `<div class="mot-stage"><small title="${esc(s.label)}">${esc(s.label)}</small><span class="${esc(s.state)}"></span></div>`).join('');
            const warnings = wo.blockers.map(x => esc(x)).join(' · ');
            const stateCls = wo.overdue ? 'mot-late' : (wo.blockers.length ? 'mot-warning' : 'mot-ok');
            return `<div class="mot-row">
                <div class="mot-head"><div>
                  <a class="mot-title" href="/app/maintenance-work-order/${encodeURIComponent(wo.name)}">${esc(wo.name)}</a>
                  <div class="mot-sub">${esc(wo.asset_name)} · ${esc(wo.location || 'Sem localização')} · ${esc(wo.maintenance_type || '')}</div>
                  <div class="mot-sub">${esc(wo.description || '')}</div>
                </div><div style="text-align:right;min-width:145px">
                  <strong>${esc(wo.status)}</strong>
                  <div class="mot-sub">${esc(wo.date_planned || 'Sem data prevista')}</div>
                  <div class="mot-sub ${stateCls}">${warnings || 'Sem bloqueios identificados'}</div>
                </div></div>
                <div class="mot-grid">${stages}</div>
              </div>`;
        }).join('');
        body.html(kpis + (result.limited ? '<p class="text-muted">A apresentar até 200 ordens recentes; aplicar filtros para restringir a vista.</p>' : '') +
            (rows || '<div class="text-muted" style="padding:20px">Sem ordens para os filtros seleccionados.</div>'));
    }
    refresh();
};
