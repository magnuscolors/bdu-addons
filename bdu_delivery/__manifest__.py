# -*- coding: utf-8 -*-
{
    'name': "BDU deliveries",

    'summary': """
        Distribution lists for magazines and newspaper distributors.\n
                """,

    'description': """
        Ships a delivery list to distributors based on selected title(s), delivery type(s), file format and communication path(s).\n
        Manual shipment is based on the selected date, i.e. issue date.\n 
         \n
        Automated shipment:\n
        - can be done by calling the automated_run method of the delivery.config object. \n
        - needs an obligatory configuration name in the form ("name",) in the arguments field of the scheduled action.\n
        - uses system date plus the configured lead time in days to calculte the issue date.\n
         \n
        (Delivery) titles, delivery list and delivery lines are generated or updated.\n
        Be aware that already prepared delivery lines will not be deleted when deleted afterwards in the subscription order.\n
        Delivery lists are named after the sent files. Sent files become attachments to the config too.
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 
    'category': 'Connector',
    'version' : '10.0',
    'depends' : [
                  'publishing_subscription_order', #delivery_type (should be carrier_id) and delivery tables
                  'bdu_account',   #insert after zeno-, pubble- and exact-id's
                  'subscription_baarn', #wijknummer, should be temporary,...but what is ..:-(
                  #'inventory', #for carrier_id, i.e. delivery method (provides way to add costs)
                ],
    'data'    : [
                 'security/security.xml',
                 'security/ir.model.access.csv',
                 'views/delivery_config.xml',
                 'views/remove_generate_buttons.xml'
                ],
    'qweb'    : [
                  'static/src/xml/qweb.xml',
                ],
}