# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Megis - Willem Hulshof - www.megis.nl
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs.
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company like Veritos.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
##############################################################################

{
    'name'       : 'BDU Account',
    'version'    : '0.9',
    'category'   : 'accounts',
    'description': """
This module adds customization for BDU Media, like :\n
- product variant name\n
- order and orderline layout\n
- partner attributes (like social media id's)\n
- custom invoice per OU\n
- custom credit control per company, including invoices in appendix\n
- open invoice status, showing latest status per open invoice for manual follow up\n
- reverse billing logo\n
- zip and street number in partner tree list to support customer search by zip and house number\n
- default credit management policy for new partners, according company default\n
- zip format checking\n
  As this is made for BDU in NL the standard zip format is r'^[1-9]{1}[0-9]{3}[A-Z]{2}$'
  The format is checked when country is empty or equal to the default_country configuration parameter.
  The ZIP format can be changed by defining the default_zip_format configuration parameter.
  Hence for use in other countries both of these configuration parameters must be defined.
    """,
    'author'  : 'Magnus - Willem Hulshof, D. Prosee',
    'website' : 'http://www.magnus.nl',
    'depends' : ['account', 'sale_advertising_order', 'account_bank_statement_import_camt',
                 'partner_contact_gender','purchase', 'account_invoice_refund_link',
                 'partner_sector','base_partner_sequence','account_credit_control',
                 'account_analytic_required', 'account_type_inactive', 'account_type_menu',
                 'account_type_multi_company'
    ],
    'data' : [
            "security/ir.model.access.csv",
            "data/partner_sequence.xml",
            "data/operating_unit.xml",
            "data/mail_template_data.xml",
            "report/report_invoice.xml",
            "report/report_saleorder.xml",
            "report/purchase_quotation_templates.xml",
            "report/purchase_order_templates.xml",
            "report/report_deliveryslip.xml",
            "report/report_credit_control_summary.xml",
            "report/report.xml",
            "views/account_invoice_view.xml",
            "views/operating_unit_view.xml",
            "views/res_partner_view.xml",
            "views/product_view.xml",
            "views/company_view.xml",
            "views/open_invoice_status_view.xml",
            "wizard/account_invoice_state_view.xml",
            "views/sql_export_view.xml",
    ],
    'demo' : [],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

