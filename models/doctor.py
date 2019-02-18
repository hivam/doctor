# -*- coding: utf-8 -*-
# #############################################################################
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
#from odoo import pooler
from datetime import date, datetime, timedelta
#from odoo.osv import fields, osv
from odoo import models, fields, api
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from pytz import timezone
import pytz
from lxml import etree
import logging
_logger = logging.getLogger(__name__)

#~ import logging
from dateutil import parser
from dateutil import rrule
from dateutil.relativedelta import relativedelta
import time
import re
import math

from odoo import SUPERUSER_ID, tools
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

#from . import sale
#import addons.doctor.doctor_person
#import addons.doctor.doctor_appointment
#import addons.doctor.doctor_attentions
#import addons.doctor.doctor_invoice
#import addons.doctor.doctor_sales_order
#import addons.doctor.doctor_data
from odoo import netsvc


class doctor_schedule(models.Model):
    """Schedule"""
    _name = 'doctor.schedule'
    _description = "Scheduling doctor office hours"
    _order = 'date_begin asc'
    _rec_name = 'professional_id'


    def _date_to_dateuser(self, cr, uid, ids, date_begin):
        date_begin_user = datetime.strptime(date_begin, "%Y-%m-%d %H:%M:%S")

        user = self.pool.get('res.users').browse(cr, uid, uid)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        date_begin_user = pytz.utc.localize(date_begin_user).astimezone(tz)

        date_begin_user = datetime.strftime(date_begin_user, "%d-%m-%Y %H:%M")
        return date_begin_user

    def _date_end_to_dateuser(self, cr, uid, ids, date_end):
        date_end_user = datetime.strptime(date_end, "%Y-%m-%d %H:%M:%S")

        user = self.pool.get('res.users').browse(cr, uid, uid)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        date_end_user = pytz.utc.localize(date_end_user).astimezone(tz)

        date_end_user = datetime.strftime(date_end_user, "%H:%M")
        return date_end_user

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            date_begin = record.date_begin
            date_end = record.date_end
            display_name = record.professional_id['firtsname'] +' '+ record.professional_id['lastname'] + ' (' + self._date_to_dateuser(cr, uid, ids,
                                    date_begin) + ' - ' + self._date_end_to_dateuser( cr, uid, ids, date_end) + ')'
            res.append((record['id'], display_name))
        return res

    def _get_register(self, cr, uid, ids, fields, args, context=None):
        """Get Confirm or uncofirm register value.
        @param ids: List of Event registration type's id
        @param fields: List of function fields(register_current and register_prospect).
        @param context: A standard dictionary for contextual values
        @return: Dictionary of function fields value.
        """
        res = {}
        for schedule in self.browse(cr, uid, ids, context=context):
            res[schedule.id] = {}
            reg_open = 0
            for appointment in schedule.appointment_ids:
                if appointment.state != 'cancel':
                    reg_open += appointment.nb_register
            for field in fields:
                number = 0
                if field == 'patients_count':
                    number = reg_open
                res[schedule.id][field] = number
        return res

    professional_id = fields.Many2one('doctor.professional', 'Doctor')
    date_begin = fields.Datetime('Start date', required=True)
    schedule_duration = fields.Float('Duration (in hours)', required=True)
    date_end = fields.Datetime('End date', required=True)
    patients_count = fields.Char(compute='_get_register', string='Number of patients', multi='register_numbers')
    appointment_ids = fields.One2many('doctor.appointment', 'schedule_id', 'Appointments',
                                       domain=[('state', '!=', 'cancel'), ('cita_eliminada', '!=', True)])

    """
    _defaults = {
        'professional_id': _get_professional_id if _get_professional_id != False else False,
    }
    """

    def _check_schedule(self, cr, uid, ids):
        for record in self.browse(cr, uid, ids):
            schedule_ids = self.search(cr, uid,
                                       [('date_begin', '<', record.date_end), ('date_end', '>', record.date_begin),
                                        ('id', '<>', record.id)])
            if schedule_ids:
                return False
        return True

    def _check_date_begin(self, cr, uid, ids):
        for record in self.browse(cr, uid, ids):
            date_today = datetime.today()
            date_begin = record.date_begin
            date_begin = datetime.strptime(date_begin, "%Y-%m-%d %H:%M:%S")
            if date_begin < date_today:
                return False
        return True

    def _check_closing_time(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.date_end < record.date_begin:
                return False
        return True

    """
    _constraints = [
        (_check_closing_time, 'Error ! Closing Time cannot be set before Beginning Time.', ['date_end']),
        (_check_schedule, 'Error ! The Office Doctor is busy.', ['date_begin', 'date_end']),
        (_check_date_begin, 'Error ! Can not create a schedule for a date before the current.', ['date_begin']),
    ]
    """

    def onchange_start_date(self, cr, uid, ids, date_begin, schedule_duration, date_end, context={}):
        values = {}
        res = {}
        if not date_begin and not date_end:
            return res
        schedule_begin = datetime.strptime(date_begin, "%Y-%m-%d %H:%M:%S")
        duration = schedule_duration
        date_end = schedule_begin + timedelta(hours=duration)
        values.update({
            'date_end': date_end.strftime("%Y-%m-%d %H:%M:%S"),
        })
        return {'value': values}

    def _get_professional_id(self, cr, uid, user_id):
        doctor = self.pool.get('doctor.professional').search(cr, uid, [('user_id', '=', uid)])
        if doctor:
            return self.pool.get('doctor.professional').browse(cr, uid, doctor)[0].id
        return False







doctor_schedule()


class doctor_diseases(models.Model):
    _name = "doctor.diseases"

    code = fields.Char('Code', size=4, required=True),
    name = fields.Char('Disease', size=256, required=True),


    _sql_constraints = [('code_uniq', 'unique (code)', 'The Medical Diseases code must be unique')]

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name', 'code'], context)
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
        odontologia = context.get('odontologia')

        if name:
            ids = self.search(cr, uid, [('code', 'ilike', name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        elif odontologia:
            ids = self.search(cr, uid, [('code','>=','k000'),('code','<=','K149')], limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)


doctor_diseases()


class doctor_systems_category(models.Model):
    def name_get(self, cr, uid, ids, context=None):
        """Return the categories' display name, including their direct
           parent by default.

        :param dict context: the ``systems_category_display`` key can be
                             used to select the short version of the
                             category name (without the direct parent),
                             when set to ``'short'``. The default is
                             the long version."""
        if context is None:
            context = {}
        if context.get('systems_category_display') == 'short':
            return super(doctor_systems_category, self).name_get(cr, uid, ids, context=context)
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1] + ' / ' + name
            res.append((record['id'], name))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)


    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _description = 'Review systems categories'
    _name = 'doctor.systems.category'

    name = fields.Char('Category Name', required=True, size=64, translate=True)
    parent_id = fields.Many2one('doctor.systems.category', 'Parent Category', select=True, ondelete='cascade')
    complete_name = fields.Char(compute='_name_get_fnc', type="char", string='Full Name')
    child_ids = fields.One2many('doctor.systems.category', 'parent_id', 'Child Categories')
    active = fields.Boolean('Active',
                             help="The active field allows you to hide the category without removing it.",
                            default=1)
    parent_left = fields.Integer('Left parent', select=True)
    parent_right = fields.Integer('Right parent', select=True)


    """
    _constraints = [
        (models.Model._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]
    
    """
    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'


doctor_systems_category()


class doctor_review_systems(models.Model):
    _name = "doctor.review.systems"
    _rec_name = 'attentiont_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention'),
    system_category = fields.Many2one('doctor.systems.category', 'Systems category', required=True,
                                       ondelete='restrict'),
    review_systems = fields.Text('Review systems', required=True),


    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'attentiont_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res


doctor_review_systems()


class doctor_past_category(models.Model):
    def name_get(self, cr, uid, ids, context=None):
        """Return the categories' display name, including their direct
           parent by default.

        :param dict context: the ``past_category_display`` key can be
                             used to select the short version of the
                             category name (without the direct parent),
                             when set to ``'short'``. The default is
                             the long version."""
        if context is None:
            context = {}
        if context.get('past_category_display') == 'short':
            return super(doctor_past_category, self).name_get(cr, uid, ids, context=context)
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1] + ' / ' + name
            res.append((record['id'], name))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)


    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _description = 'Past categories'
    _name = 'doctor.past.category'

    name = fields.Char('Category Name', required=True, size=64, translate=True)
    parent_id = fields.Many2one('doctor.past.category', 'Parent Category', select=True, ondelete='cascade')
    complete_name = fields.Char(compute='_name_get_fnc', type="char", string='Full Name')
    child_ids = fields.One2many('doctor.past.category', 'parent_id', 'Child Categories')
    active = fields.Boolean('Active',
                             help="The active field allows you to hide the category without removing it.",
                            default=1)
    parent_left = fields.Integer('Left parent', select=True)
    parent_right = fields.Integer('Right parent', select=True)


    """
    _constraints = [
        (models.Model._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]
    """

    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'


