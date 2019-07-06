# -*- coding: utf-8 -*-
{
    'name': "BDU paid digital subscriptions",

    'summary': """
        Sends list of subscribers and titles to website
                """,

    'description': """
        Almost all titles have a digital sibling. Some of them have a paywall and thus need to be aware of active subscriptions.\n
        This interface deducts this information from active orderlines and the titles with a paywall.\n
        Via the product template it is possible to define a suffix to the title to further distinguish between subscription rights.\n
        \n
        The communicated information contains an subscriber number, zip code, empty field and double quotes enclosed title-codes in a comma separate record style.\n
        Because the current website is unable to process more than 10k records at once, the complete list is hatched into multiple files.\n
        \n
        A realtime interface may be activated so when orderlines changes are directly communicated with the Drupal website.\n
        However, the batch interface is the only interface that keeps track of the sync status (by keeping track of the most recently synced orderline).\n
        So the batch interface should run frequently to circumvent any miscommunication when using the realtime API.\n
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 
    'category': 'Connector',
    'version' : '10.0',
    'depends' : [
                  'publishing_subscription_order',
                  'bdu_account',   #insert after zeno-, pubble- and exact-id's
                ],
    'data'    : [
                 'security/security.xml',
                 'security/ir.model.access.csv',
                 'views/digital_subscribers_config.xml',
                 'views/advertising_issue.xml',
                 'views/res_partner.xml',
                 'views/product.xml',
                ],
    'demo'    : [
                 #'demo/demo.xml',
                ],
}