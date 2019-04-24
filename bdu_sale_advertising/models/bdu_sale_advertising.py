# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
import logging
from odoo import api, fields, models, _
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.queue_job.exception import FailedJobError

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
    @job
    @api.multi
    def invoice_filtered_order(self, domain, invoice_date, invoice_type, ou):
        #sanity check
        if not type(domain) == list :
            return "Provided domain is not of type list. Program aborted.\n" + \
                   "Arguments should e.g. have following format :([('payment_method_id.name','=','Ideal'),'|',('team_id', '=' 'Alkmaar'),('team_id','=','Barneveld')], 'nearest_tuesday', 'ad', 'LNM')"
        if not invoice_type in ('ad', 'sub', 'general') :
            return "Allowed invoice types are: ad, sub and general. Provided invoice type : "+ invoice_type
        if not invoice_date in ('first_this_month', 
                                'last_day_previous_month', 
                                'today',
                                'yesterday',
                                'day_before_yesterday',
                                'last_sunday',
                                'nearest_tuesday') :
            return "Wrong invoice date.\n"+\
                   "Allowed invoice dates are: first_this_month, last_day_previous_month, today, yesterday, " + \
                   "day_before_yesterday, last_sunday', nearest_tuesday"
        ou_objects = self.env['operating.unit'].search([('code','=',ou)])
        if len(ou_objects) != 1 :
            return "Operating unit ID not found. Check for correct code under settings/operating unit."

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
        result  = "Parsed arguments are :\n"
        result += "- domain : %s \n" % domain
        result += "- invoice date : %s \n" % invoice_date
        result += "- operating unit : %s \n" % ou_objects[0].name
        selection = self.search(domain)
        
        if len(selection)==0:
            _logger.info("No order in selection.")
            result += "No order in selection."
            return result
        
        aolmi_obj   = self.env['ad.order.line.make.invoice']
        result     += "\nOrders selected for invoicing : %s\n" % len(selection)
        post_date   = date.today().strftime('%Y-%m-%d')

        for order in selection :
            orderlines = self.env['sale.order.line'].search([('order_id','=', order.id),('state','in',('sale','done'))])
            if not orderlines :
                result += "No orderlines for order %s. Order skipped." % order.name
                continue
            
            description = 'Invoice for order '+order.name
            aolmi_obj.with_delay(description=description).make_invoices_job_queue(invoice_date, post_date, orderlines)
            result += "Order "+order.name+" dispatched as seperate invoicing job.\n"

        result += "End of dispatching"
        return result






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
            return "Provided domain is not of type list. Program aborted.\n" + \
                   "Arguments should have e.g. following formati : ([('advertising','=',True),('state','=','sale'),('adv_issue.name', '=','ESO 2019-01-30')], 'nearest_tuesday', 'ad', 'LNM')"
        if not invoice_type in ('ad', 'sub', 'general') :
            return "Allowed invoice types are: ad, sub and general. Provided invoice type : "+ invoice_type
        if not invoice_date in ('first_this_month', 
                                'last_day_previous_month', 
                                'today',
                                'yesterday',
                                'day_before_yesterday',
                                'last_sunday',
                                'nearest_tuesday') :
            return "Wrong invoice date.\n"+\
                   "Allowed invoice dates are: first_this_month, last_day_previous_month, today, yesterday, " + \
                   "day_before_yesterday, last_sunday', nearest_tuesday"
        ou_objects = self.env['operating.unit'].search([('code','=',ou)])
        if len(ou_objects) != 1 :
            return "Operating unit ID not found. Check for correct code under settings/operating unit."

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

        #invoice
        domain.append(('state','in',('sale','done')))
        if invoice_type=='ad' :
            domain.append(('advertising','=',True))
        elif invoice_type=='sub' :
            domain.append(('subscription','=',True))
        else :
            domain.append(('advertising','=',False))
            domain.append(('subscription','=',False))


        result  = "Parsed arguments are :\n"
        result += "- domain : %s \n" % domain
        result += "- invoice date : %s \n" % invoice_date
        result += "- operating unit : %s \n" % ou_objects[0].name
        orderlines = self.search(domain)

        if len(orderlines)==0:
            result += "No orderlines in selection."
            return result


        result     += "\nOrderlines selected for invoicing : %s\n" % len(orderlines)
        aolmi_obj  = self.env['ad.order.line.make.invoice']
        post_date  = date.today().strftime('%Y-%m-%d')
        eta        = datetime.now()
        size       = 100
        chop_res   = aolmi_obj.make_invoices_split_lines_jq(invoice_date, post_date, orderlines, eta, size)
        result    += chop_res + "\n"
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


