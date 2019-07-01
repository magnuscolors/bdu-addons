# -*- coding: utf-8 -*-

#import datetime
import logging
from odoo import api, fields, models, _
#from odoo.exceptions import UserError
#from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
#from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class TelecatsTicket(models.Model):
    _name = 'telecats.ticket'
    _rec_name = 'filename'
    
    source = fields.Many2one('project.source', string='Source')
    filename = fields.Char(string='Ticket filename',  required=True)
    excerpt = fields.Char(string="Subject", size=128)
    content = fields.Char(string="File content", required=True)

    ticket_id = fields.Many2one('project.issue', string="Issue")
    remark = fields.Char(string="Reason for status", size=128)
    state = fields.Selection([
							    ('collected', 'Collected'),
							    ('done','Done'),
							    ('error','Error'),
							    ('cancel', 'Cancelled'),
							    ('skip', 'Skip'),
							    ('input_error', 'Input error')
							  ],
							    'State', index=True,  default='collected',
						        help=' * The \'Collected\' status is set after collecting the order. \
						        \n* The \'Done\' status is set after successfully registring an Odoo order and partner. \
						        \n* The \'Error\' status is set after an error and leaves the opportunity to correct the order content. \
						        \n* The \'Cancelled\' status may be invoked by the user to ignore the order for further processing.\
						        \n* The \'Skip\' status may be used to temporarily skip an order in error to keep processing the other orders.\
						        \n* The \'Input error\' status is for collected files that are sure to crash when they are to be processed. User must fix this first before changing state to \'Collected\'.')

   