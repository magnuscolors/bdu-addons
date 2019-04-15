    # -*- coding: utf-8 -*-

import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class ProductDistributionOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        for order in self :
            for orderline in order.order_line :
                if orderline.custom_orderline=="Recruitment":
                    if not orderline.recruit_job_description or len(orderline.recruit_job_description)==0 :
                        raise UserError(_("Order %s has orderline with empty job description and cannot be confirmed." % order.name))             

        result = super(ProductDistributionOrder, self).action_confirm()
        return result


class ProductDistributionOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    #note, because re-use in form view of existing fields leaves one them empty we need product specific fields
    recruit_from_date       = fields.Date('Publiceer van')
    recruit_until_date      = fields.Date('Publiceer tot')
    recruit_adv_issue_ids   = fields.Many2many('sale.advertising.issue', string='Publiceer op')

    #job
    recruit_job_title       = fields.Char('Functienaam')
    recruit_job_description = fields.Char('Functie beschrijving')
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
    #recruit_company_region  = fields.Char('Regio',                 size=50)   #obsolete
    recruit_company_province= fields.Many2one('res.country.state', string='Provincie')
    recruit_company_country = fields.Many2one('res.country',       string='Land')


    #data input help when accessed for first time
    @api.onchange('recruit_from_date') 
    def recruit_from_date_onchange(self) :
        if self.recruit_from_date and self.recruit_until_date :
            if self.recruit_from_date > self.recruit_until_date :
                self.recruit_until_date = self.recruit_from_date
        if self.recruit_from_date and not self.recruit_until_date :
            from_date=datetime.datetime.strptime(self.recruit_from_date,DEFAULT_SERVER_DATE_FORMAT).date()
            self.recruit_until_date = from_date+relativedelta(months=1)
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

    @api.multi
    @api.onchange('custom_orderline')
    def init_recruitment_orderline(self):
        for record in self :
            if not record.recruit_company_name and not record.recruit_company_email    and not record.recruit_company_website and \
               not record.recruit_company_logo and not record.recruit_company_street   and not record.recruit_company_zip     and \
               not record.recruit_company_city and not record.recruit_company_province and not record.recruit_company_country and \
               record.custom_orderline == 'Recruitment':
                record.recruit_company_name    = record.order_id.partner_shipping_id.name
                record.recruit_company_email   = record.order_id.partner_shipping_id.email
                record.recruit_company_website = record.order_id.partner_shipping_id.website
                record.recruit_company_logo    = record.order_id.partner_shipping_id.image
                record.recruit_company_street  = record.order_id.partner_shipping_id.street
                record.recruit_company_zip     = record.order_id.partner_shipping_id.zip
                record.recruit_company_city    = record.order_id.partner_shipping_id.city
                record.recruit_company_province= record.order_id.partner_shipping_id.state_id
                record.recruit_company_country = record.order_id.partner_shipping_id.country_id
        return 



