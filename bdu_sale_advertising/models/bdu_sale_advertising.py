# -*- coding: utf-8 -*-
from datetime import date, timedelta
import logging
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

    # automated call expects domain selections in arguments in form of  (<arguments>,invoice_date, invoice_type, ou)
    #example ([('payment_method_id.name','=','Ideal')], "nearest_tuesday", 'ad', 'LNM')    
    def invoice_filtered_order(self, domain, invoice_date, invoice_type, ou):
        #sanity check
        if not type(domain) == list :
            _logger.error("Provided domain is not of type list. Program aborted.")
            return False
        if not invoice_type in ('ad', 'sub', 'general') :
            _logger.error("Allowed invoice types are: ad, sub and general")
            return False
        ou_objects = self.env['operating.unit'].search([('code','=',ou)])
        if len(ou_objects) != 1 :
            _logger.error("Operating unit ID not found. Check for correct code under settings/operating unit.")
            return False

        #init and date parsing
        helper=self.env['argument.helper']
        for num, filter in enumerate(domain) :
            lst         = list(filter)
            if len(lst)>2: #if not a RPN operator
                lst[2]      = helper.date_parse(lst[2])
                filter      = tuple(lst)
                domain[num] = filter
        invoice_date = helper.date_parse(invoice_date)

        #domain additions
        domain.append(('state','in',('sale','done')))
        if invoice_type=='ad' :
            domain.append(('advertising','=',True))
        elif invoice_type=='sub' :
            domain.append(('subscription','=',True))
        else :
            domain.append(('advertising','=',False))
            domain.append(('subscription','=',False))

        #invoicing per order
        selection = self.search(domain)
        if len(selection)==0:
            _logger.info("No order in selection.")
            return False
        his_obj = self.env['ad.order.line.make.invoice']
        for order in selection :
            orderlines = self.env['sale.order.line'].search([('order_id','=', order.id)])
            ctx = self._context.copy()
            ctx['active_ids']   = orderlines.ids
            ctx['invoice_date'] = invoice_date
            ctx['posting_date'] = date.today().strftime('%Y-%m-%d')
            ctx['chunk_size']   = 100
            ctx['job_queue']    = True
            ctx['execution_datetime'] = fields.Datetime.now()
            ctx['job_queue_description'] = 'Automated invoice for order '+order.name
            result = his_obj.with_context(ctx).make_invoices_from_lines()
        return True






class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_team_id = fields.Many2one(
        related='order_id.team_id',
        relation='crm.team',
        string='Salesteam',
        store=True
    )
    
    # automated call expects domain selections in arguments in form of  (<arguments>,invoice_date, invoice_type, ou)
    #example ([('advertising','=',True),('state','=','sale'),('adv_issue.name', '=','ESO 2019-01-30')], 'nearest_tuesday', 'ad', 'LNM')        
    def invoice_filtered_orderlines(self, domain, invoice_date, invoice_type, ou):
        #sanity check
        if not type(domain) == list :
            _logger.error("Provided domain is not of type list. Program aborted.")
            return False
        if not invoice_type in ('ad', 'sub', 'general') :
            _logger.error("Allowed invoice types are: ad, sub and general")
            return False
        ou_objects = self.env['operating.unit'].search([('code','=',ou)])
        if len(ou_objects) != 1 :
            _logger.error("Operating unit ID not found. Check for correct code under settings/operating unit.")
            return False

        #init, parse dates
        ou_id = ou_objects[0].id
        helper=self.env['argument.helper']
        for num, filter in enumerate(domain) :
            lst         = list(filter)
            if len(lst)>2: #if not a RPN operator
                lst[2]      = helper.date_parse(lst[2])
                filter      = tuple(lst)
                domain[num] = filter
        invoice_date = helper.date_parse(invoice_date)
        domain.append(('state','in',('sale','done')))

        #invoice
        if invoice_type=='ad' :
            domain.append(('advertising','=',True))
        elif invoice_type=='sub' :
            domain.append(('subscription','=',True))
        else :
            domain.append(('advertising','=',False))
            domain.append(('subscription','=',False))

        orderlines = self.search(domain).ids
        if len(orderlines)==0:
            _logger.info("No orderlines in selection.")
            return False
        his_obj    = self.env['ad.order.line.make.invoice']
        ctx = self._context.copy()
        ctx['active_ids']   = orderlines
        ctx['invoice_date'] = invoice_date
        ctx['posting_date'] = date.today().strftime('%Y-%m-%d')
        ctx['chunk_size']   = 100
        ctx['job_queue']    = True
        ctx['execution_datetime'] = fields.Datetime.now()
        ctx['job_queue_description'] = 'Automated invoice for orderlines'
        result = his_obj.with_context(ctx).make_invoices_from_lines()
        return result








class ArgumentHelper(models.Model):
    _name = 'argument.helper'

    def date_parse(self, value) :
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
                days= +1 -weekday +7  #saturday or sunday
            nt = now + timedelta(days=days)
            return nt.strftime('%Y-%m-%d')

        else :
            return value


