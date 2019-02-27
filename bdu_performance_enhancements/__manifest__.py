# -*- coding: utf-8 -*-
{
    'name': "BDU performance enhancements",

    'summary': """
        Several interventions to improve user experience
        """,

    'description': """
        
    """,

    'author': "D. Prosee",
    'website': "http://www.bdu.nl",

    'category': 'Uncategorized',
    'version': '10.0',

    # any module necessary for this one to work correctly
    'depends': [
                'base', 
                'contacts',
                ],

    # always loaded
    'data': [
        'views/contacts.xml',
        'views/standard_sales_customer.xml',
        'views/finance_customer.xml',
        'views/finance_supplier.xml',
    ],

}