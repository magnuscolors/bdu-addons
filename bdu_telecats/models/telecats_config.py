# -*- coding: utf-8 -*-

import base64, csv, datetime, ftputil, ftputil.session, logging, os, re, time
from unidecode import unidecode
#import xml.etree.ElementTree as et
from lxml import etree as et

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

_logger = logging.getLogger(__name__)

class TelecatsConfig(models.Model):
    _name = 'telecats.config'

    server1 = fields.Char(string="Server", copy=False, help="URL excluding protocol. E.g. ftp.mycompany.com")
    server_dir1 = fields.Char(string="Server dir.", help="A server directory to work from or empty")
    user1 = fields.Char(string="Login", copy=False)
    password1 = fields.Char(string="Password", copy=False)
    done_dir1 = fields.Char(string="Server done directory", copy=False, help="Directory to move ticket to after completion, e.g. /done")
    done_dir_active1 = fields.Boolean(string="Activate done directory", help="Files are only moved when activated")
    work_dir1 = fields.Char(string="Local work directory", copy=False, help="Local temporary directory. Files are removed after completion.")
    status1 = fields.Char(string="Status file collect", copy=False)
    source1 = fields.Many2one('project.source', string="Source") 
    

    server2 = fields.Char(string="Server", copy=False, help="URL excluding protocol. E.g. ftp.mycompany.com")
    server_dir2 = fields.Char(string="Server dir.", help="A server directory to work from or empty")
    user2 = fields.Char(string="Login", copy=False)
    password2 = fields.Char(string="Password", copy=False)
    done_dir2 = fields.Char(string="Server done directory", copy=False, help="Directory to move ticket to after completion, e.g. /done")
    done_dir_active2 = fields.Boolean(string="Activate done directory", help="Files are only moved when activated")
    work_dir2 = fields.Char(string="Local work directory", copy=False, help="Local temporary directory. Files are removed after completion.")
    status2 = fields.Char(string="Status file collect", copy=False) 
    source2 = fields.Many2one('project.source', string="Source") 
    
    #business rules
    check_titles = fields.Boolean(string="Check title validity") 
    days_for_prio2 = fields.Integer(string="Days for prio2", copy=False)
    days_for_prio3 = fields.Integer(string="Days for prio3", copy=False)
    zip_format = fields.Char(string="Zip format", help="Use regular expression syntax")
    sla = fields.Integer(string="Time to deadline (secs)")
    priority_period = fields.Integer(string="Days for priority", help="Number of days to count issues to get priority")
    
    #defaults for ticket
    default_assignee = fields.Many2one('res.users', ondelete='set null', string="Responsible")
    default_priority = fields.Selection([('0','low'),('1','normal'),('2','high')], string="Default priority")
    default_issue_type = fields.Many2one('project.issue.type', string="Default issue type")
    default_project = fields.Many2one('project.project', string="Default project")
    task_id = fields.Many2one('project.task', string="Default task")
    default_stage = fields.Many2one('project.task.type', string="Default stage")
    #default_kanban_state = fields.Many2one('kanban.state', string="Default kanban state")
    default_tag = fields.Many2one('project.tags', "Default tag")

    #defaults for new customer
    account_manager = fields.Many2one('res.users', ondelete='set null', string="Account manager")
    sector_id = fields.Many2one('res.partner.sector', ondelete='set null', string="Default Sector")  
    country_id = fields.Many2one('res.country', ondelete='set null', string="Default Country") 
    partner_payment_mode_id = fields.Many2one('account.payment.mode', string="Payment Mode")
    partner_payment_term_id = fields.Many2one('account.payment.term', string="Payment terms")
    transmit_method_id = fields.Many2one('transmit.method', string="Invoice transmission method")

    status = fields.Char(string="Status ticket processing")

    #show only first record to configure, no options to create an additional one
    @api.multi
    def default_view(self):
        configurations = self.search([])
        if not configurations :
            server1 = "URL excluding protocol. E.g. : ftp.mycompany.nl"
            self.write({'server1' : server1})
            configuration = self.id
        else :
            configuration = configurations[0].id
        action = {
                    "type":"ir.actions.act_window",
                    "res_model":"telecats.config",
                    "view_type":"form",
                    "view_mode":"form",
                    "res_id":configuration,
                    "target":"inline",
        }
        return action 


    @api.multi
    def save_config(self, vals):
        msg = 'Configuration saved'
        self.write({'status' : msg, 'status' : msg})
        return True

    @api.multi
    def automated_run(self):
        self.get_files()
        self.process_tickets()
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
            ftp = ftputil.FTPHost(config.server1, config.user1, config.password1, session_factory = psf)
            msg = 'Connection OK'
        except Exception, msg:
            msg = "Invalid FTP configuration."
            _logger.exception(msg)
            config.write({'status' : msg})
            return msg
        
        #Transfer files, init dirs
        if config.server_dir1 :
            server_dir=config.server_dir1.strip()
        else :
            server_dir=""
        if not server_dir.endswith("/") :
            server_dir += "/"

        if config.done_dir1 :
            done_dir=config.done_dir1.strip()
        else :
            done_dir=""
        if not done_dir.endswith("/") :
            done_dir += "/"

        work_dir=config.work_dir1.strip()
        if not work_dir.endswith("/") :
            work_dir += "/"

        done_dir_active = config.done_dir_active1
        status_field = 'status1'
        source = config.source1
        
        #Transfer files, actual move
        n=0
        errors = 0
        skipped = 0
        try:
            for file in ftp.listdir(server_dir):
                if ftp.path.isfile(server_dir+file) and file.endswith(".xml"):
                    _logger.info("File to transfer : " + server_dir+file)
                    ftp.download(server_dir+file, work_dir + file)
                    rc = self.store_telecats_ticket(work_dir, file, source)
                    if rc :
                        n += 1
                        #move ticket on ftp server if activated
                        if done_dir_active :
                            ftp.rename(server_dir+file, done_dir+File)
                    else :
                        errors +=1
                else :
                    skipped += 1
                    _logger.info("Skipping : " +file)
            ftp.close()
            if n==0 and errors == 0:
                msg = "No files to collect"
            elif n>0 and errors == 0 :
                msg = str(n)+" Files successfully transfered"
            else :
                msg = str(n)+ " Files successfully transfered and " + str(errors) + " files not transferred because of errors"
            _logger.info(msg)
            config.write({status_field : msg})
            return msg
        except Exception:
            msg="Error during file transfer"
            _logger.exception(msg)
            config.write({status_field : msg})
            return msg

    @api.multi
    def store_telecats_ticket(self, work_dir, filename, source) :
        excerpt = ""
        state   = "collected"
        remark  = ""
        #get content
        try : 
            f = open(work_dir + filename, "r")
            content = f.read()
        except Exception :
            return False
        #prettyfy content
        try :
            xml_root=et.fromstring(content.strip())
            content=et.tostring(xml_root, pretty_print=True).replace("\n\n","\n")
        except Exception, e : 
            excerpt = "n.a."
            remark  = "Unable to estimate xml root, error : " + str(e) 
            state   = "input_error"
        #get subject
        if not excerpt :
            try :
                line=xml_root.find("KLT_PK").find("KON_KD")
                excerpt=line.text or "n.a."
            except Exception, e :
                excerpt = "n.a."
                remark  = "Error while retrieving KLT_PK/KON_KD tag"
                state   = "input_error"
        if len(excerpt)>21 :
            excerpt = excerpt[0:21]+"..."
        #save record and cleanup
        fname = filename.replace(".xml","")
        telecats_tickets = self.env['telecats.ticket'].search([('filename','=',fname)])
        if len(telecats_tickets)==0 :
            telecats_tickets.create({'source'  : source.id, 
                                     'name'    : fname, 
                                     'filename': fname, 
                                     'content' : content,
                                     'excerpt' : excerpt,
                                     'state'   : state,
                                     'remark'  : remark,
                                     })
        else :
            telecats_tickets[0].write({
                                     'content' : content, 
                                     'excerpt' : excerpt,
                                     'state'   : state,
                                     'remark'  : remark, })
        f.close()
        os.unlink(work_dir + filename)
        return True

    @api.multi
    def process_tickets(self):
        #get config
        configs = self.search([])
        config  = configs[0]
        if not config:
            msg = "Telecats connector configuration does not exist, please configure."
            _logger.exception(msg)
            config.write({'status' : msg})
            return

        #standard exit on fatal error
        def abort(config, ticket, msg) :
            ticket.state = 'error'
            ticket.remark = msg
            _logger.error("Fatal error. "+msg+". Processing aborted.")
            config.write({'status' : "Fatal error. "+msg+" Processing aborted."})
            return
        
        #get tickets to process
        tickets=self.env['telecats.ticket'].search([('state','in',('collected','error'))])
        if len(tickets)==0:  
            config.write({'status' : "No tickets to process"})
            return
        
        #init, then cycle through tickets
        errors = 0
        skip   = 0
        for ticket in tickets :
            xml_root = et.fromstring(ticket.content.strip())

            #skip if title not to be processed
            if config.check_titles :
                title = str(xml_root.find("KLT_PK").findtext("PRG_KD").strip())
                titles_to_import = self.env['sale.advertising.issue'].search([ ('parent_id','=', False),
                                                                               ('code','=',title)
                                                                            ])
                if len(titles_to_import)==0 :
                    skip += 1
                    ticket.state = 'skip'
                    ticket.remark='Title '+ title+ ' not defined for import'
                    continue
                if len(titles_to_import) > 1 :
                    skip += 1
                    ticket.state = 'skip'
                    ticket.remark='Title '+ title+ ' has multiple definitions in \'Titles to import\''
                    continue
                if not titles_to_import[0].import_service_requests :
                    skip += 1
                    ticket.state = 'skip'
                    ticket.remark='Title '+ title+ ' import marked as inactive'
                    continue

            #customer
            customer = self.parse_into_partner_details(xml_root)

            #process only when zip is correct
            if config.zip_format :
                if not re.match(config.zip_format, customer['zip']) :
                    errors += 1
                    ticket.state = 'error'
                    ticket.remark='Zip format not correct : ' + customer['zip']
                    continue
            
            #search by email, skip ticket if error
            if customer['email'] :
                partner = self.search_update_by_email(customer)
                if type(partner) in [unicode, str] :
                    errors += 1
                    ticket.state='error'
                    ticket.remark='Error searching email, '+ partner
                    continue


            #if not found, search by name, zip and street_number. Skip ticket if error
            if not partner :
                partner = self.search_update_by_name(customer)
                if type(partner) in [unicode, str] :
                    errors += 1
                    ticket.state = 'error'
                    ticket.remark='Error searching by name, ' + partner
                    continue

            #make partner if not found (probably a reader of free title)
            if not partner :
                partner = self.env['res.partner'].create(customer)
                if not partner or type(partner) in [unicode, str] :
                    errors += 1
                    ticket.state = 'error'
                    ticket.remark="Error creating partner " + (str(partner) or "")
                    continue


            #make a ticket
            parsed_ticket = self.parse_into_ticket_details(xml_root, partner, ticket)
            if type(parsed_ticket) in [unicode, str] :
                errors += 1
                ticket.state='error'
                ticket.remark='Error parsing ticket, '+ parsed_ticket
                continue
            odoo_tickets = self.env['project.issue'].search([ ('ext_ref','=', parsed_ticket['ext_ref']),
                                                              ('source', '=', parsed_ticket['source'])
                                                           ])
            if len(odoo_tickets) == 1 :
                odoo_ticket=odoo_tickets[0]
                if odoo_ticket.stage_id.name in ('done', 'Done', 'Afgehandeld'):
                    errors += 1
                    ticket.state = 'error'
                    ticket.remark= 'Cannot update already resolved ticket'
                    continue
                odoo_ticket.write(parsed_ticket)
                ticket.remark = odoo_ticket.name
                ticket.state = 'done'
            elif len(odoo_tickets) > 1 :
                errors += 1
                ticket.state = 'error'
                ticket.remark="Multiple tickets with client ticket ref "+ticket_header['ext_ref']
                continue
            else : 
                odoo_ticket = self.env['project.issue'].create(parsed_ticket)
                ticket.remark = odoo_ticket.name
                ticket.state = 'done'
                ticket.ticket_id = odoo_ticket.id

        #report stats
        msg= datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d %H:%M:%S" )+" "+str(len(tickets))+" telecats tickets processed."
        if errors>0 :
            msg += " "+str(errors)+" errors encountered. See collected tickets for details."
        else :
            msg += " No errors encounterd."
        _logger.info(msg)
        config.write({'status' : msg})
        return

    def parse_into_partner_details(self, xml) :
        naw = xml.find("KLT_PK").find("KLT_SRE_PK_MELDER")
        company_name = str(naw.findtext("SRE_NM"))
        if len(company_name)==0 : 
            is_company = False
        else :
            is_company = True;
        customer  = {
                    'is_company'     : is_company,
                    'street_name'    : str(naw.findtext("SRE_AD")),
                    'street_number'  : str(naw.findtext("SRE_HNR1")),
                    'street2'        : str(naw.findtext("SRE_HNR2")),
                    'zip'            : str(naw.findtext("SRE_PC")).replace(" ","").upper(),
                    'city'           : str(naw.findtext("SRE_PL")),
                    'country_id'     : self.search([])[0].country_id.id,
                    'website'        : "",
                    'sector_id'      : self.search([])[0].sector_id.id,
                    'secondary_sector_ids' : "",
                    'phone'          : str(naw.findtext("SRE_TEL")).replace(" ", ""),
                    'mobile'         : str(naw.findtext("SRE_TEL_MOBIEL")).replace(" ", ""),
                    'email'          : str(naw.findtext("SRE_E_MAIL")),
                    'lang'           : "nl_NL",
                    'message_is_follower' : 0, 
                    'customer'       : True,
                    'comment'        : "Partner geregistreerd/bijgewerkt door telecats",
                    'account_manager': self.search([])[0].account_manager.id,
                    }
        if is_company :
            customer['name'] = company_name
        else :
            customer['firstname']= str(naw.findtext("SRE_FIRST_NM")).strip()
            customer['initials'] = str(naw.findtext("SRE_P_VL")).strip()
            customer['infix'] = str(naw.findtext("SRE_P_VV")).strip()
            customer['lastname'] = str(naw.findtext("SRE_P_NM")).strip()
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
                #update invoice address and return company address to link ticket to
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
            return u"Multiple email addresses found."

    def search_update_by_name(self, customer) :

        if customer['is_company'] :
            name_to_search = customer['name']
            search_name = name_to_search.replace("bv","").replace("b.v.","").replace("nv","").replace("n.v.","").replace("vof", "").replace("BV","").replace("B.V.","").replace("NV","").replace("N.V.","")
        else :
            name_to_search = customer['firstname']+" "+customer['infix']+" "+customer['lastname']
            name_to_search = name_to_search.replace("  "," ")
        
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
            return u"Multiple addresses found. Make unique by email or name, zip and street number."

    def parse_into_ticket_details(self, xml, partner, ticket) :
        config     = self.search([])[0]
        note       = ""
        
        #name
        try:
            subject = str(xml.find("KLT_PK").findtext("KLT_ONDERWERP").strip()) 
        except Exception, msg:
            subject =  ""
        if len(subject)>50 :
            subject = subject[0:50]+"..."
        if subject=="" :
            subject = str(xml.find("KLT_PK").findtext("KON_KD").strip()) 

        #title, return error message if not ok
        title      = str(xml.find("KLT_PK").findtext("PRG_KD").strip())
        adv_issue = self.env['sale.advertising.issue'].search([('parent_id','=',False),('code','=',title)])
        if len(adv_issue)==0 :
            return u"title code '"+title+"' not found in advertising issues"
        if len(adv_issue)!=1 :
            return u"multiple titles found for code '"+title+"'."
        title_name = adv_issue[0].default_note.strip()
        title_id   = adv_issue[0].id

        #edition, if not found search on other days, return error message if not ok
        edition_date = str(xml.find("KLT_PK").findtext("PRJ_VERSCH_DD").strip())
        edition_date = datetime.datetime.strptime(edition_date, '%Y%m%d')
        edition_lower_boundary = edition_date - datetime.timedelta(days=7)
        search_date = edition_date
        edition_id = False
        while search_date > edition_lower_boundary and not edition_id :
            editions = self.env['sale.advertising.issue'].search([('parent_id',  '=', title_id),
                                                                  ('issue_date', '=', search_date.strftime('%Y-%m-%d'))])
            if len(editions)==1 :
                edition_id = editions[0].id
            elif len(editions)>1 :
                return u"Multiple editions found for title "+title+" on date "+search.date.strftime('%Y-%m-%d')
            else :
                search_date = search_date - datetime.timedelta(days=1)
        #time
        starttime  = str(xml.find("KLT_PK").findtext("KLT_TIJD")).strip()
        startday   = str(xml.find("KLT_PK").findtext("KLT_DD_MELDING")).strip() 
        start      = datetime.datetime.strptime(startday+starttime, '%Y%m%d%H:%M:%S')
        deadline   = start +datetime.timedelta(seconds=config.sla)
        if deadline.weekday()==6 :
            deadline = deadline + datetime.timedelta(days=2)
        if deadline.weekday()==0 :
            deadline = deadline + datetime.timedelta(days=1)
        confirmation_date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')

        #assign distributor based on zip or default assignee
        if edition_id :
            zip   = str(xml.find("KLT_PK").find("KLT_SRE_PK_MELDER").findtext("SRE_PC").strip())
            zip   = zip.replace(" ","").upper()
            zipnr = zip[0:4] 
            distributors = self.env['logistics.address.table'].search([('zip', '=', zipnr)])
            if len(distributors)==1 :
                user_id=distributors[0].partner_id
            elif len(distributors)>1 : 
                #todo: some more logic
                #for now we satisfice
                user_id=distributors[0].partner_id
            else :
                user_id = config.default_assignee.id
                note += "No distributor found for zip "+zipnr+"\n"
        else : 
            note += "No edition found for title "+title+ " between "+edition_date.strftime('%Y-%m-%d')+" and "+edition_lower_boundary.strftime('%Y-%m-%d')+"\n"
            note += "Hence no distributor assigned.\n"
            user_id = config.default_assignee.id

        #priority:
        if partner and title : 
            priority = self.get_priority(partner, title_id, edition_id, config.priority_period)
        else :
            priority = config.default_priority

        #description
        description = "Ticket details : "+"...."
        description += "\nNote : "+note

        ticket = {
                  'ext_ref'             : ticket.filename,
                  #'kanban_state'        : config.default_kanban_state,
                  'name'                : subject, 
                  'source'              : ticket.source.id, 
                  'user_id'             : user_id,  
                  'priority'            : priority,
                  'tag_ids'             : "", 
                  'partner_id'          : partner.id,
                  'email_from'          : partner.email,
                  'issue_type'          : config.default_issue_type.id,
                  'date_open'           : datetime.datetime.strftime(start, '%Y-%m-%d'),
                  'deadline'            : datetime.datetime.strftime(start, '%Y-%m-%d %H:%M:%S'),
                  'project_id'          : config.default_project.id,
                  'stage_id'            : config.default_stage.id,
                  'description'         : description,
                  'title_id'            : title_id,
                  'edition_date'        : datetime.datetime.strftime(edition_date, '%Y-%m-%d'),
                  'edition_id'          : edition_id,
                  #'title_name'          : title_name, 
                  #'partner_name'        : "",
                  #'street_number'       : "",
                  #'street_name'         : "",
                  #'city'                : "",
                  #'zip'                 : "",
                  #'task_id'             : config.task_id,
                  #'solution_id'         : ""
                }
        return ticket

    def get_priority(self, partner, title_id, edition_id, priority_period) :     
        #- high if unique tickets during last 56 days (abonnee, editie) >= 4
        #- normal if unique tickets during last 56 days (abonnee, editie) ==3
        #- low if unique tickets during last 56 days (abonnee, editie) <=2
        lower_search_boundary = datetime.datetime.now() - datetime.timedelta(days=priority_period)
        #todo:
        return self.search([])[0].default_priority


    

