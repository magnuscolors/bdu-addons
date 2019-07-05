# -*- encoding: utf-8 -*-
{
    'name'       : 'BDU Dashboards',
    'version'    : '10.0',
    'category'   : 'Reporting',
    'summary'    : 'Create shared dashboard',
    'description': """
This module adds team dashboards.\n
Team dashboards contain content that may be shared amongst teams.\n
MIS builder users may add to team dashboards.\n
Since team dashboards belong to admin, only admin can change the layout (column) of the team dashboard.
Note: any update will make a new board, hence custom views might be lost
    """,
    'author'     : 'D. Prosee',
    'website'    : 'http://www.bdu.nl',
    'depends'    : ['board',
                    'mis_builder', 
                   ],
    'data'       : [
                    "security/security.xml",
                    "views/dashboard.xml",
                  ],
    'installable': True
}

