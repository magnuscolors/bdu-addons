# -*- coding: utf-8 -*-
{
    'name': "BDU Classifieds Online",

    'summary': """
        Sends classified orders to the websites of BDU. 
                """,

    'description': """
        This module provides a manual and batch facility for shipment of classified orders, currently known as "Regiotreffers" to BDU's website.
        Classified order are selected by the configured ad class and will be shipped as text based on the original order; hence the depends on wave2 module.
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 

    'category': 'Connector',
    'version': '10.0',

    # depends on mis_builder to find menu location (see views)
    'depends': [
                'sale_advertising_order',     #ad class et al.
                'bdu_wave2',                  #original order that holds the text
               ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/classifieds_online_menu.xml',
        'views/classifieds_online_config.xml',
        'views/classifieds_online_mapping.xml',
    ]
}