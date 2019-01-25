# -*- coding: utf-8 -*-

import datetime, logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class Wave2AlternativeDate(models.Model):
    _name = 'wave2.alternative.date'

    title        = fields.Many2one('sale.advertising.issue', string='Title',  required=True, domain="[('parent_id','=',False)]")
    wave2_date   = fields.Date(string="Wave2 date", required=True)
    search_begin = fields.Date(string="Begin date for issue search", required=True)
    issue        = fields.Many2one('sale.advertising.issue', string='Issue',  required=True, domain="[('parent_id','!=',False)]")
    remark       = fields.Char(string="Remark", help="Any note reminding you of the reason")

    @api.onchange('wave2_date')
    @api.multi
    def _compute_issue_date(self):
        for rec in self:
            if rec.wave2_date:
                selected_date    = datetime.datetime.strptime(rec.wave2_date,DEFAULT_SERVER_DATE_FORMAT).date()
                rec.search_begin = selected_date-datetime.timedelta(days=7)