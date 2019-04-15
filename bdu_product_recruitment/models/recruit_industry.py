    # -*- coding: utf-8 -*-

from odoo import api, fields, models


class RecruitIndustry(models.Model):
    _name = 'recruit.industry'
    
    name     = fields.Char('Sector')

