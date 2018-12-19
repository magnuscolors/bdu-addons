# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models

class LogisticsAddressTable(models.Model):
    _name = 'logistics.address.table'
    _rec_name = 'country_id'

    country_id    = fields.Many2one('res.country', string='Country')
    region        = fields.Char(string='Region', size=50)
    province_id   = fields.Many2one('res.country.state', string='Province')
    municipality  = fields.Char(string='Municipality', size=50)
    city          = fields.Char(string='City')
    zip           = fields.Char(string='Zip')
    zip_2         = fields.Char(string='Zip AB')
    nr_from       = fields.Integer(string='From streetnr.')
    nr_until      = fields.Integer(string='Until streetnr.') #and including
    #when used as exceptions: use negative numbers for folder_addresses and total_addresses
    title_id      = fields.Many2one('sale.advertising.issue', string='Title')
    distribution_area = fields.Char(string='Distribution Area', size=50)
    total_addresses   = fields.Integer(string='Total Addresses')
    folder_addresses  = fields.Integer(string='Folder Addresses')
    number_no_no  = fields.Integer(string='Number No No')
    number_yes_no = fields.Integer(string='Number Yes No')
    user_id       = fields.Many2one('res.users', string='Logistics Service Provider')

    @api.onchange('country_id')
    def onchange_country_id(self):
        self.province_id = False #Empty province_id whenever country_id is altered.