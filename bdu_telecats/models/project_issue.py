# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ProjectIssue(models.Model):
    _inherit = "project.issue"

    ext_ref = fields.Char(string='External reference')
    