doctor_past_category()


class doctor_diseases_past(models.Model):
    _name = "doctor.diseases.past"
    _rec_name = 'attentiont_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention', ondelete='restrict')
    patient_id = fields.Many2one('doctor.patient', 'Patient', required=True, ondelete='restrict')
    diseases_id = fields.Many2one('doctor.diseases', 'Past diseases', required=True, ondelete='restrict')


    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'attentiont_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

    _defaults = {
        'patient_id': lambda self, cr, uid, context: context.get('patient_id', False),
    }


doctor_diseases_past()


class doctor_atc_past(models.Model):
    _name = "doctor.atc.past"
    _rec_name = 'attentiont_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention', ondelete='restrict')
    patient_id = fields.Many2one('doctor.patient', 'Patient', required=True, ondelete='restrict')
    atc_id = fields.Many2one('doctor.atc', 'Past drugs', required=True, ondelete='restrict')

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'attentiont_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

    _defaults = {
        'patient_id': lambda self, cr, uid, context: context.get('patient_id', False),
    }


doctor_atc_past()


class doctor_exam_category(models.Model):
    def name_get(self, cr, uid, ids, context=None):
        """Return the categories' display name, including their direct
           parent by default.

        :param dict context: the ``exam_category_display`` key can be
                             used to select the short version of the
                             category name (without the direct parent),
                             when set to ``'short'``. The default is
                             the long version."""
        if context is None:
            context = {}
        if context.get('exam_category_display') == 'short':
            return super(doctor_exam_category, self).name_get(cr, uid, ids, context=context)
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1] + ' / ' + name
            res.append((record['id'], name))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)


    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _description = 'Exam categories'
    _name = 'doctor.exam.category'

    name = fields.Char('Category Name', required=True, size=64, translate=True)
    parent_id = fields.Many2one('doctor.exam.category', 'Parent Category', select=True, ondelete='cascade')
    complete_name = fields.Char(compute='_name_get_fnc', type="char", string='Full Name')
    child_ids = fields.One2many('doctor.exam.category', 'parent_id', 'Child Categories')
    active = fields.Boolean('Active',
                             help="The active field allows you to hide the category without removing it.",
                            default=1)
    parent_left = fields.Integer('Left parent', select=True)
    parent_right = fields.Integer('Right parent', select=True)

    """
    _constraints = [
        (models.Model._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]
    """


    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'


