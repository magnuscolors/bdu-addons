# -*- encoding: utf-8 -*-

import pdb
import base64, requests, logging
from datetime import datetime, timedelta
from odoo import api, fields, exceptions, models
#from dateutil.relativedelta import relativedelta
#from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        for order in self.filtered(lambda s: s.state in ['sale'] and s.subscription ):
            r = self.drupal_update(order)
            if r != "ok" :            
                _logger.warning(r)
        return result

    @api.multi
    def drupal_update(self, order):
        #use config to prep api call      
        configs     = self.env['digital.subscribers.config'].search([])
        if len(configs)==0 : 
            return "No digital subscribers config"
        config      = configs[0] 
        #return if api interface not activated
        if not config.api_active :
            config.api_last_msg = "API not active"
            return "ok"
        url         = config.api_server.strip()+config.api_method.strip()
        b_auth      = bytes(config.api_user+":"+config.api_password)
        headers     = {'authorization': "Basic " + base64.b64encode( b_auth),
                       'cache-control': "no-cache",
                       'content-type' : "application/x-www-form-urlencoded",
                      }

        payload={}
        #order header info
        payload['source']        = "Odoo"
        payload['function_type'] = "single_order_update"
        subscriber               = order.partner_shipping_id
        payload['subscriber']    = subscriber.id
        payload['firstname']     = subscriber.firstname
        payload['lastname']      = subscriber.lastname
        payload['street']        = subscriber.street
        payload['zip']           = subscriber.zip
        payload['city']          = subscriber.city

        #eligible titles
        titles = self.env['sale.advertising.issue'].search([('parent_id','=',False),('digital_paywall','=',True)])
        if len(titles)==0 :
            config.api_last_msg = "API aborted, no titles with a paywall."
            return "No titles with a paywall. So nothing to communicate. API call terminated."
        td = []
        for title in titles :
            td.append(str(title.name))

        #rights per orderline
        now=datetime.now().strftime("%Y-%m-%d")
        rights=[]
        for orderline in order.order_line:
            right={}
            right['orderline_nr']           = orderline.id
            right['previous_orderline_nr']  = orderline.subscription_origin
            
            if orderline.title.name in td :
                right['subscription'] = orderline.title.name
            else :
                right['subscription'] = ""
            
            if orderline.start_date <= now and orderline.end_date >= now :
                right['count']     = str(int(orderline.product_uom_qty)) 
            else :
                right['count']     = "0"
            
            right['startdate']     = orderline.start_date
            right['enddate']       = orderline.end_date
            rights.append(right)
        
        payload['rights'] =  rights
        
        #send it, give answer as triplet or plain ok
        try :
            response = requests.request("POST", url, data=payload, headers=headers)
        except :            
            config.api_last_msg = "No connection"
            return "no connection"
        if response.status_code == requests.codes.ok :  # equal 200 ok
            config.api_last_msg = "ok"
            return "ok"
        elif response.status_code in list(range(100, 600)) :
            config.api_last_msg = "bad response,"+str(response.status_code)+", "+response.content
            return "bad response,"+str(response.status_code)+", "+response.content
        else:
            msg=str(response.json()['message'])
            config.api_last_msg = "bad response,"+str(response.status_code)+", "+msg
            return "bad response,"+str(response.status_code)+", "+msg




