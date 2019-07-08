# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models

    

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    #a suffix to put after the title/domain to distinguish between subscription products mnd keep backward compatibility
    subscription_suffix = fields.Char("Subscription suffix", help="Title and this suffix will compose a digital right on websites.") 



