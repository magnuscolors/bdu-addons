# -*- coding: utf-8 -*-

from odoo import api, fields, models
import re

class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    @api.onchange('title_id', 'zip') 
    def user_from_logistics_address(self):
        logistic_add = self.env['logistics.address.table']
        if self.title_id and self.zip:
            zip = re.sub("\D", "", self.zip)
            log_obj = logistic_add.search([('title_id','=',self.title_id.id),('zip','=',zip)], order="id desc", limit=1)
            if log_obj:
                user_obj = self.env['res.users'].search([('partner_id','=',log_obj.partner_id.id)])
                if partner_obj :
                    self.user_id = user_obj.id