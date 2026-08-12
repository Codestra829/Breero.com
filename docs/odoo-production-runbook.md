# Odoo production runbook

Target module: `breero_crm` version `19.0.1.0.0`. Before installation, query the running Odoo version, database, company, installed CRM/Helpdesk/marketing modules, teams, stages, custom fields, and service-account groups. Do not install if the major version is not 19.

## 2026-08-12 environment verification

The reachable shared Codestra staging runtime reports Odoo `19.0-20260630`, database `odoo19_module_staging`, company `YourCompany`, CRM and mass mailing installed, Helpdesk absent, zero `x_breero_*` fields, and no BREERO service account. It contains unrelated business teams and is therefore **not approved as the BREERO target**. No changes were made to it. The module was instead installed and tested with the identical Odoo image against an isolated temporary database.

Before production, take and checksum a database backup, restore it into an isolated environment, export teams/stages/fields, record the exact Git SHA and module version, and upgrade staging with `--test-enable`. Verify the four synthetic canaries and outage/recovery test. Production delivery stays disabled until those results and release approval exist.

Rollback: disable `ODOO_ENABLED`, leave outbox rows durable, restore the tested backup if Odoo data/schema rollback is required, redeploy the previous exact module artifact, verify health, then re-enable delivery and drain the queue. Never downgrade against an untested database. Retention/deletion remains manual until legal policy is approved; financial/audit records are preserved.

Company: Codestra LLC DBA Breero.com, 20633 Longenbaugh Rd, Cypress, TX 77433, United States. Corporate site: https://codestra.co. Customer brand: BREERO, https://breero.com, support@breero.com.
