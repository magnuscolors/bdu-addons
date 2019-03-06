# -*- encoding: utf-8 -*-
##############################################################################
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs.
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company like Veritos.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
##############################################################################

{
    'name'       : 'BDU advertising sales',
    'version'    : '10.0.1.1.0',
    'category'   : 'sale',
    'description': """
BDU specific modifications:

a) filters and grouping in sale advertising: complete replacement of standard set\n
b) title grouping by primary salesteam added to facilitate filtering based on titles\n
c) future edition filter on issues\n
d) additional selection "Exception" for invoicing frequency\n
e) batch invoicing with parsed date arguments\n

Barch invoicing uses an argument in the form : ([domain filter],invoice_date,)\n
Date arguments in filters and invoice date may either be a date or a date keyword like :
- nearest_tuesday
- first_this_month (monday afterwards if a sunday)
- last_day_previous_month (saturday before if a sunday)
- today
- yesterday
- day_before_yesterday
- last_sunday
\n\n
Filters are a.o. based on sales teams to circumvent additional administration\n
Note that by using sales teams only direct sales teams should be used (i.e. one channel)\n
Note that results from title based filtering may differ from salesteam filter as salesperson might sell titles belonging to other teams. 


    """,
    'author'  	 : 'D. Prosee',
    'website' 	 : 'http://www.bdu.nl',
    'depends' 	 : [
    				'sale_advertising_order',
                    'orderline_invoicing_frequency',           
    			   ],
    'data'    	 : [
		            "data/mail_template_data.xml",
		            "views/sale_advertising_order_line_filter_view.xml",
                    "views/sale_advertising_issue_form_view.xml",
                    "views/orderline_issue_filter.xml",
    			   ],
    'demo'    	 : [
    			   ],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

