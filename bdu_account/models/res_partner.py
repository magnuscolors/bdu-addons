# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Magnus
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import re
from odoo import api, fields, exceptions, models, _

class DeliveryTerms(models.Model):
    _name = 'delivery.terms'
    _description = 'Terms Of Delivery'
    _rec_name = 'name'

    name = fields.Char('Name')

class PartnerStatus(models.Model):
    _name = 'partner.status'
    _description = 'Status'
    _rec_name = 'name'

    name = fields.Char('Name')

class Partner(models.Model):
    _inherit = 'res.partner'


    #override base_partner_sequence method to change sequence number padding
    @api.multi
    def _get_next_ref(self, vals=None):
        return self.env['ir.sequence'].next_by_code('res.partner.seq')

    @api.multi
    def _needsRef(self, vals=None):
        """
        Override base_partner_sequence method
        Checks whether a sequence value should be assigned to a partner's 'ref'

        :param self: recordset(s) of the partner object
        :param vals: known field values of the partner object
        :return: true if a sequence value should be assigned to the\
                      partner's 'ref'
        """
        res = super(Partner, self)._needsRef(vals)
        # to check partner belongs to res users or res company, if yes no sequence created
        if self._context.get('no_partner_sequence', False):
            return False
        return res

    promille_id = fields.Char('Promille ID')
    pubble_id = fields.Char('Pubble ID')
    zeno_id = fields.Char('Zeno ID')
    exact_id = fields.Char('Exact ID')
    facebook = fields.Char('Facebook')
    twitter = fields.Char('Twitter')
    linkedIn = fields.Char('LinkedIn')
    instagram = fields.Char('Instagram')
    date_established = fields.Date('Date Established')
    delievery_terms = fields.Many2one('delivery.terms','Terms of delivery')
    status = fields.Many2one('partner.status','Status')
    newsletter_opt_out = fields.Boolean('Newsletter opt-out')

    #default value for country
    country_id = fields.Many2one(default=166)

    #default credit policy
    def _default_credit_control_policy_id(self):
        return self.env.user.company_id.default_credit_control_policy.id

    credit_policy_id = fields.Many2one(default=_default_credit_control_policy_id)


    @api.constrains('zip')
    def _check_zip_format(self):
        default_country_id = int(self.env['ir.config_parameter'].search([('key','=','default_country')]).value) or 166 
        zip_format = int(self.env['ir.config_parameter'].search([('key','=','default_zip_format')]).value) or r'^[1-9]{1}[0-9]{3}[A-Z]{2}$' 
        for partner in self :
            if not partner.country_id or partner.country_id.id==default_country_id :
                if not re.match(zip_format, partner.zip) :
                    raise exceptions.ValidationError(_('ZIP format (numbers, letters) not correct. Please correct ZIP and/or country.'))
                    #return False
        return True

    # introduction of unique and rightly formatted email address needs some other changes first
    # so for now no constraints
    email = fields.Char(copy=False) #prevent double emailaddress
    @api.constrains('email')
    #def _check_email_format_and_uniqueness(self):
    #    #check format 
    #    if self.email:
    #        match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email)
    #        if match == None:
    #            raise exceptions.ValidationError('Not a valid email address format')
    #        #check if it is unique
    #        addresses = self.search([('email','=',self.email)])
    #        if self.id in addresses.ids :
    #            max = 1
    #        else :
    #            max = 0
    #        if len(addresses)>max :
    #            raise exceptions.ValidationError('Not a unique email address')

    @api.onchange('email')
    def _set_invoice_transmit_method(self):
        if self.email :
            self.customer_invoice_transmit_method_id = 1 # "E-mail"
        else :
            self.customer_invoice_transmit_method_id = 2 # "Post"


class Users(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        ctx = self._context.copy()
        ctx.update({'no_partner_sequence': True})
        self = self.with_context(ctx)
        return super(Users, self).create(vals)


class Company(models.Model):
    _inherit = "res.company"

    @api.model
    def create(self, vals):
        ctx = self._context.copy()
        ctx.update({'no_partner_sequence': True})
        self = self.with_context(ctx)
        return super(Company, self).create(vals)
