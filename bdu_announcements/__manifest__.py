# -*- coding: utf-8 -*-
{
    'name': "BDU Announcements",

    'summary': """
        Sends orderlines for family announcements to the websites of BDU. 
                """,

    'description': """
        BDU Announcements provides a manual and batch facility for shipment of family announcement to BDU's online announcement database.
        Orderlines with defined ad class products will be shipped together with meta tags (firstname, lastname, city, publications) as well as the web domain and from/to date.
        The material link should point to a PDF file holding the announcement as published in the newspaper editions. A product count of 0 will delete the entry from the announcement database.
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Connector',
    'version': '10.0',

    # depends on mis_builder to find menu location (see views)
    'depends': [
                'sale_advertising_order',     #to convert title name into analytic account 
               ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/announcement_config.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}