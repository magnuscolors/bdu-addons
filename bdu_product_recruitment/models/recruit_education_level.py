    # -*- coding: utf-8 -*-

from odoo import api, fields, models


class RecruitEducationLevel(models.Model):
    _name = 'recruit.education.level'
    
    name     = fields.Char('Opleidingsniveau')

