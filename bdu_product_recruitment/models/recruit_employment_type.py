    # -*- coding: utf-8 -*-

from odoo import api, fields, models


class RecruitEmploymentType(models.Model):
    _name = 'recruit.employment.type'
    
    name     = fields.Char('Dienstverband')

