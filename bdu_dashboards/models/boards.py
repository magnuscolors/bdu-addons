# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Board(models.AbstractModel):
    _inherit = 'board.board'

    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """
        Overloads board field_view_get.
        @return: Dictionary of Fields, arch and toolbar for a team dashboard.
        """
        
        res = super(Board, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if res['name'] in ('Team dashboard Alkmaar',  'Team dashboard Haarlem', 
                           'Team dashboard Barneveld', 'Team dashboard Online',
                           'Team dashboard Vakmedia',   'Team dashboard BDUprint',
                           'Directors dashboard' ) :
            #search custom_view possibly made by other user
            custom_view = self.sudo().env['ir.ui.view.custom'].search([('ref_id', '=', view_id)], limit=1)
        else :
            custom_view = self.env['ir.ui.view.custom'].search([('user_id', '=', self.env.uid), ('ref_id', '=', view_id)], limit=1)
        if custom_view:
            res.update({'custom_view_id': custom_view.id,
                        'arch': custom_view.arch})
        res.update({
            'arch': self._arch_preprocessing(res['arch']),
            'toolbar': {'print': [], 'action': [], 'relate': []}
        })
        return res
