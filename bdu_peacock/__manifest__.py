# -*- coding: utf-8 -*-
{
    'name': "BDU Peacock",

    'summary': """
        Sends movelines and account info
                """,

    'description': """
        BDU accountant Schuiteman / Peacock insights use periodic accounting info to monitor data quality.\n
        This interface collects and ships this information. \n
        The latest interface lets the user choose the basic method for acquiring the information, being either ORM search-read or SQL query.\n
        Shipping can be done manually using the Send-button above, or automatically via scheduled actions calling the automated_run method of the peacock.config object.
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 
    'category': 'Connector',
    'version' : '10.0',
    'depends' : ['account'
                ],
    'data'    : [
                 'security/security.xml',
                 'security/ir.model.access.csv',
                 'views/peacock_config.xml',
                ],
    'demo'    : [
                 #'demo/demo.xml',
                ],
}