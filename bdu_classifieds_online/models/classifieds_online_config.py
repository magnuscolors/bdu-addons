# -*- coding: utf-8 -*-

import base64, datetime, httplib, json, logging, pdb, requests, urllib
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

_logger = logging.getLogger(__name__)

class ClassifiedsOnlineConfig(models.Model):
    _name          = 'classifieds.online.config'
    _description   = 'Connection info for Classified Ads API interface to Drupal'

    server  	   = fields.Char(string='Server',help="servername, including protocol, e.g. https://prod.barneveldsekrant.nl" )
    method		   = fields.Char(string='Method and query',help="method with start slash, e.g. /api/v1")
    user           = fields.Char(string='User')
    password       = fields.Char(string='Password')
    ad_class       = fields.Many2one('product.category', 'Advertising Class')
    days_visible   = fields.Integer(string='Days visible on site')

    next_sync_start= fields.Datetime(string='Next sync start', help="Next sync will start from this timestamp")
    latest_run     = fields.Char(string='Latest run',          help="Date of latest run of Classifieds Online connector")
    latest_success = fields.Char(string='Latest success',      help="Youngest date when connector was shipping successfully")
    latest_status  = fields.Char(string='Latest status',       help="Status of latest run")
    latest_reason  = fields.Char(string='Latest reason',       help="Reason of status code of latest run")
    
    begin          = fields.Date(string='Begin',               help="Begin date of date range in format yyyy-mm-dd")
    
    #show only first record to configure, no options to create an additional one
    @api.multi
    def default_view(self):
        configurations = self.search([])
        if not configurations :
            server = "bdu.nl"
            self.write({'server' : server, 'next_sync_start' : datetime.datetime(1970,1,1,0,0)})
            configuration = self.id
            _logger.info("configuration created")
        else :
            configuration = configurations[0].id
        action = {
                    "type":"ir.actions.act_window",
                    "res_model":"classifieds.online.config",
                    "view_type":"form",
                    "view_mode":"form",
                    "res_id":configuration,
                    "target":"inline",
        }
        return action

    @api.multi
    def save_config(self):
        self.write({})
        return True

    #hook for automated actions
    @api.multi
    def automated_run(self):
        configurations = self.search([])
        if not configurations :
            _logger.info("Cannot start automated_run. Need a valid configuration")
            return False
        else :
            #start with previous end
            self = configurations[0]
            if not self.next_sync_start :
                 self.next_sync_start = datetime.datetime(1970,1,1,0,0)
            self.begin = datetime.datetime.strptime(self.next_sync_start,DEFAULT_SERVER_DATETIME_FORMAT).date()
            self.write({})
            return self.do_send()

    #started by automated run or send button
    @api.multi 
    def do_send(self):	    
        config = self[0] 
        #repair if not already done
        if not config.next_sync_start :
            config.next_sync_start = next_sync_start = datetime.datetime(1970,1,1,0,0)
        else :
            next_sync_start = datetime.datetime.strptime(config.next_sync_start,DTF)

        #run is based on config.begin, either given by user or automated run wrapper
        if not config.begin :
            raise ValidationError("Please provide a begin date")
            return False
        
        #get changed orderlines since begin
        orderlines=self.env['sale.order.line'].search([('ad_class', '=', config.ad_class.id),\
                                                          ('write_date', '>', config.begin+" T00:00:00")]).\
                      sorted(key = lambda r : r.write_date)

        #abandon if nothing to do
        if not orderlines :
            config.latest_run     = datetime.date.today()
            config.latest_status  = "N.A."
            config.latest_reason  = "No orderlines changed since "+config.begin+" T00;00:00"
            config.write({})
            _logger.info("No new classifieds to sync to website")
            return True

        #check title to domain translation
        domains = self.env['classifieds.online.mapping'].search([])
        mapped_titles = domains.mapped('title')
        filtered_orderlines = orderlines.filtered(lambda r: orderlines.title in mapped_titles)
        unmapped_orderlines = orderlines.filtered(lambda r: orderlines.title not in mapped_titles)

        #send it to websites
        if len(filtered_orderlines) != 0 :
            result = self.send_orderlines(config, filtered_orderlines)
        else :
            result = "No orderlines with a valid title-domain mapping."
       
        #leave testimonial of run
        if result == "ok" and len(unmapped_orderlines)==0:
            config.next_sync_start= orderline['write_date']
            config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
            config.latest_success = datetime.date.today()
            config.latest_status  = "Last record processed : "+result
            config.latest_reason  = "Sync OK"
            config.write({})
            _logger.info("Successfull shipment of %d classifieds orderlines created/changed after %s T00:00:00",\
                         len(orderlines), config.begin)
            return True
        else :
            config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
            config.latest_status  = "Error(s)"
            #todo:
            prologue = ""
            if len(unmapped_orderlines)>0 :
                prologue += "Orderlines not processed / no mapping for titles : "
                for line in unmapped_orderlines :
                    prologue += unmapped_orderlines.title.name+", "
            config.latest_reason  = prologue+result
            config.write({})
            _logger.info("Finished processing with errors. See connector page for details.")
            return False

    
    #sending orderline by consuming website API
    @api.multi 
    def send_orderlines(self, config, lines):
        #use config to prep api call      
        url         = config.server.strip()+config.method.strip()
        b_auth      = bytes(config.user+":"+config.password)
        headers     = {'authorization': "Basic " + base64.b64encode( b_auth),
                       'cache-control': "no-cache",
                       'content-type' : "application/x-www-form-urlencoded",
                      }
        
        #all orderlines in one batch (lines should have valid mapping, etc.)
        batch  = []
        domains = self.env['classifieds.online.mapping'].search([])
        for orderline in lines:
            #prepare
            order                          = orderline.order_id
            partner                        = order.partner_id
            domain                         = domains.filtered(lambda r: r.title.id == orderline.title.id)
            classified_ad={}
            #header info
            classified_ad['source']        = "Odoo"
            classified_ad['function_type'] = "single_order_update"
            classified_ad['partner']       = partner.id
            classified_ad['firstname']     = partner.firstname
            classified_ad['lastname']      = partner.lastname
            classified_ad['street']        = partner.street
            classified_ad['zip']           = partner.zip
            classified_ad['city']          = partner.city
            classified_ad['email']         = partner.email
            #orderline info
            classified_ad['orderline_nr']  = orderline.id
            classified_ad['count']         = str(int(orderline.product_uom_qty)) #number of mm
            classified_ad['start_date']    = orderline.issue_date
            classified_ad['end_date']      = (datetime.datetime.strptime(orderline.issue_date, DF)+datetime.timedelta(days=config.days_visible)).strftime(DF)  
            classified_ad['category']      = orderline.analytic_tag_ids[0].name
            classified_ad['domain']        = domain[0].domain
            classified_ad['description']   = orderline.layout_remark #needs latest amendments in Odoo wave2 interface
            #consolidate result
            batch.append(classified_ad) 
        payload={}
        payload['batch'] =  batch

        #actual send plus logging
        try :
            response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
        except :            
            _logger.error("No connection error on Drupal update for classifieds orders batch")
            return "No connection"
        if response.status_code == requests.codes.ok :  # equal 200 ok
            _logger.info("Successful Drupal update for classifieds orders batch")
            return "ok"
        elif response.status_code in list(range(100, 600)) :
            _logger.error("Bad response,"+str(response.status_code)+", "+response.content+ " on Drupal update for classifieds orders batch")
            return "bad response,"+str(response.status_code)+", "+response.content
        else:
            msg=str(response.json()['message'])
            _logger.error("Bad response,"+str(response.status_code)+", "+ msg+" on Drupal update for classifieds orders batch")
            return "bad response,"+str(response.status_code)+", "+msg





	