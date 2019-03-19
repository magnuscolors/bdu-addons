# -*- coding: utf-8 -*-

import base64, datetime, ftputil,  ftputil.session, httplib, json, logging, os, requests, urllib, xlrd
from unidecode import unidecode
from lxml import etree 
from tempfile import TemporaryFile
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

class DeliveryConfig(models.Model):
    _name          = 'delivery.config'
    _description   = 'Connection info for newspaper deliveries'
    #_rec_name      = name

    name           = fields.Char(string="Configuration name")

    file_prefix    = fields.Char(string='File prefix')
    file_suffix    = fields.Char(string='File suffix', help="File type, e.g. .csv or .txt")
    file_format    = fields.Selection([('papo','Papo csv lijst'),('vakmedia','Vakmedia csv lijst'),('spreadit','SpreadIT XML')], string="File format") 
    offset_days    = fields.Integer(string='Offset in days')
    title_ids      = fields.Many2many('sale.advertising.issue', string='Titlels')
    carrier_ids    = fields.Many2many('delivery.carrier', string="Carriers")               #future
    delivery_ids   = fields.Many2many('delivery.list.type', string="Delivery Type")        #based on current subs implementation
    tempdir        = fields.Char(string='Local temp dir', help="Local temporary directory. e.g. /home/odoo")

    server  	   = fields.Char(string='Server',         help="FTP server" )
    directory	   = fields.Char(string='Server subdir',  help="Directory starting with slash, e.g. /api/v1, or empty")
    user           = fields.Char(string='User')
    password       = fields.Char(string='Password')
    use_ftp        = fields.Boolean(string='Use FTP')


    email_recipient= fields.Char(string='Email recipient')
    email_cc       = fields.Char(string='Email cc')
    email_subject  = fields.Char(string='Email subject')
    email_sender   = fields.Char(string='Email sender')
    use_email      = fields.Boolean(string='Use email')

    latest_run     = fields.Char(string='Latest run',     help="Date of latest run of Announcement connector")
    latest_status  = fields.Char(string='Latest status',  help="Log of latest run")
    
    active_date	   = fields.Date(string='Active on',      help="Date for which subscribers should be active in format yyyy-mm-dd")
    
    def save_config(self):
        self.write({})
        return True

    def log_exception(self, msg, final_msg):
        config = self[0] 
        _logger.warning(final_msg)
        config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
        config.latest_status  = msg+final_msg
        config.write({})
        return 


    @api.multi
    def automated_run(self, config_name):
        # automated call should use name of config as text parameter enclosed in brackets and followed by comma, like ("spreadit",)
        configurations = self.search([('name','=',config_name)])
        if not configurations :
            #cannot use local method because there is no record
            self.log_exception(msg, "Cannot start automated_run. Need a valid configuration")
            return False
        else :
            #start normal with today plus offset in days as active date
            self = configurations[0]
            self.active_date = datetime.date.today()+datetime.timedelta(days=self.offset_days)
            self.write({})
            return self.do_send()

    def days_before(self, date, n) :
        return (datetime.datetime.strptime(date,DEFAULT_SERVER_DATE_FORMAT).date()- datetime.timedelta(days=n)).strftime('%Y-%m-%d')  
    
    @api.multi 
    def do_send(self):	
        msg    = ""    
        config = self[0] 
        if not config :
            self.log_exception(msg, "No configuration found. <br>Please configure digital subscribers connector.")
            return False
       
        if not config.active_date :
            #raise ValidationError("Please provide a valid date")
            self.log_exception(msg, "Please provide a valid date.<br>Program aborted.")
            return False

        if    config.use_ftp   and (not config.server or not config.user or not config.password ) :
            self.log_exception(msg,"Program not started. <br>Please provide a valid ftp configuration")
            return False
        if    config.use_email and (not config.email_recipient or not config.email_subject or not config.email_sender) :
            self.log_exception(msg,"Program not started. <br>Please provide a valid email configuration")
            return False
        if not config.tempdir or not config.file_prefix or not config.file_suffix or not config.file_format:
            self.log_exception(msg,"Program not started. <br>Please provide a valid directory, file format, prefix and/or suffix")
            return False
        if not config.delivery_ids or config.offset_days=="" or not config.title_ids :
            self.log_exception(msg,"Program not started. <br>Please provide a valid delivery type, offset in day and/or title list")
            return False

        #eligible titles
        titles = []
        for title in config.title_ids :
            issues=self.env['sale.advertising.issue'].search([('parent_id','=',title.id),('issue_date','=',config.active_date),('subscription_title','=',True)])
            if len(issues)==1 :
                titles.append(title.name) #no str() because diacritic chars in e.g. esthé are non ascii
        if len(titles)==0 :
            self.log_exception(msg, "No issues found for date "+config.active_date+". Program terminated.")
            return False

        # subscriptions
        orderlines = self.env['sale.order.line']
        three_days_ago = self.days_before(config.active_date, 3)
        period_subs = [
            ('start_date', '<=', config.active_date),
            ('end_date', '>=', three_days_ago),
            #('company_id', '=', self.company_id.id),
            ('subscription', '=', True),
            ('state', '=', 'sale'),
            ('title', 'in', titles),
            ('product_template_id.digital_subscription','=', False), #not digital only subscription, but physical delivery needed
            ('number_of_issues', '=', 0)                             #period subscriptions
        ]
        counted_subs = [
            ('line_renewed', '=', False),
            ('subscription', '=', True),
            ('state', '=', 'sale'),
            ('title', 'in', titles),
            ('product_template_id.digital_subscription','=', False),  #not digital only subscription, but physical delivery needed
            ('number_of_issues', '!=', 0)                             #period subscriptions
        ]
        if config.delivery_ids :
            period_subs.append(('order_id.delivery_type', 'in', config.delivery_ids.ids))
            counted_subs.append(('order_id.delivery_type', 'in', config.delivery_ids.ids))

        set1 = orderlines.search(period_subs)
        set2 = orderlines.search(counted_subs)
        set2 = set2.filtered(lambda r: r.number_of_issues > r.delivered_issues) 
        period_and_counted_subs = set1 | set2
        
        subscriptions = period_and_counted_subs.sorted(key=lambda r: r.order_id.partner_shipping_id) 

        #filter for weekdays that product is active
        active_weekday = datetime.datetime.strptime(config.active_date, DEFAULT_SERVER_DATE_FORMAT).strftime('%A')
        def list_of_days(weekday_ids):
            wda=[]
            for wd in weekday_ids :
                wda.append(wd.name)
            return wda
        subscriptions = subscriptions.filtered(lambda r: active_weekday in  list_of_days(r.product_template_id.weekday_ids))

        #todo: filter for temp stop in orderline
        def no_temp_stop(date1, date2):
            if date1<= config.active_date and date2>=config.active_date :
                return False
            else :
                return True
        subscriptions = subscriptions.filtered(lambda r: no_temp_stop(r.tmp_start_date, r.tmp_end_date) )

        if len(subscriptions)==0 :
            self.log_exception(msg, "No subscriptions found. Program terminated.")
            return False

        # make file 
        filename      = str(config.tempdir)+"/"+str(config.file_prefix)+"_"+config.active_date+str(config.file_suffix)
        delivery_list = open(filename, "w")
        if config.file_format=='papo' :
            delivery_list = self.dance_for_papo(config, subscriptions, delivery_list)
            self.store_delivered_obligations(config, subscriptions, titles)
        elif config.file_format=='vakmedia' :
            delivery_list = self.content_for_vakmedia(config, subscriptions, delivery_list)
            self.store_delivered_obligations(config, subscriptions, titles)
        elif config.file_format=='spreadit' :
            delivery_list = self.content_for_spreadit(config, subscriptions, delivery_list)
            self.store_delivered_obligations(config, subscriptions, titles)
        else :
            self.log_exception(msg, "Unsupported file format. Program terminated.")
            return False
        delivery_list.close()
        delivery_list = None

        # send file by ftp
        if config.use_ftp :
            try:
                port_session_factory = ftputil.session.session_factory(port=21, use_passive_mode=True)
                ftp = ftputil.FTPHost(config.server, config.user, config.password, session_factory = port_session_factory)
            except Exception, e:
                self.log_exception(msg, "Invalid FTP configuration")
                return False

            if not self.ship_file(msg, filename, ftp) :
                return False
            ftp.close()

        # and/or send by email
        attachment = self.env['ir.attachment'].create({'name'       : filename,
                                                      'datas'      : base64.encodestring(open(filename).read()),
                                                      'datas_fname': filename,
                                                      'res_model'  : 'delivery.config',
                                                      'res_id'     : config.id
                                                     })
        if config.use_email :
            f              = open(filename)
            email_obj      = self.env['mail.mail']
            attachment_id  = 78
            email_template = {
                                'subject'   : config.email_subject,
                                'body_html' : "",
                                'email_from': config.email_sender,
                                'email_to'  : config.email_recipient,
                                'email_cc'  : config.email_cc,
                                'attachment_ids': [[6,0,[attachment.id]]]
            }
            email_id = email_obj.create(email_template)
            email_obj.send(email_id)
            f.close()

        #clean up
        os.unlink(filename)

        #report and exit positively
        final_msg = "Delivery information succesfully sent"
        _logger.info(final_msg)
        config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
        config.latest_status  = msg+final_msg
        config.write({})
        return True

    #
    # Tooling for filemakers
    #
   
    def init_days(self, date) :
        return self.days_before(date,1), self.days_before(date,2), self.days_before(date,3)  

    def make_concatenate(self, concat_char) :
        def concat(line, addition) :
            if addition : return line+concat_char+addition
            else :        return line+concat_char
        return concat

    #
    # The filemakers
    #
   
    def dance_for_papo(self, config, subscriptions, delivery_list) :
        line = ""
        yesterday, day_before_yesterday, three_days_ago = self.init_days(config.active_date)
        concat = self.make_concatenate(",")

        header= "abonnee_nr, abonnement_nr, achternaam, bedrijfsnaam, parent_name, name, street, zip, woonplaats, start_datum, cancel_datum, bij/af\r\n"
        delivery_list.write(header)

        for subscription in subscriptions :
            if subscription.date_cancel and subscription.date_cancel <= three_days_ago :
                continue
            subscriber = subscription.order_id.partner_shipping_id
            line = str(subscriber.ref)+","+str(subscription.id)
            line = concat(line, subscriber.lastname)
            line = concat(line, subscriber.parent_id.name)
            line = concat(line, subscriber.parent_id.name)
            line = concat(line, subscriber.name)
            line = concat(line, subscriber.street)
            line = concat(line, subscriber.zip)
            line = concat(line, subscriber.city)
            line = concat(line, subscription.start_date)
            line = concat(line, subscription.date_cancel)   
            if subscription.start_date == config.active_date and subscription.subscription_origin==0 :
                line = concat(line, "BIJ")
            #subscriptions that explicitly end
            elif subscription.date_cancel == yesterday or subscription.date_cancel == day_before_yesterday or subscription.date_cancel == three_days_ago :
                line = concat(line, "AF")
            #for products that do not renew
            elif (subscription.end_date == yesterday or subscription.end_date == day_before_yesterday or subscription.end_date == three_days_ago) and subscription.renew_product_id.product_tmpl_id.can_renew == False:
                line = concat(line, "AF")
            else :
                line = concat(line, "")  
            line = unidecode(line)         
            delivery_list.write(line+"\r\n")

        footer=""
        delivery_list.write(line)
        return delivery_list

    

    def content_for_vakmedia(self, config, subscriptions, delivery_list) :
        line = ""
        yesterday, day_before_yesterday, three_days_ago = self.init_days(config.active_date)
        concat = self.make_concatenate(",")
        
        #def concatx(line, var) :
        #    if var :
        #        return (line+","+str(var))
        #    else :
        #        return (line +",")

        header= "Abonneenummer, aantal, Bedrijfsnaam, afdeling, Voorletters, Tussenvoegsels, Achternaam, Straatnaam, Huisnummer+Toevoeging, Postcode, Plaats, Land\r\n"
        delivery_list.write(header)

        for subscription in subscriptions :
            if subscription.date_cancel and subscription.date_cancel <= three_days_ago :
                continue
            subscriber = subscription.order_id.partner_shipping_id
            line = str(subscriber.ref)+","+str(subscription.product_uom_qty)
            line = concat(line, subscriber.parent_id.name)
            line = concat(line, subscriber.department_id.name)
            line = concat(line, subscriber.initials)
            line = concat(line, subscriber.infix)
            line = concat(line, subscriber.lastname)
            line = concat(line, subscriber.street_name)
            line = concat(line, subscriber.street_number)
            line = concat(line, subscriber.zip)
            line = concat(line, subscriber.city)
            line = concat(line, subscriber.country_id.name)   
            line = unidecode(line)       
            delivery_list.write(line+"\r\n")
        footer=""
        delivery_list.write(footer)
        return delivery_list



    def content_for_spreadit(self, config, subscriptions, delivery_list) :
        yesterday, day_before_yesterday, three_days_ago = self.init_days(config.active_date)
        
        root = etree.Element('GBABO')
        tree = etree.ElementTree(root)   

        identificatie = etree.Element('IDENTIFICATIE')
        root.append(identificatie)   

        bron = etree.Element('BRON')
        bron.text='BDU'
        identificatie.append(bron)
          
        creadat = etree.Element('CREADAT')
        creadat.text = datetime.datetime.today().strftime("%d%m%Y %H:%M:%S")
        identificatie.append(creadat)  

        volgnr = etree.Element('VOLGNR')
        volgnr.text = datetime.datetime.today().strftime("%d%m%Y%H%M%S")  #shortcut: number based on timestamp
        identificatie.append(volgnr)

        type = etree.Element('TYPE')
        type.text = "COMPLEET"
        identificatie.append(type)


        distributie = etree.Element('DISTRIBUTIE')
        root.append(distributie)

        def child(parent, child_tag, text) :
            if not text : text = ""
            text = unidecode(text)
            child      = etree.Element(str(child_tag).upper().strip())
            child.text = str(text)
            parent.append(child)
            return child


        for subscription in subscriptions :
            if subscription.date_cancel and subscription.date_cancel <= three_days_ago :
                continue
            subscriber = subscription.order_id.partner_shipping_id
            
            klant      = etree.Element('KLANT')
            distributie.append(klant)

            child(klant, "mutsrt ", "START")
            child(klant, "mutdatum", datetime.date.today().strftime("%d%m%Y") )
            child(klant, "uitgever", "BDU")
            child(klant, "klantnr ", subscriber.ref)
            child(klant, "naam", subscriber.lastname)
            child(klant, "voornaam", subscriber.firstname)
            child(klant, "tussenvoegsel", subscriber.infix)
            child(klant, "toevoeging1", "")
            child(klant, "toevoeging2 ", "")
            child(klant, "straat", subscriber.street_name)
            child(klant, "huisnr", subscriber.street_number)
            child(klant, "huisnrtoev ", "") 
            child(klant, "huisnrtoevtm ", "")
            child(klant, "postcode", subscriber.zip)
            child(klant, "plaats   ", subscriber.city)
            child(klant, "land   ", subscriber.country_id.name)
            child(klant, "netnr   ", subscriber.phone)
            child(klant, "telnr  ", subscriber.phone)
            child(klant, "bezinfo  ", "")
            child(klant, "uitgave  ", subscription.title.name)
            child(klant, "editie", subscription.title.name)
            child(klant, "actie", "")
            child(klant, "aantal", "1")
            child(klant, "verschwijze", "0200500")
            child(klant, "mutreden", "")

        delivery_list.write(etree.tostring(root,pretty_print=True))
        return delivery_list


    def store_delivered_obligations(self, config, subscriptions, titles) :
        filename       = str(config.file_prefix)+"_"+config.active_date+str(config.file_suffix)
        std            = self.env['subscription.title.delivery']
        sdl            = self.env['subscription.delivery.list']
        lines          = self.env['subscription.delivery.line']
        now            = datetime.datetime.now().strftime('%Y-%m-%d')
        yesterday, day_before_yesterday, three_days_ago = self.init_days(config.active_date)

        #deliveries segmented per delivery type and title as subscription module uses
        for title in config.title_ids : 
            issues  = self.env['sale.advertising.issue'].search([('parent_id','=',title.id),('issue_date','=',config.active_date)])
            if len(issues) == 0 : 
                continue
            issue=issues[0]
            for delivery_type in config.delivery_ids :
                
                #title
                std_rec = std.search([('title_id','=', title.id)])
                if len(std_rec)==0 :
                    std_rec = std.create({'title_id' : title.id})
                else :
                    std_rec = std_rec[0]
                
                #delivery list (name can be flexible, i.e. cannot be searched for)
                sdl_rec = sdl.search([('issue_date','=',config.active_date),('delivery_id','=',std_rec.id),('type','=',delivery_type.id)])
                if len(sdl_rec)==0 :
                    sdl_rec = sdl.create({
                        'name'         : filename, 
                        'delivery_id'  : std_rec.id, 
                        'delivery_date': now,
                        'type'         : delivery_type.id,
                        'title_id'     : title.id,
                        'issue_id'     : issue.id,
                        'issue_date'   : config.active_date
                    })
                else :
                    sdl_rec = sdl_rec[0]
                    #update filename and date
                    sdl_rec.write({'name'         : filename,
                                   'delivery_date': now,
                                   'state'        : 'draft'  #reset possible cancel
                    })

                #delivery lines
                subs_for_title_and_delivery_type = subscriptions.filtered(lambda r: r.title.id == title.id and r.order_id.delivery_type.id == delivery_type.id)

                for subscription in subs_for_title_and_delivery_type :
                    if subscription.date_cancel and subscription.date_cancel <= three_days_ago :
                        continue
                    #all types of subscriptions
                    #if subscription.product_template_id.number_of_issues == 0 :
                    #    continue
                    subscriber = subscription.order_id.partner_shipping_id
                    payload = {
                        'delivery_list_id'    : sdl_rec.id,
                        'sub_order_line'      : subscription.id,
                        'subscription_number' : subscription.order_id.id,
                        'partner_id'          : subscriber.id,
                        'product_uom_qty'     : subscription.product_uom_qty,
                        'title_id'            : title.id,
                        'issue_id'            : issue.id,
                        'state'               : 'draft'
                    }
                    deliveries=lines.search([('delivery_list_id','=',sdl_rec.id),('sub_order_line','=',subscription.id)])
                    if len(deliveries) != 0 :
                        delivery=deliveries[0]
                        delivery.write(payload)
                    else :
                        delivery = lines.create(payload)

        return
