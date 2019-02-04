from odoo import tools, api, fields, models, _    

class Partner(models.Model):
    _inherit = ['res.partner']

    invoice_frequency = fields.Selection(selection_add=[('Exception','Exception')]) 