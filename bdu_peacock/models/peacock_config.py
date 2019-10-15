# -*- coding: utf-8 -*-

import datetime, ftputil, ftputil.session, httplib, json, logging, pdb, requests, urllib
from lxml import etree
from tempfile import TemporaryFile
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class PeacockConfig(models.Model):
    _name = 'peacock.config'
    _description = 'Connection info for Schuiteman / Peacock Insights interface'
    server = fields.Char(string='Server', help="Servername, including protocol, e.g. https://prod.barneveldsekrant.nl")
    directory = fields.Char(string='Server subdir', help="Directory starting with slash, e.g. /api/v1, or empty")
    tempdir = fields.Char(string='Local temp dir', help="Local temporary directory. e.g. /home/odoo")
    user = fields.Char(string='User')
    password = fields.Char(string='Password')
    days = fields.Integer(string='History in days')
    pretty_print = fields.Boolean(string='Pretty print XML')
    use_sql = fields.Boolean(string='Use SQL')

    latest_run = fields.Char(string='Latest run', help="Date of latest run of Announcement connector")
    latest_status = fields.Char(string='Latest status', help="Log of latest run")

    end = fields.Date(string='End', help="End date of date range in format yyyy-mm-dd")

    # show only first record to configure, no options to create an additional one
    @api.multi
    def default_view(self):
        configurations = self.search([])
        if not configurations:
            server = "bdu.nl"
            self.write({'server': server})
            configuration = self.id
            _logger.info("configuration created")
        else:
            configuration = configurations[0].id
        action = {
            "type": "ir.actions.act_window",
            "res_model": "peacock.config",
            "view_type": "form",
            "view_mode": "form",
            "res_id": configuration,
            "target": "inline",
        }
        return action

    @api.multi
    def save_config(self):
        self.write({})
        return True

    def log_exception(self, msg, final_msg):
        config = self[0]
        _logger.exception(final_msg)
        config.latest_run = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
        config.latest_status = msg + final_msg
        config.write({})
        return

    def ship_xml_file(self, msg, xml, filename):
        config = self[0]

        f = open(config.tempdir + "/" + filename, "w")
        if self.use_sql:
            f.write(xml)
        else:
            data = etree.tostring(xml, pretty_print=self.pretty_print)
            f.write(data)
        f.close
        f = None  # to force releasing the file handle

        # Initiate File Transfer Connection
        try:
            port_session_factory = ftputil.session.session_factory(port=21, use_passive_mode=True)
            ftp = ftputil.FTPHost(config.server, config.user, config.password, session_factory=port_session_factory)
        except Exception, e:
            self.log_exception(msg, "Invalid FTP configuration")
            return False

        try:
            _logger.info("Transfering " + filename)
            if config.directory:
                target = str(config.directory) + '/' + filename
            else:
                target = '/' + filename
            source = config.tempdir + '/' + filename
            ftp.upload(source, target)
        except Exception, e:
            self.log_exception(msg, "Transfer failed, quiting....")
            return False

        ftp.close()

        return True

    @api.multi
    def automated_run(self):
        configurations = self.search([])
        if not configurations:
            # cannot use local method because there is no record
            _logger.exception(msg, "Cannot start automated_run. Need a valid configuration")
            return False
        else:
            # start with previous end
            self = configurations[0]
            self.end = datetime.date.today()
            self.write({})
            return self.do_send()

    @api.multi
    def do_send(self):
        msg = ""
        config = self[0]
        if not config:
            self.log_exception(msg, "No configuration found. <br>Please configure Schuiteman Peacock connector.")
            return False

        if not config.end:
            self.log_exception(msg, "Program not started. <br>Please provide a valid date")
            return False

        if not config.days:
            self.log_exception(msg, "Program not started. <br>Please provide a valid period (i.e. history in days)")
            return False

        if not config.server or not config.user or not config.password or not config.tempdir:
            self.log_exception(msg,
                               "Program not started. <br>Please provide a valid server/user/password/tempdir configuration")
            return False

        # calc begin and end date
        end = datetime.datetime.strptime(config.end, DEFAULT_SERVER_DATE_FORMAT).date()
        begin = end - datetime.timedelta(days=config.days)
        # for sql queries
        period_end = end.strftime('%Y-%m-%d')
        period_begin = begin.strftime('%Y-%m-%d')
        # for ORM search_reads
        end = end.strftime('UTC %Y-%m-%d T23:59:59')
        begin = begin.strftime('UTC %Y-%m-%d T00:00:00')

        # account.move
        if self.use_sql:
            cursor = self._cr
            # account.move
            query = 'SELECT  query_to_xml(\'SELECT account_move.id, account_move.name, \
                                                   account_move.create_date, account_move.create_uid, account_move.write_date, account_move.write_uid, \
                                                   account_move.date, account_move.operating_unit_id, account_move.company_id, account_move.journal_id, \
                                                   res_company.name as company_name, account_journal.name as journal_name \
                                            FROM account_move \
                                            LEFT JOIN res_company ON account_move.company_id = res_company.id \
                                            LEFT JOIN account_journal ON account_move.journal_id = account_journal.id \
                                            WHERE account_move.write_date>=$$' + period_begin + '$$ AND account_move.write_date<=$$' + period_end + '$$\',\
                                          true,false,\'\')'

            cursor.execute(query)
            am = cursor.fetchall()
            am_root = am[0][0]

            # account.move.line
            # analytic_account_ids and tax_ids are missing, needs a join to incorporate in answer
            # narration is not recognized
            query = 'SELECT  query_to_xml(\'SELECT  account_move_line.id,                account_move_line.name, \
                                                    account_move_line.create_date,       account_move_line.create_uid, creator2.name as create_id_name, \
                                                    account_move_line.write_date,        account_move_line.write_uid,  changer2.name as write_id_name, \
                                                    account_move_line.date, \
                                                    account_move_line.operating_unit_id, operating_unit.name as operating_unit_id_name, \
                                                    account_move_line.company_id,        res_company.name as company_id_name, \
                                                    account_move_line.account_id,        account_move_line.analytic_account_id, \
                                                    account_move_line.invoice_id,        account_invoice.name as invoice_id_name, \
                                                    account_move_line.quantity, \
                                                    account_move_line.product_id,        product_template.name as product_id_name, \
                                                    account_move_line.partner_id,        partner.name as partner_id_name, \
                                                    account_move_line.partner_bank_id,   account_move_line.ref,                  account_move_line.reconciled, \
                                                    account_move_line.statement_id,      account_move_line.bank_payment_line_id, account_move_line.full_reconcile_id, \
                                                    account_move_line.debit,             account_move_line.credit,               account_move_line.move_id \
                                            FROM account_move_line \
                                            LEFT JOIN res_users    as creators ON creators.id = account_move_line.create_uid          \
                                            LEFT JOIN res_partner as creator2 ON creator2.id = creators.partner_id                   \
                                            LEFT JOIN res_partner  as partner  ON partner.id = account_move_line.partner_id          \
                                            LEFT JOIN res_users    as changers ON changers.id = account_move_line.write_uid           \
                                            LEFT JOIN res_partner as changer2 ON changer2.id = changers.partner_id                   \
                                            LEFT JOIN res_company              ON res_company.id = account_move_line.company_id          \
                                            LEFT JOIN operating_unit           ON operating_unit.id = account_move_line.operating_unit_id   \
                                            LEFT JOIN product_product          ON product_product.id = account_move_line.product_id           \
                                            LEFT JOIN product_template        ON product_template.id = product_product.product_tmpl_id       \
                                            LEFT JOIN account_invoice          ON account_invoice.id = account_move_line.invoice_id           \
                                            WHERE account_move_line.write_date>=$$' + period_begin + '$$ AND account_move_line.write_date<=$$' + period_end + '$$\',true,false,\'\')'
            cursor.execute(query)
            aml = cursor.fetchall()
            aml_root = aml[0][0]

            # account.account
            # tag_ids needs joining
            # display_name not recognized
            query = 'SELECT  query_to_xml(\'SELECT  id, name, create_date, create_uid, write_date, write_uid, \
                                                company_id, code \
                                        FROM account_account WHERE deprecated>=$$False$$\',true,false,\'\')'
            cursor.execute(query)
            aa = cursor.fetchall()
            aa_root = aa[0][0]

        else:
            # account.move
            am = self.env['account.move'].search_read([('write_date', '>=', begin), \
                                                       ('write_date', '<=', end) \
                                                       ], ['id', \
                                                           'name', \
                                                           'create_date', \
                                                           'create_uid', \
                                                           'write_date', \
                                                           'write_uid', \
                                                           'date', \
                                                           'operating_unit_id', \
                                                           'company_id', \
                                                           'journal_id', \
                                                           'line_ids', \
                                                           ])

            # account.move.line
            aml = self.env['account.move.line'].search_read([('write_date', '>=', begin), \
                                                             ('write_date', '<=', end) \
                                                             ], ['id', \
                                                                 'name', \
                                                                 'create_date', \
                                                                 'create_uid', \
                                                                 'write_date', \
                                                                 'write_uid', \
                                                                 'date', \
                                                                 'operating_unit_id', \
                                                                 'company_id', \
                                                                 'account_id', \
                                                                 'analytic_account_id', \
                                                                 'analytic_line_ids', \
                                                                 'invoice_id', \
                                                                 'quantity', \
                                                                 'product_id', \
                                                                 'partner_id', \
                                                                 'partner_bank_id', \
                                                                 'ref', \
                                                                 'reconciled', \
                                                                 'tax_ids', \
                                                                 'statement_id', \
                                                                 'narration', \
                                                                 'bank_payment_line_id', \
                                                                 'full_reconcile_id', \
                                                                 # 'l10n_nl_date_invoice',      \
                                                                 'debit', \
                                                                 'credit', \
                                                                 'move_id', \
                                                                 ])

            # account.account
            aa = self.env['account.account'].search_read([('deprecated', '=', False) \
                                                          ], ['id', \
                                                              'name', \
                                                              'create_date', \
                                                              'create_uid', \
                                                              'write_date', \
                                                              'write_uid', \
                                                              'company_id', \
                                                              'display_name', \
                                                              'tag_ids', \
                                                              'code', \
                                                              ])

            # process into xml files
            am_root = etree.Element('account_move')
            aml_root = etree.Element('account_move_line')
            aa_root = etree.Element('account_account')

            # files as chapters in one xml document
            for am_record in am:
                self.add_element(am_root, am_record, 'record')
            for aml_record in aml:
                self.add_element(aml_root, aml_record, 'record')
            for aa_record in aa:
                self.add_element(aa_root, aa_record, 'record')

                # Transfer files
        self.ship_xml_file(msg, am_root, 'account_move.xml')
        self.ship_xml_file(msg, aml_root, 'account_move_line.xml')
        self.ship_xml_file(msg, aa_root, 'account_account.xml')

        # report and exit positively
        final_msg = "File transfer for Schuiteman / Peacock succesfull"
        _logger.info(final_msg)
        config.latest_run = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
        config.latest_status = msg + final_msg
        config.write({})
        return True

    def add_element(self, node, dict, tag):
        new_node = etree.Element(tag)
        node.append(new_node)
        for key, value in dict.iteritems():
            element = etree.Element(key)
            new_node.append(element)
            if type(value) in [str, int, float]:
                element.text = str(value)
            elif type(value) == unicode:
                element.text = value.encode("ascii", "replace")
            elif type(value) == bool:
                element.text = str(value)
            elif key.endswith('ids'):
                n = 0
                for v in value:
                    sub_node = etree.Element('_' + str(n))
                    element.append(sub_node)
                    sub_node.text = str(v)
                    n += 1
            elif type(value) == tuple and type(value[0]) == int and type(value[1]) == unicode:
                sub_node = etree.Element('id')
                element.append(sub_node)
                sub_node.text = str(value[0])
                sub_node = etree.Element('name')
                element.append(sub_node)
                sub_node.text = value[1].encode("ascii", "replace")
            elif type(value) == tuple:
                n = 0
                for v in value:
                    sub_node = etree.Element('_' + str(n))
                    element.append(sub_node)
                    if type(v) == unicode:
                        sub_node.text = v.encode("ascii", "replace")
                    else:
                        sub_node.text = str(v)
                    n += 1
            else:  # object
                self.add_element(element, value, key)
        return True
