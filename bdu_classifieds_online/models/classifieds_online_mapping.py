# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ClassifiedsOnlineMapping(models.Model):
    _name          = 'classifieds.online.mapping'
    _description   = 'Mapping of print titles to website domain code'

    title          = fields.Many2one('sale.advertising.issue', 'Title')
    domain         = fields.Char(string='Domain code')
    remark         = fields.Char(string='Remark')