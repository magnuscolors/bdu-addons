# -*- coding: utf-8 -*-

import base64, csv, datetime, ftputil, ftputil.session, logging, os, re, time
from unidecode import unidecode
import xml.etree.ElementTree as et

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

_logger = logging.getLogger(__name__)

class Wave2Config(models.Model):
    _name = 'wave2.config'

    server           = fields.Char(string="Server", copy=False, help="URL excluding protocol. E.g. ftp.mycompany.com")
    server_dir       = fields.Char(string="Server dir.", help="A server directory to work from or empty")
    user             = fields.Char(string="Login", copy=False)
    password         = fields.Char(string="Password", copy=False)
    status           = fields.Char(string="Status file collect", copy=False) 
    done_dir         = fields.Char(string="Server done directory", copy=False, help="Directory to move order to after completion, e.g. /done")
    done_dir_active  = fields.Boolean(string="Activate done directory", help="Files are only moved when activated")

    matserver        = fields.Char(string="Mat. server", copy=False, help="URL excluding protocol. E.g. ftp.mycompany.com")
    matserver_dir    = fields.Char(string="Mat. server dir.", help="Directory on server where material resides")
    
    work_dir         = fields.Char(string="Local work directory", copy=False, help="Local temporary directory. Files are removed after completion.")
    
    #channel          = fields.Many2one('mail.channel', ondelete='set null', string="Channel")

    #defaults for new partner
    partner_am       = fields.Many2one('res.partner', ondelete='set null', string="Account manager")
    sector_id        = fields.Many2one('res.partner.sector', ondelete='set null', string="Sector")  
    country_id       = fields.Many2one('res.country', ondelete='set null', string="Country") 
    zip_format       = fields.Char(string="Zip format", help="Use regular expression syntax")
    partner_payment_mode_id = fields.Many2one('account.payment.mode', string="Payment Mode")
    partner_payment_term_id   = fields.Many2one('account.payment.term', string="Payment terms")
    transmit_method_id        = fields.Many2one('transmit.method', string="Invoice transmission method")


    #defaults for order
    user_id          = fields.Many2one('res.users', ondelete='set null', string="Sales person") 
    discount_reason  = fields.Many2one('discount.reason', ondelete='set null', string="Discount_reason") 
    order_prefix     = fields.Char(string="Order prefix", copy=False)
    one_column_prod  = fields.Many2one('product.template', ondelete="set null", string="One column product")
    two_column_prod  = fields.Many2one('product.template', ondelete="set null", string="Two column product")
    prod_uom         = fields.Many2one('product.uom', ondelete="set null", string="Selling unit")
    payment_mode_id= fields.Many2one('account.payment.mode', string="Mode for Ideal")
    payment_term_id  = fields.Many2one('account.payment.term', string="Terms for Ideal")

    status2          = fields.Char(string="Status order processing")

    #show only first record to configure, no options to create an additional one
    @api.multi
    def default_view(self):
        configurations = self.search([])
        if not configurations :
            o_server = "URL excluding protocol. E.g. : ftp.mycompany.nl"
            self.write({'o_server':o_server})
            configuration = self.id
        else :
            configuration = configurations[0].id
        action = {
                    "type":"ir.actions.act_window",
                    "res_model":"wave2.config",
                    "view_type":"form",
                    "view_mode":"form",
                    "res_id":configuration,
                    "target":"inline",
        }
        return action 


    @api.multi
    def save_config(self, vals):
        msg = 'Configuration saved'
        self.write({'status' : msg, 'status2' : msg})
        return True

    @api.multi
    def do_job(self):
        self.get_files()
        self.process_orders()
        return


    @api.multi
    def get_files(self):
        #get connection parameters
        configs = self.search([])
        config  = configs[0]
        if not config:
            msg = "Connector configuration does not exist, please configure."
            _logger.exception(msg)
            config.write({'status' : msg})
            return msg
        
        # Initiate File Transfer Connection
        try:
            psf = ftputil.session.session_factory(port=21)
            ftp = ftputil.FTPHost(config.server, config.user, config.password, session_factory = psf)
            msg = 'Connection OK'
        except Exception, msg:
            msg = "Invalid FTP configuration."
            _logger.exception(msg)
            config.write({'status' : msg})
            return msg
        
        #Transfer files, init dirs
        if config.server_dir :
            server_dir=config.server_dir.strip()
        else :
            server_dir=""
        if not server_dir.endswith("/") :
            server_dir += "/"
        if config.done_dir :
            done_dir=config.dond_dir.strip()
        else :
            done_dir=""
        if not done_dir.endswith("/") :
            done_dir += "/"
        work_dir=config.work_dir.strip()
        if not work_dir.endswith("/") :
            work_dir += "/"
        
        #Transfer files, actual move
        n=0
        errors = 0
        try:
            for file in ftp.listdir(server_dir):
                if ftp.path.isfile(server_dir+file) and file.endswith(".xml"):
                    _logger.info("File to transfer : " + server_dir+file)
                    ftp.download(server_dir+file, work_dir + file)
                    rc = self.store_wave2_order(work_dir, file)
                    if rc :
                        n += 1
                        #move order on ftp server if activated
                        if config.done_dir_active :
                            ftp.rename(server_dir+file, done_dir+File)
                    else :
                        errors +=1
                else :
                    _logger.info("Skipping directory : " +file)
            ftp.close()
            if n==0 and errors == 0:
                msg = "No files to collect"
            elif n>0 and errors == 0 :
                msg = str(n)+" Files successfully transfered"
            else :
                msg = str(n)+ " Files successfully transfered and " + str(errors) + " files not transferred because of errors"
            _logger.info(msg)
            config.write({'status' : msg})
            return msg
        except Exception:
            msg="Error during file transfer"
            _logger.exception(msg)
            config.write({'status' : msg})
            return msg

    @api.multi
    def store_wave2_order(self, work_dir, filename) :
        try : 
            f = open(work_dir + filename, "r")
            content = f.read()
            xml_root=et.fromstring(content.strip())
            line=xml_root.find("RAD_PK").find("RAD_TEKST").find("REGEL")
            excerpt=line.text or "n.a."

            fname = filename.replace(".xml","")
            wave2_orders = self.env['wave2.order'].search([('filename','=',fname)])
            if len(wave2_orders)==0 :
                wave2_orders.create({'name': fname, 'filename': fname, 'content': content, 'excerpt':excerpt})
            else :
                wave2_orders[0].write({'content': content, 'excerpt':excerpt})

            f.close()
            os.unlink(work_dir + filename)
            return True
        except Exception :
            return False

    @api.model
    def process_orders(self, ids=None):
        #get config
        configs = self.search([])
        config  = configs[0]
        if not config:
            msg = "Wave2 connector configuration does not exist, please configure."
            _logger.exception(msg)
            config.write({'status' : msg})
            return

        #standard exit on fatal error
        def abort(config, order, msg) :
            order.state = 'error'
            order.remark = msg
            _logger.error("Fatal error. "+msg+". Processing aborted.")
            config.write({'status2' : "Fatal error. "+msg+" Processing aborted."})
            return
        
        #get orders to process
        orders=self.env['wave2.order'].search([('state','in',('collected','error'))])
        if len(orders)==0:  
            config.write({'status' : "No orders to process"})
            return
        
        #init, then cycle through orders
        errors = 0

        for order in orders :
            xml_root = et.fromstring(order.content.strip())
            customer = self.parse_into_partner_details(xml_root)

            #process only when zip is correct
            if not re.match(config.zip_format, customer['zip']) :
                errors += 1
                order.state = 'error'
                order.remark='Zip format not correct : ' + customer['zip']
                continue
            
            #search by email, skip order if error
            if customer['email'] :
                partner = self.search_update_by_email(customer)
                if type(partner)==unicode :
                    errors += 1
                    order.state='error'
                    order.remark='Error searching email, '+ partner
                    continue


            #if not found, search by name, skip order if error
            if not partner :
                partner = self.search_update_by_name(customer)
                if type(partner)==unicode :
                    errors += 1
                    order.state = 'error'
                    order.remark='Error searching by name, ' + partner
                    continue

            #make partner if not found
            if not partner :
                partner = self.env['res.partner'].create(customer)
                if not partner or type(partner)==unicode :
                    errors += 1
                    order.state = 'error'
                    order.remark="Error creating partner " + (str(partner) or "")
                    continue


            #prep an order header
            order_header = self.parse_into_header_details(xml_root, partner)
            odoo_orders = self.env['sale.order'].search([('client_order_ref','=',order_header['client_order_ref'])])
            if len(odoo_orders) == 1 :
                odoo_order=odoo_orders[0]
                if odoo_order.invoice_status=='invoiced' :
                    errors += 1
                    order.state = 'error'
                    order.remark= 'already invoiced'
                    continue
                odoo_order.write(order_header)
            elif len(odoo_orders) > 1 :
                errors += 1
                order.state = 'error'
                order.remark="Multiple orders with client order ref "+order_header['client_order_ref']
                continue
            else : 
                 odoo_order = self.env['sale.order'].create(order_header)

            #count lines to estimate last line value
            count = 0;
            search_error=False
            placements = xml_root.find("RAD_PK").find("PLAATSINGSDATA").getchildren()
            for placement in placements :
                region_id     = int(placement.findtext("UCL_PK"))
                region     = self.env['wave2.region'].search([('wave2_id','=',region_id)])
                if not region :
                    errors+=1
                    order.state  = 'error'
                    order.remark = "No region found for region code "+str(region_id)+'. '
                    search_error=True
                    continue
                issue_date = str(placement.findtext("PLAATSINGS_DATUM"))
                issue_date = datetime.date(int(issue_date[0:4]),int(issue_date[4:6]),int(issue_date[6:8]))
                weekday    = issue_date.weekday() #monday=0, sunday=6
                region_titles     = self.env['wave2.region.titles'].search([('region','=',region.id),('weekday','=',weekday)])
                if len(region_titles)==0 :
                    errors+=1
                    order.state  = 'error'
                    order.remark = "No titles found for region "+str(region.name)+" and date "+str(placement.findtext("PLAATSINGS_DATUM"))+'. '
                    search_error=True
                    continue
                else :
                    count     += len(region_titles)
            #prevent dividing by zero, which not something one orders
            if search_error :
                continue
            
            #e.g. 10 euro / 3 lines = 3,33 euro per line, but last line must be 3,34 euro to total to 10 euro   
            total_netto    = float(xml_root.find("RAD_PK").findtext("RAD_NETTO").replace('.','').replace(',','.'))
            net_per_line   = round(total_netto /  count,2);
            last_line_net  = round(net_per_line + total_netto - count * net_per_line, 2)

            #uniform listprice for all lines 
            q              = round(float(xml_root.find("RAD_PK").findtext("RAD_MM")),2)
            listprice      = last_line_net/q

            #create orderlines with a)possible alternative date, b)last line amended
            currentline = 0
            placements = xml_root.find("RAD_PK").find("PLAATSINGSDATA").getchildren()
            for placement in placements :
                region_id     = int(placement.findtext("UCL_PK"))
                region        = self.env['wave2.region'].search([('wave2_id','=',region_id)])
                issue_date_w2 = str(placement.findtext("PLAATSINGS_DATUM"))
                issue_date    = datetime.date(int(issue_date_w2[0:4]),int(issue_date_w2[4:6]),int(issue_date_w2[6:8]))
                weekday       = issue_date.weekday() #monday=0, sunday=6
                region_titles = self.env['wave2.region.titles'].search([('region','=',region.id),('weekday','=',weekday)])
                for region_title in region_titles :
                    currentline  += 1;

                    #adjust net if last line of order
                    if currentline == count :
                        net=last_line_net
                    else : 
                        net=net_per_line

                    #date switch if alternative date defined
                    dates = self.env['wave2.alternative.date'].search([('title','=',region_title.title.id),('wave2_date' ,'=', issue_date_w2)])
                    if len(dates)==1 :
                        issue_date = dates[0].issue.issue_date
                        if type(issue_date) in [unicode, str] :
                            issue_date = datetime.datetime.strptime(issue_date,DF).date()
                    elif len(dates)>1 :
                        abort(config, order, "Multiple alternative dates for "+region_title.title.name+" on "+issue_date_w2+"."  )
                        return
                    
                    #prep orderline
                    orderline_to_upsert= self.parse_into_orderline_details(xml_root, odoo_order, region_title.title, issue_date, region, net, listprice)
                    if type(orderline_to_upsert)==unicode :
                        abort(config, order, orderline_to_upsert)
                        return

                    #search orderline, update if present and in future, create if not found
                    current_orderlines = self.env['sale.order.line'].search([('ad_number','=',orderline_to_upsert['ad_number'])])
                    if len(current_orderlines) == 0 :
                        orderline_id = self.env['sale.order.line'].create(orderline_to_upsert)
                    elif len(current_orderlines) == 1 :
                        orderline_id = current_orderlines[0].write(orderline_to_upsert)
                    else :
                        abort(config, order, "Multiple orderlines with client order reference "+orderline_to_upsert['ad_number'])
                        return

            #set orderstatus and reset possible remark
            odoo_order.write({'state':'sale'})
            order.write({'state':'done', 'remark': 'Order '+odoo_order.name, 'order_id':odoo_order.id})

        #report stats
        msg= datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d %H:%M:%S" )+" "+str(len(orders))+" Wave2 orders processed."
        if errors>0 :
            msg += " "+str(errors)+" errors encountered. See collectted orders for details."
        else :
            msg += " No errors encounterd."
        _logger.info(msg)
        config.write({'status2' : msg})
        return

    def parse_into_partner_details(self, xml) :
        company_name = str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_NM"))
        if len(company_name)==0 : 
            is_company = False
        else :
            is_company = True;
        zip       = str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_C_PC")).replace(" ","")
        zip       = zip.replace(" ","").upper()
        customer  = {
                    'is_company'    : is_company,
                    'street_name'   : str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_C_AD")),
                    'street_number' : str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_C_HNR1")),
                    'street2'       : str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_HNR2")),
                    'zip'           : zip,
                    'city'          : str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_C_PL")),
                    'country_id'    : self.search([])[0].country_id.id,
                    'website'       : str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_WEBSITE")),
                    'sector_id'     : self.search([])[0].sector_id.id,
                    'secondary_sector_ids' : "",
                    'phone'         : str(xml.find("RAD_PK").findtext("SRE_TEL")).replace(" ", ""),
                    'mobile'        : str(xml.find("RAD_PK").findtext("SRE_TEL_MOBIEL")).replace(" ", ""),
                    'email'         : str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_E_MAIL")),
                    'lang'          : "nl_NL",
                    'message_is_follower' : 0, 
                    'customer'      : True,
                    'is_ad_agency'  : False,  
                    'trust'         : "normal",
                    'comment'       : "Partner geregistreerd/bijgewerkt door Wave2",
                    'customer_payment_mode_id' : self.search([])[0].partner_payment_mode_id.id,
                    'property_payment_term_id' : self.search([])[0].partner_payment_term_id.id,
                    'customer_invoice_transmit_method_id' : self.search([])[0].transmit_method_id.id,
                    }
        if is_company :
            customer['name'] = str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_NM"))
        else :
            customer['firstname']= str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_FIRST_NM"))
            customer['lastname'] = str(xml.find("RAD_PK").find("RAD_SRE_PK").findtext("SRE_P_NM"))
        return customer

        
    def update_found_partner(self, customer, partner) :
        fields_to_update = {
                    'street_name'   : customer['street_name'],
                    'street_number' : customer['street_number'],
                    'street2'       : customer['street2'],
                    'zip'           : customer['zip'],
                    'city'          : customer['city'],
                    'country_id'    : customer['country_id'],
                    'email'         : customer['email'],
                    'customer'      : True,
                    'customer_invoice_transmit_method_id' : self.search([])[0].transmit_method_id.id,

        }
        partner.write(fields_to_update)
        return

    def search_update_by_email(self, customer) :

        if  len(customer['email']) == 0 :
            return False
        ids = self.env['res.partner'].search([('email','=', customer['email'])])
        if len(ids) == 1 :
            partner=ids[0]
            if partner.type == 'invoice':
                #update invoice address and return company address to link order to
                customer.pop('is_company', None)
                customer.pop('name', None)  #not allowed
                self.update_found_partner(customer, partner)
                return partner.parent_id
            elif partner.type == 'contact':
                customer.pop('is_company', None)
                self.update_found_partner(customer, partner)
                return partner
            else :
                self.update_found_partner(customer, partner)
                return partner
        elif len(ids) == 0 :
            return False
        else :
            return "Multiple email addresses found."

    def search_update_by_name(self, customer) :

        if customer['is_company'] :
            name_to_search = customer['name']
            search_name = name_to_search.replace("bv","").replace("b.v.","").replace("nv","").replace("n.v.","").replace("vof", "").replace("BV","").replace("B.V.","").replace("NV","").replace("N.V.","")
        else :
            name_to_search = customer['firstname']+" "+customer['lastname']
        
        ids=self.env['res.partner'].search([('name',          'ilike', name_to_search),
                                            ('zip',           'ilike', customer['zip']),
                                            ('street_number', 'ilike', customer['street_number'])
                                            ])
        if len(ids)==1 :
            partner=ids[0]
            self.update_found_partner(customer, partner)
            return partner
        elif len(ids) == 0 :
            return False
        else :
            return "Multiple addresses found. Make unique by email or name, zip and street number."

    def parse_into_header_details(self, xml, partner) :
        config  = self.search([])[0]
        subject = str(xml.find("RAD_PK").find("RAD_TEKST").findtext("REGEL").strip().replace("<![CDATA", ""))
        first_line = subject.split("\n")[0][0:28]
        confirmation_date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        order_ref = str(xml.find("RAD_PK").findtext("RAD_PK") ) [3:9999] #NB cut 210 in front off client order ref, this used to be used for old administrative system
        order_header = {
                          #'state'              : "sale",       
                          'advertising'         : 1,        
                          'client_order_ref'    : config.order_prefix+order_ref,
                          'published_customer'  : partner.id, 
                          'partner_id'          : partner.id,
                          'partner_shipping_id' : partner.id,  
                          'partner_invoice_id'  : partner.id,  
                          'opportunity_subject' : subject,
                          'nett_nett'           : partner.is_ad_agency,
                          'confirmation_date'   : confirmation_date
                        }
        payment_according_wave2 = int(xml.find("RAD_PK").findtext("RAD_BETALING"))
        if payment_according_wave2 == 6 :
            order_header['payment_mode_id'] = config.payment_mode_id.id
            order_header['payment_term_id'] = config.payment_term_id.id
        else :
            order_header['payment_mode_id'] = ""
            order_header['payment_term_id'] = partner.property_payment_term_id.id
        return order_header


    def parse_into_orderline_details(self, xml, odoo_order, title, issue_date, region, net, listprice):
        config=self.search([])[0]
        
        #issue
        issues=self.env['sale.advertising.issue'].search([('parent_id','=',title.id),('issue_date','=',issue_date)])
        if len(issues) == 1 :
            issue = issues[0]
        elif len(issues) == 0 :
            return  "No issue for "+title.name+" on "+datetime.datetime.strftime(issue_date,"%Y-%m-%d")+"."
        else :
            return  "Multiple issues for "+title.name+" on "+datetime.datetime.strftime(issue_date,"%Y-%m-%d")+"."

        #product, template, ad class, medium
        width = int(xml.find("RAD_PK").findtext("RAD_BREEDTE"))
        lines = int(xml.find("RAD_PK").findtext("RAD_REGELS"))
        heigth= int(xml.find("RAD_PK").findtext("RAD_MM"))
        if width>80 :
            #columns = 2
            product = config.one_column_prod
        else :
            #columns = 1
            product = config.two_column_prod
        
        #prod_category   = product.categ_id
        if not product.categ_id :
            return "Missing product category for product "+product.name

        #master_category = prod_category.parent_id 
        if not product.categ_id.parent_id :
            return "Missing master category (medium) for category "+product.categ_id.name

        #pricelist
        price_lists = self.env['product.category'].search([('type', '!=', 'view'),('name','like', title.name)])
        if len(price_lists)==1 :
            price_list = price_lists[0]
        elif len(price_lists)==0:
            return "Missing product/pricelist category for title "+title.name+"."
        else :
            return "Multiple product/pricelist categories for title "+title.name+"."

        #product variant
        product_variants = self.env['product.product'].search([('categ_id', '=', price_list.id),
                                                         ('product_tmpl_id','=', product.id),
                                                         ('name','=', product.name)])
        if len(product_variants)==1 :
            product_variant = product_variants[0]; 
        elif len(product_variants)==0 : 
            return "No  product variant found for product template \""+product.name+"\" with pricelist (category) name holding \""+title.name+"\" in its name. Check for variant existance and/or right category for product variant, i.e. pricelist."
        else :
            return "Multiple product variants found for product template \""+product.name+"\" and pricelist (category) name holding "+title.name+" in its name."

        #link to material
        wav2_order_id = str(xml.find("RAD_PK").findtext("RAD_PK"))
        material_url  = "ftp://"+config.matserver+config.matserver_dir+"/"+wav2_order_id+".pdf"


        #check classified category
        classified_id      = int(xml.find("RAD_PK").findtext("RAD_RBR_PK"))
        classified_classes = self.env['wave2.class'].search([('class_id','=',classified_id)])
        if len(classified_classes) == 1 :
            classified_class = classified_classes[0]
        elif len(classified_classes) == 0 :
            return "No classified class for "+classified_id+"."
        else :
            return "Multiple classified classes for "+classified_id+"."

        #analytic tag
        tag_ids = self.env['account.analytic.tag'].search([('name', '=', classified_class.name)]) #todo: add domain page_class_domain
        if len(tag_ids) == 1 :
            analytic_tag = tag_ids[0]
        elif len(tag_ids) == 0 :
            return "No analytic tag for classified ad class "+classified_class.name+"."
        else :
            return "Multiple analytic tags for classified ad class "+classified_class.name+"."

        #unique orderline reference
        if wav2_order_id>2100013050 : 
            region_text = str(region.wave2_id)
            if int(region.wave2_id) < 10 :
                region_text = "0"+region_text
            ad_number = odoo_order.client_order_ref+"_"+region_text+title.name+"_"+datetime.datetime.strftime(issue_date, '%Y-%m-%d')
        else :
            #old style
            return "No support for legacy style orders"

        #orderline text for online publication in dtp remark field without CDATA
        rawtext = str(xml.find("RAD_PK").find("RAD_TEKST").findtext("REGEL"))

        orderline_details = {
                      'advertising'         : 1,               
                      'order_id'            : odoo_order.id, 
                      'medium'              : product.categ_id.parent_id.id,
                      'ad_class'            : product.categ_id.id,
                      'title'               : title.id,
                      'adv_issue'           : issue.id,
                      'product_template_id' : product.id,
                      'product_tmpl_id'     : product.id,
                      'product_id'          : product_variant.id,
                      'name'                : "Wave2 plaatsingsinfo: "+str(xml.find("RAD_PK").findtext("RAD_PLAATSINGS_INFO")),
                      'ad_number'           : ad_number,
                      'page_reference'      : "Rubriek : "+classified_class.name,
                      'url_to_material'     : material_url,          #ftp location of pdf made by WAV2
                      'layout_remark'       : rawtext,   #raw info into remarks for DTP-er
                      'product_uom'         : config.prod_uom.id,    
                      'product_uom_qty'     : round(float(xml.find("RAD_PK").findtext("RAD_MM")),2),
                      #'discount'           : 0,        
                      'discount_reason_id'  : config.discount_reason.id,
                      'subtotal_before_agency_disc':net,
                      'price_unit'          : listprice,
                      'analytic_tag_ids'    : [[6,0,[analytic_tag.id]]]   #list of triples, 3rd value of triple is a list of $rubriek_ids
                      }

        return orderline_details

