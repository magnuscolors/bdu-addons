# -*- coding: utf-8 -*-
{
    'name': "BDU product distribution",

    'summary': """
        Order enhancements for product category distribution
                """,

    'description': """
        Product distribution enhancements include:\n
        - valid distribution addresses, linked to titles and distributors\n
        - custom handling on orderline form\n
        - selected area(s) and distributor added to sale orderline\n
        - quantity ordered calculated on logistics table, divided by 1000\n
        - appendices for customer with distribution details\n
        - order details per distributor (not administered)\n\n
        Usage:\n
        - define products within custom handling \'Distribution\' , found on product tab \'Sale\'\n
        - or organize products under a product category with mentioned custom handling \n
        - the custom handling on the product (template) takes precedence over the one mentioned in the product category\n
        - custom fields will show on orderline after selection of product
    """,

    'author'  : "Magnus - Willem Hulshof and BDU - D. Prosee",
    'website' : "http://www.magnus.nl",
    'license' : "LGPL-3", 
    'category': 'sale',
    'version' : '10.0',
    'depends' : [
                 'bdu_product_base', 'sale', 
                ],
    'data'    : [
                 'reports/appendix_distribution.xml',
                 'reports/list_for_distributors.xml',
                 'views/orderline_adaptions.xml',
                 'views/distribution.xml'
                 'views/logistics_addres_table_view.xml',
                 'security/security.xml',
                 'security/ir.model.access.csv',
                ],
    'demo'    : [
                ],
}