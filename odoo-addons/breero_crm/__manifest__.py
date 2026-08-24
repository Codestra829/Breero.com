{
    "name": "BREERO CRM Integration",
    "version": "19.0.1.0.0",
    "summary": "Idempotent CRM intake for BREERO",
    "author": "Codestra LLC DBA Breero.com",
    "website": "https://breero.com",
    "license": "LGPL-3",
    "depends": ["crm", "utm", "mail"],
    "data": [
        "data/crm_teams.xml", "data/crm_stages.xml",
        "security/security.xml", "security/ir.model.access.csv", "data/activity_types.xml",
        "views/crm_lead_views.xml", "views/res_partner_views.xml",
        "views/breero_sync_event_views.xml", "views/breero_crm_case_views.xml", "views/menus.xml",
    ],
    "installable": True,
    "application": False,
}
