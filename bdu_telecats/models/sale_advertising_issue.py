# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleAdvertisingIssue(models.Model):
    _inherit = 'sale.advertising.issue'

    import_service_requests = fields.Boolean('Import service requests')
    import_service_requests_remark = fields.Char(string="Remark", help="Any note")

   