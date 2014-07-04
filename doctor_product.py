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
import time
import pooler
from datetime import date, datetime, timedelta
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from pytz import timezone
import pytz

#~ import logging
from dateutil import parser
from dateutil import rrule
from dateutil.relativedelta import relativedelta
import time
import re
import math

from openerp import SUPERUSER_ID, tools
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

import sale
import doctor
import doctor_person
import doctor_appointment
import doctor_attentions
import doctor_invoice
import netsvc

class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
        'name': fields.char('Name', size=128, required=True, translate=False, select=True),
        'standard_price': fields.float('Cost', digits_compute=dp.get_precision('Product Price'), help="Cost price of the product used for standard stock valuation in accounting and used as a base price on purchase orders.", groups="base.group_user,doctor.group_doctor_configuration"),
    }

product_template()