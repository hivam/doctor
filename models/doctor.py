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

    """
    @api.multi
    def name_get(self):
        if not self._ids:
            return []
        if isinstance(self._ids, (long, int)):
            ids = [self._ids]
        res = []
        for record in self.browse(self._ids):
            date_begin = record.date_begin
            date_end = record.date_end
            display_name = record.professional_id['firtsname'] +' '+ record.professional_id['lastname'] + ' (' + self._date_to_dateuser(cr, uid, ids,
                                    date_begin) + ' - ' + self._date_end_to_dateuser( cr, uid, ids, date_end) + ')'
            res.append((record['id'], display_name))
        return res
    """

    @api.one
    def _get_register(self):
        """Get Confirm or uncofirm register value.
        @param ids: List of Event registration type's id
        @param fields: List of function fields(register_current and register_prospect).
        @param context: A standard dictionary for contextual values
        @return: Dictionary of function fields value.
        """
        _logger.info('entro a get')
        _logger.info('entro a get')
        _logger.info('entro a get')
        _logger.info(self._ids)

        res = {}
        for schedule in self.browse(self._ids):
            res[schedule.id] = {}
            reg_open = 0
            for appointment in schedule.appointment_ids:
                _logger.info('entro a get')
                _logger.info('entro a get')
                _logger.info(appointment.state)
                if appointment.state != 'cancel':
                    reg_open += appointment.nb_register
            for field in self._fields:
                number = 0
                if field == 'patients_count':
                    number = reg_open
                res[schedule.id][field] = number
        self.patients_count = res

    professional_id = fields.Many2one('doctor.professional', 'Doctor',default= lambda self: self._get_professional_id())
    date_begin = fields.Datetime('Start date', required=True)
    schedule_duration = fields.Float('Duration (in hours)', required=True)
    date_end = fields.Datetime('End date', required=True)
    patients_count = fields.Float(compute='_get_register', string='Number of patients', store=True)
    appointment_ids = fields.One2many('doctor.appointment', 'schedule_id', 'Appointments',
                                      domain=[('state', '!=', 'cancel')])

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


    @api.onchange('date_begin','schedule_duration','date_end')
    def onchange_start_date(self):
        values = {}
        res = {}
        if not self.date_begin and not self.date_end:
            return res
        schedule_begin = datetime.strptime(self.date_begin, "%Y-%m-%d %H:%M:%S")
        duration = self.schedule_duration
        date_end = schedule_begin + timedelta(hours=duration)
        values.update({
            'date_end': date_end.strftime("%Y-%m-%d %H:%M:%S"),
        })
        return {'value': values}

    @api.model
    def _get_professional_id(self):
        doctor = self.env['doctor.professional'].search([('user_id', '=', self._uid)])

        return doctor







doctor_schedule()






class doctor_diseases_past(models.Model):
    _name = "doctor.diseases.past"
    _rec_name = 'attentiont_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention', ondelete='restrict')
    patient_id = fields.Many2one('doctor.patient', 'Patient', required=True, ondelete='restrict')
    diseases_id = fields.Many2one('doctor.diseases', 'Past diseases', required=True, ondelete='restrict')

    """
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'attentiont_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res
    """



doctor_diseases_past()


class doctor_atc_past(models.Model):
    _name = "doctor.atc.past"
    _rec_name = 'attentiont_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention', ondelete='restrict')
    patient_id = fields.Many2one('doctor.patient', 'Patient', required=True, ondelete='restrict')
    atc_id = fields.Many2one('doctor.atc', 'Past drugs', required=True, ondelete='restrict')

    """
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
    """

doctor_atc_past()





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
