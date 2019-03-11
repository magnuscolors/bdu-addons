# -*- coding: utf-8 -*-
{
    'name': "BDU Recruitment online",

    'summary': """
        Sends orderlines for recruitment announcements to the websites of BDU. 
                """,

    'description': """
        This module caters for a manual and batch shipment of recruitment announcement to BDU's online vacancies database.
        Orderlines for products with customized orderline handling "Recruitment" will be shipped together with meta tags (job title, job description, education level, etc.).
        A product count of 0 is used to signal the deletion of the record to the API.
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 

    'category': 'Connector',
    'version': '10.0',

    # depends on mis_builder to find menu location (see views)
    'depends': [
                'sale_advertising_order',     #to convert title name into analytic account 
                'bdu_product_recruitment',    #addresses the custom fields added to the orderline for recruitments
               ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/recruitment_config.xml',
    ],
}