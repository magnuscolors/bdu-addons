# -*- coding: utf-8 -*-

#import datetime
import logging
from odoo import api, fields, models, _
#from odoo.exceptions import UserError
#from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
#from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class Wave2RegionTitles(models.Model):
    _name = 'wave2.region.titles'

    region     = fields.Many2one('wave2.region', string='Region',  required=True)
    weekday    = fields.Selection(string="Weekday", selection=[('6','Sunday'),('0','Monday'),('1','Tuesday'),('2','Wednesday'),('3','Thursday'),('4','Friday'),('5','Saturday')] )
    title      = fields.Many2one('sale.advertising.issue', string='Title',  required=True, domain="[('parent_id','=',False)]")
    remark     = fields.Char(string="Remark", help="Any note")

   