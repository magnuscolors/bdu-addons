# -*- coding: utf-8 -*-

#import datetime
import logging
from odoo import api, fields, models, _
#from odoo.exceptions import UserError
#from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
#from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class Wave2Order(models.Model):
    _name = 'wave2.order'
    _rec_name = 'filename'
    
    filename  = fields.Char(string='Wave2 filename',  required=True)
    excerpt   = fields.Char(string="Excerpt", size=128)
    content   = fields.Char(string="File content", required=True)

    order_id  = fields.Many2one('sale.order', string="Order")
    remark    = fields.Char(string="Reason for status", size=50)
    state     = fields.Selection([
							        ('collected', 'Collected'),
							        ('done','Done'),
							        ('error','Error'),
							        ('cancel', 'Cancelled'),
							        ('skip', 'Skip')
							      ],
							      'State', index=True,  default='collected',
						          help=' * The \'Collected\' status is set after collecting the order. \
						          \n* The \'Done\' status is set after successfully registring an Odoo order and partner. \
						          \n* The \'Error\' status is set after an error and leaves the opportunity to correct the order content. \
						          \n* The \'Cancelled\' status may be invoked by the user to ignore the order for further processing.\
						          \n* The \'Skip\' status may be used to temporarily skip an order in error to keep processing the other orders.')

   