# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class PubbleOrderInterfaceConfig(models.Model):
    _name        = 'pubble.order.interface.config'
    _description = 'Pubble order interface'
    endpoint = fields.Char(string='Endpoint', help="Protocol, domain and method, e.g. https://ws.pubble.nl/Sales.svc?singleWsdl" )
    namespace = fields.Char(string='Namespace', help="Namespace tag and name, e.g. ns1:salesOrder")
    publisher = fields.Char(string='Publisher', help="Publisher's database, e.g. testbdudata")
    api_key = fields.Char(string='API key',  help="API key, e.g. 9tituo3t2qo4zk7emvlb")
     
    #show only first record to configure, no options to create an additional one
    @api.multi
    def default_view(self):
        configurations = self.search([])
        if not configurations :
            endpoint = "https://ws.pubble.nl/Sales.svc?singleWsdl"
            self.write({'enpoint' : endpoint})
            configuration = self.id
            _logger.info("Pubble order interface configuration record created")
        else :
            configuration = configurations[0].id
        action = {
                    "type":"ir.actions.act_window",
                    "res_model":"pubble.order.interface.config",
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
