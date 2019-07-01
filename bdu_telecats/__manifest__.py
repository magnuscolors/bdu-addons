# -*- coding: utf-8 -*-
{
    'name': "BDU Telecats",

    'summary': """
        Collect delivery complaints from Telecats (IVR) and Website forms""",

    'description': """
        Delivery complaints can be made by IVR (interactive voice response) and by filling a website form.\n
        Both methods result in an XML document containing amongst others the address, title, date and customer.\n
        This interface then collects and stores the XML files first so the may be adjusted in case of an error.\n
        Then the XML's are processed into service tickets (project issues), applying first line business rules and assigning the right responsible.\n
        The business rules encompass: \n
        - whether tickets should be processed for this title (to support migration and sale of titles)
        - assessing if delivery complaint is valid according edition, subscription and delivery address\n
        - computing the priority according recent history\n
        - acquiring the assignee based on the distribution list\n
        - assigning the default assignee if the above and/or xml do not cater for a clear answer.\n
        \n
        XML's may be fetched and processed manually or by configuring a scheduled task calling the automated_run method of the telecats.config module.\n
        The interface caters for two sources to collect data from. Names of these sources are taken from the project source.\n
        The result of the latest run is shown on the interface page.\n
        The interface may be run any time, over and over. When "Done dir active" is checked the XML files are moved to that directory on the host they came from.
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Connector',
    'version': '10.0',

    'depends': ['base', 
                'project',                      #tickets
                'sale',                         #menu placement 
                'bdu_product_distribution',     #distributor search 
                'sale_advertising_order',       #titles and editions 
                'publishing_subscription_order' #validity of subscription
                ],

    # always loaded
    'data': [
            'security/security.xml',
            'security/ir.model.access.csv',
            'views/telecats_menu.xml',
            'views/telecats_config.xml',
            'views/telecats_ticket.xml',
            'views/telecats_title.xml',
            #'data/telecats_title.xml',
            ],
    # only loaded in demonstration mode
    #'demo': [
    #   'demo/config.xml',
    #],
}