# -*- coding: utf-8 -*-
{
    'name': "BDU Wave2",

    'summary': """
        Collect orders from Wave2""",

    'description': """
        Wave2 orders are collected from the configured FTP site, processed and marked as done by transfering them to the done directory.\n
        Customers are identified by their email address. Double or missing email addresses results in an order skipped and an error logged. \n
        Order reference is kept in the order and orderline external reference field, with a configurable prefix.\n
        \n
        This module also caters for region to title administration, classified classes and an alternative date configuration.\n
        \n
        Total price per order is maintained, based on total price and number of titles per order (i.e. region). \n
        Should calculation give a remainder (e.g. 3 orderlines for 10 euro), then the last orderline closes the balance.\n
        \n
        Because Wave2 only knows of weekdays, this connector transfers specific issues to other calendar dates if defined in the alternative date configuration.\n
        Reruns will result in an update, so be carefull since there is no check on deadline, issue_date or invoices made (all orders accepted)
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Connector',
    'version': '10.0',

    # depends on module sale to find menu location (see views)
    # m.m. res.partner attribute sector_id requires module partner_sector
    # m.m. res.partner attribute is_ad_agency requires module bdu_account
    # m.m. res.partner attribute promille_id requires module sale_advertising_order (already required by bdu_account)
    # NB since bdu_account needs product.template attribute booklet_surface_area, but without depends, module wobe_imports is also needed
    'depends': ['base', 'sale',  'partner_sector', 'wobe_imports', 'bdu_account'],

    # always loaded
    'data': [
            'security/security.xml',
            'security/ir.model.access.csv',
            'views/wave2_menu.xml',
            'views/wave2_class.xml',
            'views/wave2_config.xml',
            'views/wave2_order.xml',
            'views/wave2_alternative_dates.xml',
            'views/wave2_region.xml',
            'views/wave2_region_titles.xml',
            'data/wave2_class.xml',
            'data/wave2_region.xml',
            ],
    # only loaded in demonstration mode
    #'demo': [
    #   'demo/config.xml',
    #],
}