doctor_exam_category()


class doctor_health_procedures(models.Model):
    _inherit = "product.product"

    def onchange_type(self, cr, uid, ids, type):
        if not type:
            return {}
        else:
            if type != 'service':
                return {'value': {
                    'health_procedure': False,
                }
                }

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []

        def _name_get(d):
            name = d.get('name', '')
            code = d.get('default_code', False)
            if code:
                name = '%s' % (code)
            return (d['id'], name)

        partner_id = context.get('partner_id', False)

        result = []
        for product in self.browse(cr, user, ids, context=context):
            sellers = filter(lambda x: x.name.id == partner_id, product.seller_ids)
            if sellers:
                for s in sellers:
                    mydict = {
                        'id': product.id,
                        'name': s.product_name or product.name,
                        'default_code': s.product_code or product.default_code,
                        'variants': product.variants
                    }
                    result.append(_name_get(mydict))
            else:
                mydict = {
                    'id': product.id,
                    'name': product.name,
                    'default_code': product.default_code,
                    'variants': product.variants
                }
                result.append(_name_get(mydict))
        return result

    is_health_procedure = fields.Boolean('Is Health Procedure?')
    procedure_code = fields.Char('Code', size=16)
    procedure_description = fields.Char('Description', size=256)
    complexity_level = fields.Selection([('1', '1'), ('2', '2'), ('3', '3')], 'Complexity Level')
    procedure_type = fields.Selection([('1', 'Consultation'), ('2', 'Surgical Procedure'),
                                        ('3', 'Diagnostic Image'), ('4', 'Clinical laboratory'),
                                        ('5', 'Therapeutic Procedure'), ('6', 'Hospitalization'),
                                        ('7', 'Odontological'), ('8', 'Other')], 'Procedure Type')
    professional_ids = fields.Many2many('doctor.professional', id1='procedures_ids', id2='professional_ids',
                                         string='My health procedures', required=False, ondelete='restrict')


doctor_health_procedures()


class doctor_prescription(models.Model):
    _name = "doctor.prescription"
    _rec_name = 'drugs_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention')
    drugs_id = fields.Many2one('doctor.drugs', 'Drug', required=True, ondelete='restrict')
    total_quantity = fields.Integer('Total quantity', required=True)
    measuring_unit_qt = fields.Many2one('doctor.measuring.unit', 'Drug measuring unit', required=True,
                                         ondelete='restrict')
    action_id = fields.Selection([
        ('take', 'Take'),
        ('inject', 'Inject'),
        ('apply', 'Apply'),
        ('inhale', 'Inhale'),
    ], 'Action', required=True, default='take')
    quantity = fields.Integer('Quantity', required=True)
    measuring_unit_q = fields.Many2one('doctor.measuring.unit', 'Drug measuring unit', required=True,
                                        ondelete='restrict')
    frequency = fields.Integer('Frequency (each)', required=True)
    frequency_unit_n = fields.Selection([
        ('minutes', 'minutes'),
        ('hours', 'hours'),
        ('days', 'days'),
        ('weeks', 'weeks'),
        ('wr', 'when required'),
        ('total', 'total'),
    ], 'Frequency unit', required=True, default='hours')
    duration = fields.Integer('Treatment duration', required=True)
    duration_period_n = fields.Selection([
        ('minutes', 'minutes'),
        ('hours', 'hours'),
        ('days', 'days'),
        ('months', 'months'),
        ('indefinite', 'indefinite'),
    ], 'Treatment period', required=True, default='days')
    administration_route_id = fields.Many2one('doctor.administration.route', 'Administration route', required=True,
                                               ondelete='restrict')
    dose = fields.Integer('Dose', required=True)
    dose_unit_id = fields.Many2one('doctor.dose.unit', 'Dose unit', required=True, ondelete='restrict')
    indications = fields.Text('Indications')


    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'drugs_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res


doctor_prescription()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
