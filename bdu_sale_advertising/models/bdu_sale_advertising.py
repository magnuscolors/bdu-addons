# -*- coding: utf-8 -*-
from datetime import date, timedelta
import logging, pdb
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class SaleAdvertisingIssue(models.Model):
    _inherit = "sale.advertising.issue"

    crm_team_id = fields.Many2one('crm.team', 'Primary salesteam')

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def update_acc_mgr_sp(self):
        if not self.advertising:
            self.user_id = self.partner_id.user_id.id \
                if self.partner_id.user_id else False
            self.partner_acc_mgr = False
            if self.partner_id:
                if self.company_id and self.company_id.name == 'BDUmedia BV':
                    self.user_id = self._uid
                    self.partner_acc_mgr = self.partner_id.user_id.id \
                        if self.partner_id.user_id else False

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.update_acc_mgr_sp()

    @api.multi
    @api.onchange('partner_id', 'published_customer', 'advertising_agency',
                  'agency_is_publish')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        result = super(SaleOrder, self).onchange_partner_id()
        if not self.advertising:
            self.update_acc_mgr_sp()
        return result

    @api.model
    def create(self, vals):
        result = super(SaleOrder, self).create(vals)
        if not vals.get('advertising', False):
            if vals.get('partner_id', False) and vals.get('company_id', False):
                company = self.env['res.company'].browse(vals.get('company_id'))
                if company.name == 'BDUmedia BV':
                    partner = self.env['res.partner'].browse(
                        vals.get('partner_id'))
                    result['partner_acc_mgr'] = partner.user_id.id \
                        if partner.user_id else False
                else:
                    result['partner_acc_mgr'] = False
        return result

    @api.multi
    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        for order in self.filtered(lambda s: s.state in [
            'sale'] and not s.advertising):
            if 'partner_id' in vals or 'company_id' in vals:
                company = self.env['res.company'].browse(vals.get(
                    'company_id')) if 'company_id' in vals else self.company_id
                if company.name == 'BDUmedia BV':
                    partner = self.env['res.partner'].browse(vals.get(
                        'partner_id')) \
                        if 'partner_id' in vals else self.partner_id
                    self.partner_acc_mgr = partner.user_id.id \
                        if partner.user_id else False
                else:
                    self.partner_acc_mgr = False
        return result
        
    def invoice_filtered_order(self, domain, invoice_date):
        # automated call expects domain selections in arguments in form of  (<arguments>,invoice_date)
        #example ([('state','=','sale'),('advertising','=',True)], "nearest_tuesday")
        if not type(domain) == list :
            _logger.error("Provided domain is not of type list. Program aborted.")
            return
        helper=self.env['argument.helper']
        for num, filter in enumerate(domain) :
            lst         = list(filter)
            lst[2]      = helper.date_parse(lst[2])
            filter      = tuple(lst)
            domain[num] = filter
        invoice_date = helper.date_parse(invoice_date)
        pdb.set_trace()
        selection = self.search(domain).ids
        self = self.with_context(active_ids=selection,chunk_size=100, invoice_date=invoice_date)
        result = self.env['ad.order.make.invoice'].make_invoices_from_ad_orders()
        return


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_team_id = fields.Many2one(
        related='order_id.team_id',
        relation='crm.team',
        string='Salesteam',
        store=True
    )
        
    def invoice_filtered_orderlines(self, domain, invoice_date):
        # automated call expects domain selections in arguments in form of  (<arguments>,invoice_date)
        #example ([('advertising','=',True),('state','=','sale'),('adv_issue.name', '=','ESO 2019-01-30')],)
        if not type(domain) == list :
            _logger.error("Provided domain is not of type list. Program aborted.")
            return
        helper=self.env['argument.helper']
        for num, filter in enumerate(domain) :
            lst         = list(filter)
            lst[2]      = helper.date_parse(lst[2])
            filter      = tuple(lst)
            domain[num] = filter
        invoice_date = helper.date_parse(invoice_date)
        selection = self.search(domain).ids
        self = self.with_context(active_ids=selection, chunk_size=100, invoice_date=invoice_date)
        result = self.env['ad.order.line.make.invoice'].make_invoices_from_lines()
        return

class ArgumentHelper(models.Model):
    _name = 'argument.helper'

    def date_parse(self, value) :
        pdb.set_trace()
        if value == 'first_this_month' :
            now = date.today()
            ftm = date(now.year, now.month, 1)
            #move to monday if first day this month is a sunday
            if ftm.weekday() == 6 :
                ftm = date.date(now.year, now.month, 2)
            return ftm.strftime('%Y-%m-%d')

        elif value == 'last_day_previous_month' :
            now  = date.today()
            ldpm = date(now.year, now.month, 1)-timedelta(days=1)
            #move to saturday is last day prev month is a sunday
            if ldpm.weekday() == 5 :
                ldpm = ldpm - timedelta(days=1)
            return ldpm.strftime('%Y-%m-%d')

        elif value == 'today' :
            now = date.today()
            return now.strftime('%Y-%m-%d')

        elif value == 'yesterday' :
            yesterday = date.today() - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d')

        elif value == 'day_before_yesterday' :
            dby = date.today() - timedelta(days=2)
            return dby.strftime('%Y-%m-%d')

        elif value == 'last_sunday' :
            now     = date.today()
            weekday = now.weekday()
            days    = -1 - weekday
            ls      = now + timedelta(days=days)
            return ls.strftime('%Y-%m-%d')

        elif value == 'nearest_tuesday' :
            now     = date.today()
            weekday = now.weekday()
            if weekday in [0,1,2,3,4] :
                days = +1 -weekday
            else :
                days= +1 -weekdays +7  #saturday or sunday
            nt = now + timedelta(days=days)
            return nt.strftime('%Y-%m-%d')

        else :
            return value


