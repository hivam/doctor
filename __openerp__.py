# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name' : 'Doctor',
    'version' : '1.0',
    'summary': 'Electronics Health Record in the Office Doctor',
    'description': """
This module allows
=================================================================

""",
    'category' : 'Specific Industry Applications',
    'author' : 'TIX SAS',
    'website': 'http://www.tix.com.co',
    'license': 'AGPL-3',
    'depends' : ['base','product','sale'],            
    'data' : ['security/doctor_security.xml',
              'security/ir.model.access.csv',
              'doctor_sequence.xml',
              'doctor_view.xml',
              ],
    'css': ['static/src/css/doctor.css'],
    "js": [
        "static/src/js/search.js",
    ],
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
