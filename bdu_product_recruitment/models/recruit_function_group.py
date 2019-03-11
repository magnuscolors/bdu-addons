    # -*- coding: utf-8 -*-

from odoo import api, fields, models


class RecruitFunctionGroup(models.Model):
    _name = 'recruit.function.group'
    
    name     = fields.Char('Functiegroep')

