# -*- coding: utf-8 -*-

import base64, datetime, httplib, json, logging, requests, urllib
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class RecruitmentConfig(models.Model):
    _name          = 'recruitment.config'
    _description   = 'Connection info for Recruitment API interface'
    server  	   = fields.Char(string='Server',          help="servername, including protocol, e.g. https://prod.barneveldsekrant.nl" )
    method		   = fields.Char(string='Method and query',help="method with start slash, e.g. /api/v1")
    user           = fields.Char(string='User')
    password       = fields.Char(string='Password')
    ad_class       = fields.Many2one('product.category', 'Advertising Class')

    next_to_sync   = fields.Datetime(string='Next Sync starts from', help="Next sync will start with ordeline updated after this timestamp")
    latest_run     = fields.Char(string='Latest run',      help="Date of latest run of Announcement connector")
    latest_success = fields.Char(string='Latest success',  help="Youngest date when connector was shipping successfully")
    latest_status  = fields.Char(string='Latest status',   help="Status of latest run")
    latest_reason  = fields.Char(string='Latest reason',   help="Reason of status code of latest run")
    
    begin		   = fields.Date(string='Begin',           help="Begin date of date range in format yyyy-mm-dd")
    
    #show only first record to configure, no options to create an additional one
    @api.multi
    def default_view(self):
        configurations = self.search([])
        if not configurations :
            server = "bdu.nl"
            self.write({'server' : server, 'next_to_sync' : datetime.datetime(1970,1,1,0,0)})
            configuration = self.id
            _logger.info("configuration created")
        else :
            configuration = configurations[0].id
        action = {
                    "type":"ir.actions.act_window",
                    "res_model":"recruitment.config",
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
            _logger.info("Cannot start automated_run. Need a valid recruitment configuration")
            return False
        else :
            #start with previous end
            self = configurations[0]
            if not self.next_to_sync :
                 self.next_to_sync = datetime.datetime(1970,1,1,0,0)
            self.begin = datetime.datetime.strptime(self.next_to_sync,DEFAULT_SERVER_DATETIME_FORMAT).date()
            self.write({})
            return self.do_send()

    #loop started by automated run (above) or send button push
    @api.multi 
    def do_send(self):   
        config = self[0] 
        if not config.begin :
            raise ValidationError("Please provide a begin date")
            return False
        
        #get changed orderlines since oldest_non_synced
        recruitments=self.env['sale.order.line'].search([('custom_orderline', '=', 'Recruitment'),\
                                                          ('write_date', '>', config.begin+" T00:00:00")]).\
                      sorted(key = lambda r : r.write_date)

        #abandon early if no changes
        if not recruitments :
            config.latest_run     = datetime.date.today()
            config.latest_status  = "N.A."
            config.latest_reason  = "No orderlines changed since "+(config.begin or "ever")
            config.write({})
            _logger.info("No new recruitments to sync to website")
            return True

        #send orderlines
        result = self.send_orderlines(recruitments)

        #leave testimonial of run result
        if result == "ok" :
            timestamps            = recruitments.mapped('write_date')
            config.next_to_sync   = max(timestamps)
            config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
            config.latest_success = datetime.date.today()
            config.latest_status  = result
            config.latest_reason  = "Sync OK"
            config.write({})
            _logger.info("Successfull shipment of %d recruitment orderlines created/changed after %s T00:00:00",\
                         len(recruitments), config.begin)
            return True
        else :
            config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
            config.latest_status  = "Error(s)"
            prologue              = "Errors. Oldest_non_synced kept at first error/no material. "
            config.latest_reason  = prologue+result
            config.write({})
            _logger.info("Finished processing with errors. See connector page for details.")
            return False

    
    #method to be called by order update or loop (above)
    @api.multi 
    def send_orderlines(self, orderlines):
        #use config to prep api call      
        config      = self[0] 
        url         = config.server.strip() + (config.method.strip() or "")
        b_auth      = bytes(config.user+":"+config.password)
        headers     = {'authorization': "Basic " + base64.b64encode( b_auth),
                       'cache-control': "no-cache",
                       'content-type' : "application/json",
                      }

        #assume all orderlines ok, since there is input validation, send all
        batch=[]
        for orderline in orderlines :
            order   = orderline.order_id
            partner = order.partner_id
            job_ad  = {}
            #header_info
            job_ad['source']          = 'Odoo'
            job_ad['function_type']   = 'singel_order_update'
            job_ad['partner']         = partner.id
            job_ad['firstname']       = partner.firstname
            job_ad['lastname']        = partner.lastname
            job_ad['street']          = partner.street
            job_ad['zip']             = partner.zip
            job_ad['city']            = partner.zip
            job_ad['email']           = partner.email
            #orderline: reference
            job_ad['order']           = order.id
            job_ad['orderline']       = orderline.id
            #orderline info:job
            job_ad['job_title']       = orderline.recruit_job_title 
            job_ad['job_description'] = orderline.recruit_job_description
            job_ad['employment']      = orderline.recruit_employment.name
            job_ad['function_group']  = orderline.recruit_function_group.name
            job_ad['education_level'] = orderline.recruit_education_level.name
            job_ad['industry']        = orderline.recruit_industry.name
            #orderline info:company
            job_ad['company_name']    = orderline.recruit_company_name
            job_ad['company_email']   = orderline.recruit_company_email
            job_ad['company_website'] = orderline.recruit_company_website        
            job_ad['company_logo']    = orderline.recruit_company_logo
            job_ad['company_street']  = orderline.recruit_company_street
            job_ad['company_zip']     = orderline.recruit_company_zip
            job_ad['company_city']    = orderline.recruit_company_city
            job_ad['company_region']  = orderline.recruit_company_region
            job_ad['company_province']= orderline.recruit_company_province.name
            job_ad['company_country'] = orderline.recruit_company_country.code
            #orderline info:where to publish
            job_ad['startdate']       = orderline.recruit_from_date
            job_ad['enddate']         = orderline.recruit_until_date
            domains                   = []
            for issue in orderline.recruit_adv_issue_ids :
                    domains.append(issue.code) #a.k.a. issue
            job_ad['domains']         = domains
            #consolidate result
            batch.append(job_ad)

        #send all orderlines
        payload={}
        payload['batch'] = batch
        try :
            response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
        except :
            return "No connection"
        if response.status_code == requests.codes.ok :  # equal 200 ok
            return "ok"
        elif response.status_code in list(range(100, 600)) :
            return "Bad response,"+str(response.status_code)+", "+response.content
        else:
            msg=str(response.json()['message'])
            return "Bad response,"+str(response.status_code)+", "+msg


	