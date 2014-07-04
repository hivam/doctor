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

class doctor_speciality (osv.osv):
    _name = "doctor.speciality"
    _columns = {
        'code' : fields.char ('Code', size=3, required=True),
        'name' :fields.char ('Speciality', size=64, required=True),
        }

    _sql_constraints = [('code_uniq', 'unique (code)', 'The Medical Speciality code must be unique')]

doctor_speciality ()

class doctor_insurer(osv.osv):
    _name = "doctor.insurer"
    _rec_name = 'insurer'
    _columns = {
        'insurer' :fields.many2one ('res.partner','Insurer', help='Insurer'),
        'code' : fields.char ('Code', size=6, required=True),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'insurer'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

    _sql_constraints = [('code_uniq', 'unique (code)', 'The insurer code must be unique')]

doctor_insurer()

class doctor_pharmaceutical_form (osv.osv):
    _name = "doctor.pharmaceutical.form"
    _columns = {
        'code' : fields.char ('Code', size=10, required=True),
        'name' :fields.char ('Pharmaceutical form', size=128, required=True),
        }

    _sql_constraints = [('code_uniq', 'unique (code)', 'The Pharmaceutical Form code must be unique')]

doctor_pharmaceutical_form ()

class doctor_dose_unit (osv.osv):
    _name = "doctor.dose.unit"
    _columns = {
        'code' : fields.char ('Abbreviation', size=10, required=True),
        'name' :fields.char ('Dosage unit', size=128, required=True),
        }

    _sql_constraints = [('code_uniq', 'unique (code)', 'The Dose code must be unique')]

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','code'], context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            res.append((record['id'], name))
        return res

doctor_dose_unit ()

class doctor_administration_route (osv.osv):
    _name = "doctor.administration.route"
    _columns = {
        'code' : fields.char ('Code', size=10, required=True),
        'name' :fields.char ('Administration route', size=128, required=True),
        }

    _sql_constraints = [('code_uniq', 'unique (code)', 'The Administration Route code must be unique')]

doctor_administration_route ()

class doctor_measuring_unit (osv.osv):
    _name = "doctor.measuring.unit"
    _columns = {
        'code' : fields.char ('Code', size=10, required=True),
        'name' :fields.char ('Measuring unit', size=128, required=True),
        }

    _sql_constraints = [('code_uniq', 'unique (code)', 'The Measuring unit code must be unique')]

doctor_measuring_unit ()

class doctor_drugs (osv.osv):
    _name = "doctor.drugs"
    _rec_name = 'atc_id'
    _columns = {
        'code' : fields.char ('Code', size=10, required=True),
        'atc_id' : fields.many2one ('doctor.atc', 'ATC', required=True, ondelete='restrict'),
        'pharmaceutical_form' : fields.many2one ('doctor.pharmaceutical.form', 'Pharmaceutical form', required=True, ondelete='restrict'),
        'drugs_concentration' : fields.char ('Drugs concentration', size=64, required=True),
        'administration_route' : fields.many2one ('doctor.administration.route', 'Administration route', required=True, ondelete='restrict'),
    }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['atc_id','pharmaceutical_form','drugs_concentration', 'administration_route'], context)
        res = []
        for record in reads:
            name = record['atc_id'][1]
            if record['pharmaceutical_form'] and record['drugs_concentration'] and record['administration_route']:
                name = name + ' (' + record['drugs_concentration'] + ' - ' + record['pharmaceutical_form'][1] + ' - ' + record['administration_route'][1] + ')'
            res.append((record['id'], name))
        return res

doctor_drugs ()

class doctor_atc (osv.osv):
    _name = "doctor.atc"
    _columns = {
        'code' : fields.char ('Code', size=7, required=True),
        'name' :fields.char ('Description', size=512, required=True),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','code'], context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            res.append((record['id'], name))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        args = args or []
        ids = []
        if name:
            ids = self.search(cr, uid, [('code', 'ilike', name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

doctor_atc ()
