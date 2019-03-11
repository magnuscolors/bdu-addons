# -*- coding: utf-8 -*-
{
    'name': "BDU product recruitment",

    'summary': """
        Order enhancements for product category Recruitment
                """,

    'description': """
        Product Recruitment include:\n
        - custom handling on orderline form\n
        Usage:\n
        - enhance products within custom handling \'Recruitment\' , found on product tab \'Sale\'\n
        - or organize products under an enhanced product category with aforementioned custom handling \n
        - the custom handling on the product (template) takes precedence over the one mentioned in the product category\n
        - custom fields will show on orderline after selection of product
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.magnus.nl",
    'license' : "LGPL-3", 
    'category': 'sale',
    'version' : '10.0',
    'depends' : [
                 'bdu_product_base', 
                 'bdu_product_online', #list of websites
                 'sale', 
                ],
    'data'    : [
                'security/security.xml',
                'security/ir.model.access.csv',
                'data/recruit_employment_type.xml',
                'data/recruit_function_group.xml',
                'data/recruit_education_level.xml',
                'data/recruit_industry.xml',
                 'views/orderline_adaptions.xml',
                ],
    'demo'    : [
                ],
}