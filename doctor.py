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
import netsvc

class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
        'name': fields.char('Name', size=128, required=True, translate=False, select=True),
        'standard_price': fields.float('Cost', digits_compute=dp.get_precision('Product Price'), help="Cost price of the product used for standard stock valuation in accounting and used as a base price on purchase orders.", groups="base.group_user,doctor.group_doctor_configuration"),
    }

product_template()

class doctor_speciality (osv.osv):
    _name = "doctor.speciality"
    _columns = {
        'code' : fields.char ('Code', size=3, required=True),
        'name' :fields.char ('Speciality', size=64, required=True),
        }

    _sql_constraints = [('code_uniq', 'unique (code)', 'The Medical Speciality code must be unique')]

doctor_speciality ()

class doctor_professional (osv.osv):
    _name = "doctor.professional"
    _description = "Information about the healthcare professional"
    _rec_name = 'professional'
    _columns = {
        'professional' : fields.many2one ('res.partner','Healthcare Professional', required=True, ondelete='restrict', domain=[('is_company', '=', False)]),
        'photo' : fields.related ('professional', 'image_medium', type="binary", relation="res.partner", readonly= True),
        'speciality_id': fields.many2one ('doctor.speciality','Speciality', required=True),
        'professional_card' : fields.char('Professional card', size=64, required=True),
        'authority' : fields.char('Authority', size=64, required=True),
        'work_phone': fields.char('Work Phone', size=64),
        'work_mobile': fields.char('Work Mobile', size=64),
        'work_email': fields.char('Work Email', size=240),
        'user_id' : fields.many2one('res.users', 'User', help='Related user name', required=True, ondelete='restrict'),
        'active': fields.boolean('Active'),
        'procedures_ids' : fields.many2many('product.product', id1='professional_ids', id2='procedures_ids', string='My health procedures', required=False, ondelete='restrict'),
        }

    _defaults = {
        'active': lambda *a: 1,
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'professional'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

    def onchange_photo(self, cr, uid, ids, professional, photo, context=None):
        values = {}
        if not professional:
            return values
        professional_data = self.pool.get('res.partner').browse(cr, uid, professional, context=context)
        professional_img = professional_data.image_medium
        values.update({
            'photo' : professional_img,
        })
        return {'value' : values}

    def onchange_user(self, cr, uid, ids, user_id, context=None):
        work_email = False
        if user_id:
            work_email = self.pool.get('res.users').browse(cr, uid, user_id, context=context).email
        return {'value': {'work_email' : work_email}}

doctor_professional()

class doctor_patient (osv.osv):
    _name = "doctor.patient"
    _description = "Information about the patient"
    _rec_name = 'patient'

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        for patient in self.browse(cr, uid, ids, context=context):
            if 'birth_date' in vals:
                birth_date=vals['birth_date']
                current_date = time.strftime('%Y-%m-%d')
                if birth_date>current_date:
                    raise osv.except_osv(_('Warning !'), _("Birth Date Can not be a future date "))
        return super(doctor_patient, self).write(cr, uid, ids, vals, context=context)


    def create(self, cr, uid, vals, context=None):
        if 'birth_date' in vals:
                birth_date=vals['birth_date']
                current_date = time.strftime('%Y-%m-%d')
                if birth_date>current_date:
                    raise osv.except_osv(_('Warning !'), _("Birth Date Can not be a future date "))
        return super(doctor_patient, self).create(cr, uid, vals, context=context)

    _columns = {
        'patient' : fields.many2one ('res.partner','Patient', required=True, ondelete='restrict', domain=[('is_company', '=', False)]),
        'photo' : fields.related ('patient', 'image_medium', type="binary", relation="res.partner", readonly= True),
        'birth_date' : fields.date ('Date of Birth', required=True),
        'sex' : fields.selection([('m','Male'), ('f','Female'), ], 'Sex', select=True, required=True),
        'blood_type' : fields.selection([('A','A'), ('B','B'), ('AB','AB'), ('O','O'), ], 'Blood Type'),
        'rh' : fields.selection([('+','+'), ('-','-'), ], 'Rh'),
        'insurer' : fields.many2one('doctor.insurer', 'Insurer', required=False, help='Insurer'),
        'deceased' : fields.boolean ('Deceased', help="Mark if the patient has died"),
        'death_date' : fields.date ('Date of Death'),
        'death_cause' : fields.many2one ('doctor.diseases', 'Cause of Death'),
        'attentions_ids' : fields.one2many('doctor.attentions', 'patient_id', 'Attentions'),
        'appointments_ids' : fields.one2many('doctor.appointment', 'patient_id', 'Attentions'),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'patient'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

    def onchange_patient_data(self, cr, uid, ids, patient, photo, context=None):
        values = {}
        if not patient:
            return values
        patient_data = self.pool.get('res.partner').browse(cr, uid, patient, context=context)
        patient_img = patient_data.image_medium
        values.update({
            'photo' : patient_img,
        })
        return {'value' : values}

doctor_patient()

class doctor_schedule(osv.osv):
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
            display_name = record.professional_id.professional['name'] + ' (' + self._date_to_dateuser(cr, uid, ids, date_begin) + ' - ' + self._date_end_to_dateuser(cr, uid, ids, date_end) + ')'
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

    _columns = {
        'professional_id': fields.many2one ('doctor.professional','Doctor'),
        'date_begin': fields.datetime('Start date', required=True),
        'schedule_duration': fields.integer('Duration (in hours)', required=True),
        'date_end': fields.datetime('End date', required=True),
        'patients_count': fields.function(_get_register, string='Number of patients', multi='register_numbers'),
        'appointment_ids': fields.one2many('doctor.appointment', 'schedule_id', 'Appointments'),
        }

    def _check_schedule(self, cr, uid, ids):
        for record in self.browse(cr, uid, ids):
            schedule_ids = self.search(cr, uid, [('date_begin', '<', record.date_end), ('date_end', '>', record.date_begin), ('id', '<>', record.id)])
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

    _constraints = [
        (_check_closing_time, 'Error ! Closing Time cannot be set before Beginning Time.', ['date_end']),
        (_check_schedule, 'Error ! The Office Doctor is busy.', ['date_begin','date_end']),
        (_check_date_begin, 'Error ! Can not create a schedule for a date before the current.', ['date_begin']),
        ]

    def onchange_start_date(self, cr, uid, ids, date_begin, schedule_duration, date_end, context={}):
        values = {}
        if not date_begin and not date_end:
            return res
        schedule_begin = datetime.strptime(date_begin, "%Y-%m-%d %H:%M:%S")
        duration = schedule_duration
        date_end = schedule_begin + timedelta(hours=duration)
        values.update({
            'date_end' : date_end.strftime("%Y-%m-%d %H:%M:%S"),
        })
        return {'value' : values}

    def _get_professional_id(self, cr, uid, user_id):
        doctor = self.pool.get('doctor.professional').search(cr, uid, [('user_id','=',uid)])
        if doctor:
            return self.pool.get('doctor.professional').browse(cr, uid, doctor)[0].id
        return False

    _defaults = {
        'professional_id': _get_professional_id if _get_professional_id != False else False,
        'schedule_duration': 4,
        }

doctor_schedule()

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

class doctor_appointment_type(osv.osv):
    _name = "doctor.appointment.type"
    _columns = {
        'name': fields.char ('Type', size=10, required=True),
        'duration': fields.integer('Duration', required=True),
        }

doctor_appointment_type()

class doctor_appointment(osv.osv):
    _name = "doctor.appointment"
    _order = 'time_begin asc'
    _rec_name = 'number'

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'number'
        res = [(r['id'], r[rec_name])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

    def create(self, cr, uid, vals, context=None):
        # Set appointment number if empty
        if not vals.get('number'):
            vals['number'] = self.pool.get('ir.sequence').get(cr, uid, 'appointment.sequence')
        return super(doctor_appointment, self).create(cr, uid, vals, context=context)

    def button_confirm(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'confirm'}, context=context)

    def button_assists(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'assists'}, context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)

    def _time2user(self, cr, uid, ids, time_begin):
        time_begin_user = datetime.strptime(time_begin, "%Y-%m-%d %H:%M:%S")

        user = self.pool.get('res.users').browse(cr, uid, uid)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        time_begin_user = pytz.utc.localize(time_begin_user).astimezone(tz)

        time_begin_user = datetime.strftime(time_begin_user, "%Y-%m-%d")
        return time_begin_user

    def _get_appointment_today(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids):
            date_today = fields.date.context_today(self, cr, uid, context=context)
            time_begin = self._time2user(cr, uid, ids,record.time_begin)
            if time_begin == date_today:
                res[record.id] = True
            else:
                res[record.id] = False
        return res

    _columns = {
        'schedule_id': fields.many2one('doctor.schedule', 'Schedule', states={'invoiced':[('readonly',True)]}),
        'number': fields.char('Appointment number', select=1, size=32, readonly=True, help="Number of appointment. Keep empty to get the number assigned by a sequence."),
        'professional_id': fields.related ('schedule_id', 'professional_id', type="many2one", relation="doctor.professional", string='Professional', required=True, store=True),
        'patient_id': fields.many2one('doctor.patient',"Patient", required=True, states={'invoiced':[('readonly',True)]}),
        'insurer_id': fields.related ('patient_id', 'insurer', type="many2one", relation="doctor.insurer", string='Insurer', required=True, states={'invoiced':[('readonly',True)]}, store=True),
        'type_id' : fields.many2one('doctor.appointment.type',"Appointment type", states={'invoiced':[('readonly',True)]}),
        'time_begin': fields.datetime('Start time', required=True, states={'invoiced':[('readonly',True)]}),
        'time_end': fields.datetime('End time', required=True, states={'invoiced':[('readonly',True)]}),
        'appointment_today': fields.function (_get_appointment_today, type = "boolean", store=True, readonly=True, method=True, string="Appointment today"),
        'state': fields.selection([
            ('draft', 'Unconfirmed'), ('cancel', 'Cancelled'),
            ('confirm', 'Confirmed'), ('assists', 'Waiting'),
            ('attending', 'Attending'), ('invoiced', 'Invoiced')],
            'Status', readonly=True, required=True),
        'procedures_id': fields.one2many('doctor.appointment.procedures', 'appointment_id', 'Health Procedures', ondelete='restrict', states={'invoiced':[('readonly',True)]}),
        'order_id' : fields.many2one('sale.order', 'Order', ondelete='restrict', readonly=True),
        'attentiont_id' : fields.many2one('doctor.attentions', 'Attentiont', ondelete='restrict', readonly=True),
        'attended': fields.boolean('Attended', readonly=True),
        'aditional': fields.boolean('Aditional'),
        'nb_register': fields.integer('Number of Participants', required=True, readonly=True),
        }

    _defaults = {
        'state': 'draft',
        'aditional': False,
        'schedule_id': lambda self, cr, uid, context: context.get('schedule_id', False),
        'nb_register': 1,
    }

    def update_appointment_today(self, cr, uid, ids=False, context=None):
        if context is None:
            context = {}
        if not ids:
            ids = self.search(cr, uid, [], context=None)
        return super(doctor_appointment, self).write(cr, uid, ids, {'appointment_today': 'True'}, context=context)

    def _check_appointment(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            appointment_ids = self.search(cr, uid, [('time_begin', '<', record.time_end), ('time_end', '>', record.time_begin), ('aditional', '=', record.aditional), ('state', '=',record.state), ('id', '<>', record.id)])
            if appointment_ids:
                return False
        return True

    def _check_closing_time(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.time_end < record.time_begin:
                return False
        return True

    def _check_date_appointment(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            schedule_begin = record.schedule_id.date_begin
            schedule_end = record.schedule_id.date_end
            time_begin = record.time_begin
            time_end = record.time_end
            if time_begin < schedule_begin or time_end > schedule_end:
                return False
        return True

    _constraints = [
        (_check_closing_time, 'Error ! Closing Time cannot be set before Beginning Time.', ['time_end']),
        (_check_appointment, 'Error ! Already exists an appointment at that time.', ['time_begin','time_end']),
        (_check_date_appointment, 'Error ! Appointment time outside scheduling.', ['time_begin','time_end']),
        ]

    def onchange_patient(self, cr, uid, ids, patient_id, insurer_id, context=None):
        values = {}
        if not patient_id:
            return values
        patient = self.pool.get('doctor.patient').browse(cr, uid, patient_id, context=context)
        insurer_patient = patient.insurer.id
        values.update({
            'insurer_id' : insurer_patient,
        })
        return {'value' : values}

    def onchange_start_time(self, cr, uid, ids, schedule_id, professional_id, time_begin, context=None):
        values = {}
        if not schedule_id:
            return values
        schedule = self.pool.get('doctor.schedule').browse(cr, uid, schedule_id, context=context)
        schedule_professional = schedule.professional_id.id
        schedule_begin = datetime.strptime(schedule.date_begin, "%Y-%m-%d %H:%M:%S")
        time_begin = schedule_begin.strftime("%Y-%m-%d %H:%M:%S")
        values.update({
            'time_begin' : time_begin,
            'professional_id' : schedule_professional,
        })
        return {'value' : values}

    def onchange_end_time(self, cr, uid, ids, type_id, time_begin, time_end, context=None):
        values = {}
        if not type_id:
            return values
        time_begin = datetime.strptime(time_begin, "%Y-%m-%d %H:%M:%S")
        appointment_type = self.pool.get('doctor.appointment.type').browse(cr, uid, type_id, context=context)
        duration = appointment_type.duration
        time_end = time_begin + timedelta(minutes=duration)
        time_end = time_end.strftime("%Y-%m-%d %H:%M:%S")
        values.update({
            'time_end' : time_end,
        })
        return {'value' : values}

    def create_order(self, cr, uid, doctor_appointment, date, appointment_procedures, confirmed_flag, context={}):
        """
        Method that creates an order from given data.
        @param doctor_appointment: Appointment method get data from.
        @param date: Date of created order.
        @param appointment_procedures: Lines that will generate order lines.
        @confirmed_flag: Confirmed flag in agreement order line will be set to this value.
        """
        order_obj = self.pool.get('sale.order')
        order_line_obj = self.pool.get('sale.order.line')
        # Create order object
        order = {
            'date_order': date.strftime('%Y-%m-%d'),
            'origin': doctor_appointment.number,
            'partner_id': doctor_appointment.insurer_id.insurer.id,
            'patient_id': doctor_appointment.patient_id.id,
            'state': 'draft',
        }
        # Get other order values from appointment partner
        order.update(sale.sale.sale_order.onchange_partner_id(order_obj, cr, uid, [], doctor_appointment.insurer_id.insurer.id)['value'])
        order['user_id'] = doctor_appointment.insurer_id.insurer.user_id.id
        order_id = order_obj.create(cr, uid, order, context=context)
        # Create order lines objects
        appointment_procedures_ids = []
        for procedures_id in appointment_procedures:
            order_line = {
                'order_id': order_id,
                'product_id': procedures_id.procedures_id.id,
                'product_uom_qty': procedures_id.quantity,
            }
            # get other order line values from appointment procedures line product
            order_line.update(sale.sale.sale_order_line.product_id_change(order_line_obj, cr, uid, [], order['pricelist_id'], \
                product=procedures_id.procedures_id.id, qty=procedures_id.quantity, partner_id=doctor_appointment.insurer_id.insurer.id, fiscal_position=order['fiscal_position'])['value'])
            # Put line taxes
            order_line['tax_id'] = [(6, 0, tuple(order_line['tax_id']))]
            # Put custom description
            if procedures_id.additional_description:
                order_line['name'] += " " + procedures_id.additional_description
            order_line_obj.create(cr, uid, order_line, context=context)
            appointment_procedures_ids.append(procedures_id.id)
        # Create order appointment record
        appointment_order = {
            'order_id': order_id,
        }
        self.pool.get('doctor.appointment').write(cr, uid, [doctor_appointment.id], appointment_order, context=context)

        return order_id

    def generate_order(self, cr, uid, ids, context={}):
        """
        Method that creates an order with all the appointment procedures lines
        """
        doctor_appointment = self.browse(cr, uid, ids, context=context)[0]
        time_begin = doctor_appointment.time_begin
        time_begin = time_begin.split(" ")[0]
        date_begin = datetime.strptime(time_begin, "%Y-%m-%d")
        appointment_procedures = []
        # Add only active lines
        for line in doctor_appointment.procedures_id:
            if line: appointment_procedures.append(line)
        order_id = self.create_order(cr, uid, doctor_appointment, date_begin, appointment_procedures, True, context=context)
        # Update appointment state
        self.write(cr, uid, doctor_appointment.id, { 'state': 'invoiced' }, context=context)
        # Get view to show
        data_obj = self.pool.get('ir.model.data')
        result = data_obj._get_id(cr, uid, 'sale', 'view_order_form')
        view_id = data_obj.browse(cr, uid, result).res_id
        # Return view with order created
        return {
            'domain': "[('id','=', " + str(order_id) + ")]",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'context': context,
            'res_id': order_id,
            'view_id': [view_id],
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }

    def create_attentiont(self, cr, uid, doctor_appointment, context={}):
        """
        Method that creates an attention from given data.
        @param doctor_appointment: Appointment method get data from.
        """
        attentiont_obj = self.pool.get('doctor.attentions')
        # Create attentiont object
        attentiont = {
            'patient_id': doctor_appointment.patient_id.id,
            'professional_id' : doctor_appointment.professional_id.id,
            'origin': doctor_appointment.number,
        }
        # Get other attentiont values from appointment partner
        attentiont.update(doctor_attentions.onchange_patient(attentiont_obj, cr, uid, [], doctor_appointment.patient_id.id)['value'])
        attentiont.update(doctor_attentions.onchange_professional(attentiont_obj, cr, uid, [], doctor_appointment.professional_id.id)['value'])
        attentiont_id = attentiont_obj.create(cr, uid, attentiont, context=context)
        # Create number attentiont record
        attentiont_number = {
            'attentiont_id': attentiont_id,
        }
        self.pool.get('doctor.appointment').write(cr, uid, [doctor_appointment.id], attentiont_number, context=context)

        return attentiont_id

    def generate_attentiont(self, cr, uid, ids, context={}):
        """
        Method that creates an attentiont
        """
        doctor_appointment = self.browse(cr, uid, ids, context=context)[0]

        attentiont_id = self.create_attentiont(cr, uid, doctor_appointment, context=context)
        # Update appointment state
        appointment_state = doctor_appointment.state
        if appointment_state != 'invoiced':
            self.write(cr, uid, doctor_appointment.id, { 'state': 'attending' }, context=context)
        self.write(cr, uid, doctor_appointment.id, { 'attended': True }, context=context)
        # Get view to show
        data_obj = self.pool.get('ir.model.data')
        result = data_obj._get_id(cr, uid, 'doctor', 'view_doctor_attentions_form')
        view_id = data_obj.browse(cr, uid, result).res_id
        # Return view with attentiont created
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'doctor.attentions',
            'context': context,
            'res_id': attentiont_id,
            'view_id': [view_id],
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }

doctor_appointment()

class doctor_appointment_procedures (osv.osv):
    _name = "doctor.appointment.procedures"
    _rec_name = 'procedures_id'
    _columns = {
        'appointment_id' : fields.many2one ('doctor.appointment', 'Appointment'),
        'professional_id': fields.many2one ('doctor.professional','Doctor'),
        'procedures_id' : fields.many2one ('product.product', 'Health Procedures', required=True, ondelete='restrict'),
        'quantity' : fields.integer ('Quantity', required=True),
        'additional_description': fields.char('Add. description', size=30, help='Additional description that will be added to the product description on orders.'),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'procedures_id'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

    _defaults = {
         'professional_id': lambda self, cr, uid, context: context.get('professional_id', False),
         'quantity' : 1,
    }

doctor_appointment_procedures ()

class doctor_diseases (osv.osv):
    _name = "doctor.diseases"
    _columns = {
        'code' : fields.char ('Code', size=4, required=True),
        'name' :fields.char ('Disease', size=256, required=True),
        }

    _sql_constraints = [('code_uniq', 'unique (code)', 'The Medical Diseases code must be unique')]

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

doctor_diseases ()

class doctor_attentions(osv.osv):
    _name = "doctor.attentions"
    _rec_name = 'number'
    _order = "date_attention desc"

    def create(self, cr, uid, vals, context=None):
        # Set appointment number if empty
        if not vals.get('number'):
            vals['number'] = self.pool.get('ir.sequence').get(cr, uid, 'attention.sequence')
        return super(doctor_attentions, self).create(cr, uid, vals, context=context)

    def button_closed(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'closed'}, context=context)

    def _previous(self, cr, uid, patient_id, type_past, attentiont_id=None):
        condition = [('patient_id', '=', patient_id.id)]
        if attentiont_id != None:
            condition.append (('attentiont_id', '<=', attentiont_id))
        if type_past == 'past':
            return self.pool.get('doctor.attentions.past').search(cr, uid, condition, order = 'id desc' )
        if type_past == 'pathological':
            return self.pool.get('doctor.diseases.past').search(cr, uid, condition, order = 'id desc' )
        if type_past == 'drugs':
            return self.pool.get('doctor.atc.past').search(cr, uid, condition, order = 'id desc' )

    def _get_past(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for datos in self.browse(cr,uid,ids):
            res[datos.id] = self._previous(cr, uid, datos.patient_id, 'past', datos.id)
        return res

    def _get_pathological_past(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for datos in self.browse(cr,uid,ids):
            res[datos.id] = self._previous(cr, uid, datos.patient_id, 'pathological', datos.id)
        return res

    def _get_drugs_past(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for datos in self.browse(cr,uid,ids):
            res[datos.id] = self._previous(cr, uid, datos.patient_id, 'drugs', datos.id)
        return res

    _columns = {
        'patient_id': fields.many2one ('doctor.patient', 'Patient', ondelete='restrict', readonly= True),
        'patient_photo' : fields.related ('patient_id', 'photo', type="binary", relation="doctor.patient", readonly= True),
        'date_attention': fields.datetime ('Date of attention', required=True, readonly= True),
        'number': fields.char('Attention number', select=1, size=32, readonly=True, help="Number of attention. Keep empty to get the number assigned by a sequence."),
        'origin': fields.char('Source Document', size=64, help="Reference of the document that produced this attentiont.", readonly=True),
        'age_attention':fields.integer('Current age', readonly= True),
        'age_unit':fields.selection([('1','Years'),('2','Months'),('3','Days'),],'Unit of measure of age', readonly= True),
        'professional_id': fields.many2one ('doctor.professional', 'Doctor', required=True, readonly= True),
        'speciality': fields.related ('professional_id', 'speciality_id', type="many2one", relation="doctor.speciality", string='Speciality', required=True, store=True, states={'closed':[('readonly',True)]}),
        'professional_photo' : fields.related ('professional_id', 'photo', type="binary", relation="doctor.professional", readonly= True, store=False),
        'reason_consultation': fields.many2many('doctor.diseases', id1='attention_id', id2='reason_consultation', string='Reason for consultation', required=False, ondelete='restrict', states={'closed':[('readonly',True)]}),
        'actual_disease': fields.text ('Current disease', required=False, states={'closed':[('readonly',True)]}),
        'review_systems_id': fields.one2many ('doctor.review.systems','attentiont_id', 'Review of systems', ondelete='restrict', states={'closed':[('readonly',True)]}),
        'attentions_past_ids': fields.one2many('doctor.attentions.past', 'attentiont_id', 'Past', ondelete='restrict', states={'closed':[('readonly',True)]}),
        'past_ids': fields.function (_get_past, relation="doctor.attentions.past", type = "one2many", store=False, readonly=True, method=True, string="Old Past"),
        'pathological_past' : fields.one2many('doctor.diseases.past', 'attentiont_id', 'Pathological past', ondelete='restrict', states={'closed':[('readonly',True)]}),
        'pathological_past_ids': fields.function (_get_pathological_past, relation="doctor.diseases.past", type = "one2many", store=False, readonly=True, method=True, string="Old Pathological Past"),
        'drugs_past' : fields.one2many('doctor.atc.past', 'attentiont_id', 'Drugs past', ondelete='restrict', states={'closed':[('readonly',True)]}),
        'drugs_past_ids': fields.function (_get_drugs_past, relation="doctor.atc.past", type = "one2many", store=False, readonly=True, method=True, string="Old drugs Past"),
        'weight' : fields.float('Weight (kg)', states={'closed':[('readonly',True)]}),
        'height' : fields.float('Height (cm)', states={'closed':[('readonly',True)]}),
        'body_mass_index' : fields.float('Body Mass Index', states={'closed':[('readonly',True)]}),
        'heart_rate' : fields.integer ('Heart Rate',help="Heart rate expressed in beats per minute", states={'closed':[('readonly',True)]}),
        'respiratory_rate' : fields.integer ('Respiratory Rate',help="Respiratory rate expressed in breaths per minute", states={'closed':[('readonly',True)]}),
        'systolic' : fields.integer('Systolic Pressure', states={'closed':[('readonly',True)]}),
        'diastolic' : fields.integer('Diastolic Pressure', states={'closed':[('readonly',True)]}),
        'temperature' : fields.float('Temperature (celsius)', states={'closed':[('readonly',True)]}),
        'pulsioximetry' : fields.integer ('Oxygen Saturation',help="Oxygen Saturation (arterial).", states={'closed':[('readonly',True)]}),
        'attentions_exam_ids': fields.one2many('doctor.attentions.exam', 'attentiont_id', 'Exam', ondelete='restrict', states={'closed':[('readonly',True)]}),
        'analysis': fields.text ('Analysis', required=False, states={'closed':[('readonly',True)]}),
        'conduct': fields.text ('Conduct', required=False, states={'closed':[('readonly',True)]}),
        'diseases_ids': fields.one2many('doctor.attentions.diseases', 'attentiont_id', 'Diseases', ondelete='restrict', states={'closed':[('readonly',True)]}),
        'drugs_ids': fields.one2many('doctor.prescription', 'attentiont_id', 'Drugs prescription', ondelete='restrict', states={'closed':[('readonly',True)]}),
        'diagnostic_images_ids': fields.one2many('doctor.attentions.procedures', 'attentiont_id', 'Diagnostic Images', ondelete='restrict', states={'closed':[('readonly',True)]}, domain=[('procedures_id.procedure_type', '=', 3)]),
        'clinical_laboratory_ids': fields.one2many('doctor.attentions.procedures', 'attentiont_id', 'Clinical Laboratory', ondelete='restrict', states={'closed':[('readonly',True)]}, domain=[('procedures_id.procedure_type', '=', 4)]),
        'surgical_procedure_ids': fields.one2many('doctor.attentions.procedures', 'attentiont_id', 'Surgical Procedure', ondelete='restrict', states={'closed':[('readonly',True)]}, domain=[('procedures_id.procedure_type', '=', 2)]),
        'therapeutic_procedure_ids': fields.one2many('doctor.attentions.procedures', 'attentiont_id', 'Therapeutic Procedure', ondelete='restrict', states={'closed':[('readonly',True)]}, domain=[('procedures_id.procedure_type', '=', 5)]),
        'other_procedure_ids': fields.one2many('doctor.attentions.procedures', 'attentiont_id', 'Other Procedure', ondelete='restrict', states={'closed':[('readonly',True)]}, domain=['|',('procedures_id.procedure_type', '=', 1), '|', ('procedures_id.procedure_type', '=', 6), ('procedures_id.procedure_type', '=', 7)]),
        'referral_ids': fields.one2many('doctor.attentions.referral', 'attentiont_id', 'Referral', ondelete='restrict', states={'closed':[('readonly',True)]}),
        'disability_ids': fields.one2many('doctor.attentions.disability', 'attentiont_id', 'Disability', ondelete='restrict', states={'closed':[('readonly',True)]}),
        'state': fields.selection([('open', 'Open'), ('closed', 'Closed')], 'Status', readonly=True, required=True),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'number'
        res = [(r['id'], r[rec_name])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

    def onchange_professional(self, cr, uid, ids, professional_id, context=None):
        values = {}
        if not professional_id:
            return values
        professional_data = self.pool.get('doctor.professional').browse(cr, uid, professional_id, context=context)
        professional_img = professional_data.photo
        professional_speciality = professional_data.speciality_id.id
        values.update({
            'professional_photo' : professional_img,
            'speciality' : professional_speciality,
        })
        return {'value' : values}

    def onchange_patient(self, cr, uid, ids, patient_id, context=None):
        values = {}
        if not patient_id:
            return values
        past = self.pool.get('doctor.attentions.past').search(cr, uid, [('patient_id', '=', patient_id)], order = 'id asc')
        phatological_past = self.pool.get('doctor.diseases.past').search(cr, uid, [('patient_id', '=', patient_id)], order = 'id asc')
        drugs_past = self.pool.get('doctor.atc.past').search(cr, uid, [('patient_id', '=', patient_id)], order = 'id asc' )
        patient_data = self.pool.get('doctor.patient').browse(cr, uid, patient_id, context=context)
        photo_patient = patient_data.photo
        patient_birth_date = patient_data.birth_date
        current_date = datetime.today()
        st_birth_date = datetime.strptime(patient_birth_date, '%Y-%m-%d')
        re = current_date-st_birth_date
        dif_days = re.days
        age = dif_days
        age_unit = ''
        if age<30:
            age_attention = age,
            age_unit = '3'

        elif age>30 and age<365:
            age=age/30
            age=int(age)
            age_attention = age,
            age_unit = '2'

        elif age>365:
            age=age/365
            age=int(age)
            age_attention = age,
            age_unit = '1'

        values.update({
            'patient_photo' : photo_patient,
            'age_attention' : age,
            'age_unit' : age_unit,
            'past_ids' : past,
            'pathological_past_ids' : phatological_past,
            'drugs_past_ids': drugs_past,
        })
        return {'value' : values}

    def _get_professional_id(self, cr, uid, user_id):
        return self.pool.get('doctor.professional').browse(cr, uid, self.pool.get('doctor.professional').search(cr, uid, [('user_id','=',uid)]))[0].id,

    _defaults = {
        'patient_id': lambda self, cr, uid, context: context.get('patient_id', False),
        'date_attention': lambda *a: datetime.strftime (datetime.now(), "%Y-%m-%d %H:%M:%S"),
        'professional_id': _get_professional_id,
        'state': 'open',
        }

doctor_attentions()

class doctor_systems_category (osv.osv):

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
    _columns = {
        'name': fields.char('Category Name', required=True, size=64, translate=True),
        'parent_id': fields.many2one('doctor.systems.category', 'Parent Category', select=True, ondelete='cascade'),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Full Name'),
        'child_ids': fields.one2many('doctor.systems.category', 'parent_id', 'Child Categories'),
        'active': fields.boolean('Active', help="The active field allows you to hide the category without removing it."),
        'parent_left': fields.integer('Left parent', select=True),
        'parent_right': fields.integer('Right parent', select=True),
    }

    _constraints = [
        (osv.osv._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]

    _defaults = {
        'active': 1,
    }

    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'

doctor_systems_category ()

class doctor_review_systems (osv.osv):
    _name = "doctor.review.systems"
    _rec_name = 'attentiont_id'
    _columns = {
        'attentiont_id' : fields.many2one ('doctor.attentions', 'Attention'),
        'system_category' : fields.many2one ('doctor.systems.category', 'Systems category', required=True, ondelete='restrict'),
        'review_systems' : fields.text ('Review systems', required=True),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'attentiont_id'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

doctor_review_systems ()

class doctor_past_category (osv.osv):

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
    _columns = {
        'name': fields.char('Category Name', required=True, size=64, translate=True),
        'parent_id': fields.many2one('doctor.past.category', 'Parent Category', select=True, ondelete='cascade'),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Full Name'),
        'child_ids': fields.one2many('doctor.past.category', 'parent_id', 'Child Categories'),
        'active': fields.boolean('Active', help="The active field allows you to hide the category without removing it."),
        'parent_left': fields.integer('Left parent', select=True),
        'parent_right': fields.integer('Right parent', select=True),
    }

    _constraints = [
        (osv.osv._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]

    _defaults = {
        'active': 1,
    }

    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'

doctor_past_category ()

class doctor_attentions_past (osv.osv):
    _name = "doctor.attentions.past"
    _rec_name = 'attentiont_id'
    _columns = {
        'attentiont_id' : fields.many2one ('doctor.attentions', 'Attention', ondelete='restrict'),
        'patient_id' : fields.many2one ('doctor.patient', 'Patient', required=True, ondelete='restrict'),
        'past_category' : fields.many2one ('doctor.past.category', 'Past category', required=True, ondelete='restrict'),
        'past' : fields.text ('Past', required=True),
        }

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

doctor_attentions_past ()

class doctor_diseases_past (osv.osv):
    _name = "doctor.diseases.past"
    _rec_name = 'attentiont_id'
    _columns = {
        'attentiont_id' : fields.many2one ('doctor.attentions', 'Attention', ondelete='restrict'),
        'patient_id' : fields.many2one ('doctor.patient', 'Patient', required=True, ondelete='restrict'),
        'diseases_id' : fields.many2one ('doctor.diseases', 'Past diseases', required=True, ondelete='restrict'),
        }

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

doctor_diseases_past ()

class doctor_atc_past (osv.osv):
    _name = "doctor.atc.past"
    _rec_name = 'attentiont_id'
    _columns = {
        'attentiont_id' : fields.many2one ('doctor.attentions', 'Attention', ondelete='restrict'),
        'patient_id' : fields.many2one ('doctor.patient', 'Patient', required=True, ondelete='restrict'),
        'atc_id' : fields.many2one ('doctor.atc', 'Past drugs', required=True, ondelete='restrict'),
        }

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

doctor_atc_past ()

class doctor_exam_category (osv.osv):

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
    _columns = {
        'name': fields.char('Category Name', required=True, size=64, translate=True),
        'parent_id': fields.many2one('doctor.exam.category', 'Parent Category', select=True, ondelete='cascade'),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Full Name'),
        'child_ids': fields.one2many('doctor.exam.category', 'parent_id', 'Child Categories'),
        'active': fields.boolean('Active', help="The active field allows you to hide the category without removing it."),
        'parent_left': fields.integer('Left parent', select=True),
        'parent_right': fields.integer('Right parent', select=True),
    }

    _constraints = [
        (osv.osv._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]

    _defaults = {
        'active': 1,
    }

    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'

doctor_exam_category ()

class doctor_attentions_exam (osv.osv):
    _name = "doctor.attentions.exam"
    _rec_name = 'attentiont_id'
    _columns = {
        'attentiont_id' : fields.many2one ('doctor.attentions', 'Attention'),
        'exam_category' : fields.many2one ('doctor.exam.category', 'Exam category', required=True, ondelete='restrict'),
        'exam' : fields.text ('Exam', required=True),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'attentiont_id'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

doctor_attentions_exam ()

class doctor_attentions_diseases (osv.osv):
    _name = "doctor.attentions.diseases"
    _rec_name = 'diseases_id'
    _columns = {
        'attentiont_id' : fields.many2one ('doctor.attentions', 'Attention'),
        'diseases_id' : fields.many2one ('doctor.diseases', 'Disease', required=True, ondelete='restrict'),
        'status' : fields.selection([
            ('presumptive', 'Presumptive'),
            ('confirm', 'Confirmed'),
            ('recurrent', 'Recurrent')],
            'Status', required=True),
        'diseases_type' : fields.selection([
            ('main', 'Main'),
            ('related', 'Related')],
            'Type', required=True),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'diseases_id'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

    _defaults = {
        'status': 'presumptive',
        'diseases_type': 'main',
        }

doctor_diseases ()

class doctor_attentions_procedures (osv.osv):
    _name = "doctor.attentions.procedures"
    _rec_name = 'procedures_id'
    _columns = {
        'attentiont_id' : fields.many2one ('doctor.attentions', 'Attention'),
        'procedures_id' : fields.many2one ('product.product', 'Health Procedures', required=True, ondelete='restrict'),
        'quantity' : fields.integer ('Quantity', required=True),
        'indications' : fields.char ('Indications', size=256),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'procedures_id'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

    _defaults = {
        'quantity': 1,
        }

doctor_attentions_procedures ()

class doctor_attentions_referral (osv.osv):
    _name = "doctor.attentions.referral"
    _rec_name = 'referral_ids'
    _columns = {
        'attentiont_id' : fields.many2one ('doctor.attentions', 'Attention'),
        'referral_ids' : fields.selection([
            ('consult', 'Consultation'),
            ('urgency', 'Urgency'),
            ('hospital', 'Hospitalization'),],
            'Service', required=True),
        'speciality_id' : fields.many2one ('doctor.speciality', 'Speciality', required=True, ondelete='restrict'),
        'interconsultation': fields.boolean('Is interconsultation?'),
        'cause' : fields.text ('Referral cause', required=True),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'referral_ids'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

doctor_attentions_referral ()

class doctor_attentions_disability (osv.osv):
    _name = "doctor.attentions.disability"
    _rec_name = 'disability_ids'
    _columns = {
        'attentiont_id' : fields.many2one ('doctor.attentions', 'Attention'),
        'disability_ids' : fields.date('Start date', required=True, ondelete='restrict'),
        'duration': fields.integer('Duration', required=True),
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'disability_ids'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

doctor_attentions_disability ()

class doctor_pharmaceutical_form (osv.osv):
    _name = "doctor.pharmaceutical.form"
    _columns = {
        'code' : fields.char ('Code', size=10, required=True),
        'name' :fields.char ('Pharmaceutical form', size=128, required=True),
        }

    _sql_constraints = [('code_uniq', 'unique (code)', 'The Pharmaceutical Form code must be unique')]

doctor_pharmaceutical_form ()

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

class doctor_health_procedures (osv.osv):
     _inherit = "product.product"

     def onchange_type (self, cr, uid, ids, type):
        if not type:
            return {}
        else:
            if type != 'service':
                return{'value': {
                              'health_procedure': False,
                              }
                    }

     def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        def _name_get(d):
            name = d.get('name','')
            code = d.get('default_code',False)
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

     _columns = {
                 'is_health_procedure':fields.boolean('Is Health Procedure?'),
                 'procedure_code': fields.char ('Code', size=16),
                 'procedure_description' : fields.char ('Description', size=256),
                 'complexity_level': fields.selection([('1','1'),('2','2'),('3','3')],'Complexity Level'),
                 'procedure_type': fields.selection([('1','Consultation'),('2','Surgical Procedure'),
                                                     ('3','Diagnostic Image'), ('4','Clinical laboratory'),
                                                     ('5','Therapeutic Procedure'), ('6','Hospitalization'),
                                                     ('7','Other')], 'Procedure Type'),
                 'professional_ids' : fields.many2many('doctor.professional', id1='procedures_ids', id2='professional_ids', string='My health procedures', required=False, ondelete='restrict'),
                 }

doctor_health_procedures()

class doctor_prescription (osv.osv):
    _name = "doctor.prescription"
    _rec_name = 'drugs_id'
    _columns = {
        'attentiont_id' : fields.many2one ('doctor.attentions', 'Attention'),
        'drugs_id' : fields.many2one ('doctor.drugs', 'Drug', required=True, ondelete='restrict'),
        'total_quantity' : fields.integer ('Total quantity', required=True),
        'measuring_unit_qt' : fields.many2one ('doctor.measuring.unit', 'Drug measuring unit', required=True, ondelete='restrict'),
        'action_id' : fields.selection ([
            ('take','Take'),
            ('inject','Inject'),
            ('apply','Apply'),
            ('inhale','Inhale'),
            ], 'Action', required=True),
        'quantity' : fields.integer ('Quantity', required=True),
        'measuring_unit_q' : fields.many2one ('doctor.measuring.unit', 'Drug measuring unit', required=True, ondelete='restrict'),
        'frequency' : fields.integer ('Frequency (each)', required=True),
        'frequency_unit_n' : fields.selection ([
            ('minutes','minutes'),
            ('hours','hours'),
            ('days','days'),
            ('weeks','weeks'),
            ('wr','when required'),
            ('total','total'),
            ], 'Frequency unit', required=True),
        'duration' : fields.integer ('Treatment duration', required=True),
        'duration_period_n' : fields.selection([
            ('minutes','minutes'),
            ('hours','hours'),
            ('days','days'),
            ('months','months'),
            ('indefinite','indefinite'),
            ], 'Treatment period', required=True),
        'administration_route_id' : fields.many2one ('doctor.administration.route', 'Administration route', required=True, ondelete='restrict'),
        'dose' : fields.integer ('Dose', required=True),
        'dose_unit_id' : fields.many2one ('doctor.dose.unit', 'Dose unit', required=True, ondelete='restrict'),
        'indications' : fields.text ('Indications'),
    }

    _defaults = {
        'action_id': 'take',
        'frequency_unit_n': 'hours',
        'duration_period_n' : 'days',
        }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'drugs_id'
        res = [(r['id'], r[rec_name][1])
        for r in self.read(cr, uid, ids, [rec_name], context)]
        return res

doctor_prescription ()

class doctor_invoice (osv.osv):
    _inherit = "account.invoice"
    _name = "account.invoice"

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_patient': 0.0,
                'amount_total': 0.0,
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_patient'] = invoice.amount_patient
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] - res[invoice.id]['amount_patient']
        return res

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    _columns = {
        'patient_id': fields.many2one('doctor.patient',"Patient"),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['amount_patient'], 20),
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_patient': fields.float('Amount patient', digits_compute= dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
        'amount_partner': fields.float('Amount partner', digits_compute= dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
        'account_patient': fields.many2one('account.account', 'Account patient', readonly=True, states={'draft':[('readonly',False)]}, help="The patient account used for this invoice."),
                 }

    def onchange_amount_patient(self, cr, uid, ids, amount_untaxed, amount_tax, amount_patient, context=None):
        values = {}
        if not amount_patient:
            return values
        total_invoice = amount_untaxed
        total_tax = amount_tax
        total_patient = amount_patient
        total_partner = total_invoice + total_tax - total_patient
        values.update({
            'amount_total' : total_partner,
        })
        return {'value' : values}

    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        """finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
        Hook method to be overridden in additional modules to verify and possibly alter the
        move lines to be created by an invoice, for special cases.
        :param invoice_browse: browsable record of the invoice that is generating the move lines
        :param move_lines: list of dictionaries with the account.move.lines (as for create())
        :return: the (possibly updated) final move_lines to create for this invoice
        """
        if invoice_browse.amount_patient != 0:
            account = invoice_browse.account_patient.id
            total_patient = invoice_browse.amount_patient
            if not account:
                raise osv.except_osv(_('Warning!'), _('Please define the account for the patient.'))
            else:
                line = {
                    'name': invoice_browse.name or '/',
                    'partner_id': invoice_browse.patient_id.patient.id,
                    'journal_id': invoice_browse.journal_id.id,
                    'account_id': account,
                    'invoice': invoice_browse.id,
                    'debit': total_patient,
                    'credit': 0.0,
                    'quantity': 1,
                    'tax_amount': 0.0,
                    'amount_currency': 0,
                }
                move_lines.append((0, 0, line))
        return move_lines

    def action_move_create(self, cr, uid, ids, context=None):
        """Creates invoice related analytics and financial move lines"""
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            if not inv.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
            company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
            # create the analytical lines
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
            # check if taxes are all computed
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
            self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

            # I disabled the check_total feature
            group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
            group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
            if group_check_total and uid in [x.id for x in group_check_total.users]:
                if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
                    raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)

            entry_type = ''
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
                entry_type = 'journal_pur_voucher'
                if inv.type == 'in_refund':
                    entry_type = 'cont_voucher'
            else:
                ref = self._convert_ref(cr, uid, inv.number)
                entry_type = 'journal_sale_vou'
                if inv.type == 'out_refund':
                    entry_type = 'cont_voucher'

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
            total_patient = inv.amount_patient
            total = total - total_patient
            acc_id = inv.account_id.id

            name = inv['name'] or '/'
            totlines = False
            if inv.payment_term:
                totlines = payment_term_obj.compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': inv.date_invoice})
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity': inv.date_due or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'ref': ref
            })

            date = inv.date_invoice or time.strftime('%Y-%m-%d')

            part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)

            line = self.group_lines(cr, uid, iml, line, inv)

            journal_id = inv.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)

            move = {
                'ref': inv.reference and inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            period_id = inv.period_id and inv.period_id.id or False
            ctx.update(company_id=inv.company_id.id,
                       account_period_prefer_normal=True)
            if not period_id:
                period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

            ctx.update(invoice=inv)
            move_id = move_obj.create(cr, uid, move, context=ctx)
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post(cr, uid, [move_id], context=ctx)
        self._log_event(cr, uid, ids)
        return True

    def invoice_pay_patient(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')

        inv = self.browse(cr, uid, ids[0], context=context)
        return {
            'name':_("Pay Invoice"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.patient_id.patient).id,
                'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.amount_patient or inv.amount_patient,
                'default_reference': inv.name,
                'close_after_process': True,
                'invoice_type': inv.type,
                'invoice_id': inv.id,
                'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
            }
        }

doctor_invoice()

class doctor_sales_order (osv.osv):
    _inherit = "sale.order"
    _name = "sale.order"

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val


    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_patient': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_patient'] = order.amount_patient
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] - res[order.id]['amount_patient']
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'patient_id': fields.many2one('doctor.patient',"Patient"),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['amount_patient'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        'amount_patient': fields.float('Amount patient', digits_compute= dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
        'amount_partner': fields.float('Amount partner', digits_compute= dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
                 }

    def onchange_amount_patient(self, cr, uid, ids, amount_untaxed, amount_tax, amount_patient, context=None):
        values = {}
        if not amount_patient:
            return values
        total_invoice = amount_untaxed
        total_tax = amount_tax
        total_patient = amount_patient
        total_partner = total_invoice + total_tax - total_patient
        values.update({
            'amount_total' : total_partner,
        })
        return {'value' : values}

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
            limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'patient_id': order.patient_id.id,
            'journal_id': journal_ids[0],
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'amount_patient': order.amount_patient,
            #~ 'amount_partner':  order.amount_partner,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals

doctor_sales_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
