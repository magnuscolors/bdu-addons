# -*- coding: utf-8 -*-

#import datetime
import logging
from odoo import api, fields, models, _
#from odoo.exceptions import UserError
#from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
#from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class Wave2Class(models.Model):
    _name = 'wave2.class'

    class_id = fields.Integer(string='Wave2 class id',  required=True)
    name     = fields.Char(string="Classified class", required=True)
    remark   = fields.Char(string="Remark", help="Any note")

    _sql_constraints = [
        ('wave2_id', 'unique(wave2_id)', "Already defined! You can only define a Wave2 number once; it has to be unique!"),
        ('name', 'unique(name)', "Already defined! You can only define a Wave2 classified class once; it has to be unique!"),
    ]
