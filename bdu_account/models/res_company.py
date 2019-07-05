# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = 'res.company'

    credit_control_logo = fields.Binary('Credit control logo',
            help='Use logo (not background image), for first page, supporting all operating units of the company')
    credit_control_footer    = fields.Char('Credit control footer',
    		help='Footer, supporting all operating units of the company')

    default_credit_control_policy = fields.Many2one('credit.control.policy', string='Default credit control policy for new customers')
