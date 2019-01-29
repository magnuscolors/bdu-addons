# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Partner(models.Model):
    _inherit = 'res.partner'

    kosmetiek_nr = fields.Char('Kosmetiek nr')
