    # -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ProductDistributionOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    #note, because re-use in form view of existing fields leaves one them empty we need product specific fields
    recruit_from_date       = fields.Date('Publiseer van')
    recruit_until_date      = fields.Date('Publiseer tot')
    recruit_adv_issue_ids   = fields.Many2many('sale.advertising.issue', string='Publiceren op')

    #job
    recruit_job_title       = fields.Char('Functienaam')
    recruit_job_description = fields.Char('Job description')
    recruit_employment      = fields.Many2one('recruit.employment.type', string='Dienstverband')
    recruit_function_group  = fields.Many2one('recruit.function.group',  string='Functiegroep')
    recruit_education_level = fields.Many2one('recruit.education.level', string='Opleidingsniveau')
    recruit_industry        = fields.Many2one('recruit.industry',        string='Sector')
    
    #not in partners
    recruit_company_name    = fields.Char('Bedrijf')
    recruit_company_email   = fields.Char('Email/contact')
    recruit_company_website = fields.Char('Website')
    recruit_company_logo    = fields.Binary('Bedrijfslogo')
    recruit_company_street  = fields.Char('Street + nr')
    recruit_company_zip     = fields.Char('Postcode')
    recruit_company_city    = fields.Char('Plaats')
    recruit_company_region  = fields.Char('Regio',                 size=50)
    recruit_company_province= fields.Many2one('res.country.state', string='Provincie')
    recruit_company_country = fields.Many2one('res.country',       string='Land')


    #data input help when accessed for first time
    @api.onchange('recruit_from_date') 
    def recruit_from_date_onchange(self) :
        if self.recruit_from_date and self.recruit_until_date :
            if self.recruit_from_date > self.recruit_until_date :
                self.recruit_until_date = self.recruit_from_date
            #from_date=datetime.datetime.strptime(self.recruit_from_date,DEFAULT_SERVER_DATE_FORMAT).date()
            #self.recruit_until_date = from_date+datetime.timedelta(days=6)
        self.set_standard_date_fields()
        return
    
    @api.onchange('recruit_until_date') 
    def recruit_until_date_onchange(self) :
        if self.recruit_from_date and self.recruit_until_date:
            if self.recruit_until_date < self.recruit_from_date :
                self.recruit_from_date = self.recruit_until_date
        self.set_standard_date_fields()
        return

    @api.model
    def set_standard_date_fields(self) :
        self.start_date = self.recruit_from_date
        self.end_date   = self.recruit_until_date
        return



