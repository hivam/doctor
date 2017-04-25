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

from datetime import datetime, timedelta
from openerp.osv import fields, osv
from openerp.tools.translate import _
import pytz
from doctor_attentions import doctor_attentions
import logging
_logger = logging.getLogger(__name__)
class doctor_appointment_type(osv.osv):
	_name = "doctor.appointment.type"
	_columns = {
		'name': fields.char('Type', size=30, required=True),
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
			time_begin = self._time2user(cr, uid, ids, record.time_begin)
			if time_begin == date_today:
				res[record.id] = True
			else:
				res[record.id] = False
		return res

	_columns = {
		'schedule_id': fields.many2one('doctor.schedule', 'Schedule', states={'invoiced': [('readonly', True)]}),
		'number': fields.char('Appointment number', select=1, size=32, readonly=True,
							  help="Number of appointment. Keep empty to get the number assigned by a sequence."),
		'professional_id': fields.related('schedule_id', 'professional_id', type="many2one",
										  relation="doctor.professional", string='Professional', required=True,
										  store=True),
		'patient_id': fields.many2one('doctor.patient', "Patient", required=True,
									  states={'invoiced': [('readonly', True)]}),
		'insurer_id': fields.related('patient_id', 'insurer', type="many2one", relation="doctor.insurer",
									 string='Insurer', required=False, states={'invoiced': [('readonly', True)]},
									 store= True),
		'type_id': fields.many2one('doctor.appointment.type', "Appointment type",
								   states={'invoiced': [('readonly', True)]}),
		'time_begin': fields.datetime('Start time', required=True, states={'invoiced': [('readonly', True)]}),
		'time_end': fields.datetime('End time', required=True, states={'invoiced': [('readonly', True)]}),
		'appointment_today': fields.function(_get_appointment_today, type="boolean", store=True, readonly=True,
											 method=True, string="Appointment today"),
		'state': fields.selection([
									  ('draft', 'Unconfirmed'), ('cancel', 'Cancelled'),
									  ('confirm', 'Confirmed'), ('assists', 'Waiting'),
									  ('attending', 'Attending'), ('invoiced', 'Invoiced')],
								  'Status', readonly=True, required=True),
		'procedures_id': fields.one2many('doctor.appointment.procedures', 'appointment_id', 'Health Procedures',
										 ondelete='restrict', states={'invoiced': [('readonly', True)]}),
		'order_id': fields.many2one('sale.order', 'Order', ondelete='restrict', readonly=True),
		'attentiont_id': fields.many2one('doctor.attentions', 'Attentiont', ondelete='restrict', readonly=True),
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
			modulo_instalado = self.pool.get('ir.module.module').search(cr,uid,[('name', '=', 'doctor_multiroom'), ('state', '=', 'installed')],context=context)
			if modulo_instalado:
				if record.schedule_id.consultorio_id.multi_paciente:
					return True
			else:
				appointment_ids = self.search(cr, uid,
											  [('time_begin', '<', record.time_end), ('time_end', '>', record.time_begin),
											   ('aditional', '=', record.aditional), ('state', '=', record.state),
											   ('id', '<>', record.id)])
				if appointment_ids:
					return False
		
		return True

	def _check_closing_time(self, cr, uid, ids, context=None):
		for record in self.browse(cr, uid, ids, context=context):
			if record.time_end < record.time_begin:
				return False
		return True

	def _check_date_appointment(self, cr, uid, ids, context=None):
		fecha_hora_actual = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:00")
		fecha_hora_actual = datetime.strptime(fecha_hora_actual, "%Y-%m-%d %H:%M:00")
		fecha_usuario_ini = fecha_hora_actual.strftime('%Y-%m-%d 00:00:00')
		for record in self.browse(cr, uid, ids, context=context):
			schedule_begin = record.schedule_id.date_begin
			schedule_end = record.schedule_id.date_end
			time_begin = record.time_begin
			time_end = record.time_end
			if record.time_begin < fecha_usuario_ini:
				return True
			elif time_begin < schedule_begin or time_end > schedule_end:
				return False
		return True

	_constraints = [
		(_check_closing_time, 'Error ! Closing Time cannot be set before Beginning Time.', ['time_end']),
		(_check_appointment, 'Error ! Already exists an appointment at that time.', ['time_begin', 'time_end']),
		(_check_date_appointment, 'Error ! Appointment time outside scheduling.', ['time_begin', 'time_end']),
	]

	def onchange_patient(self, cr, uid, ids, patient_id, insurer_id, context=None):
		values = {}
		if not patient_id:
			return values
		patient = self.pool.get('doctor.patient').browse(cr, uid, patient_id, context=context)
		insurer_patient = patient.insurer.id
		values.update({
			'insurer_id': insurer_patient,
		})
		return {'value': values}

	def onchange_start_time(self, cr, uid, ids, schedule_id, professional_id, time_begin, context=None):
		values = {}
		if not schedule_id:
			return values
		schedule = self.pool.get('doctor.schedule').browse(cr, uid, schedule_id, context=context)
		schedule_professional = schedule.professional_id.id
		schedule_begin = datetime.strptime(schedule.date_begin, "%Y-%m-%d %H:%M:%S")
		time_begin = schedule_begin.strftime("%Y-%m-%d %H:%M:%S")
		values.update({
			'time_begin': time_begin,
			'professional_id': schedule_professional,
		})
		return {'value': values}

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
			'time_end': time_end,
		})
		return {'value': values}

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
		order.update(
			sale.sale.sale_order.onchange_partner_id(order_obj, cr, uid, [], doctor_appointment.insurer_id.insurer.id)[
				'value'])
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
			order_line.update(
				sale.sale.sale_order_line.product_id_change(order_line_obj, cr, uid, [], order['pricelist_id'], \
															product=procedures_id.procedures_id.id,
															qty=procedures_id.quantity,
															partner_id=doctor_appointment.insurer_id.insurer.id,
															fiscal_position=order['fiscal_position'])['value'])
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
		order_id = self.create_order(cr, uid, doctor_appointment, date_begin, appointment_procedures, True,
									 context=context)
		# Update appointment state
		self.write(cr, uid, doctor_appointment.id, {'state': 'invoiced'}, context=context)
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
			'professional_id': doctor_appointment.professional_id.id,
			'origin': doctor_appointment.number,
		}
		# Get other attentiont values from appointment partner
		attentiont.update(
			doctor_attentions.onchange_patient(attentiont_obj, cr, uid, [], doctor_appointment.patient_id.id)['value'])
		
		attentiont.update(
			doctor_attentions.onchange_professional(attentiont_obj, cr, uid, [], doctor_appointment.professional_id.id)[
				'value'])
		
		context['patient_id'] = doctor_appointment.patient_id.id
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
			self.write(cr, uid, doctor_appointment.id, {'state': 'attending'}, context=context)
		self.write(cr, uid, doctor_appointment.id, {'attended': True}, context=context)
		# Get view to show
		data_obj = self.pool.get('ir.model.data')
		result = data_obj._get_id(cr, uid, 'doctor', 'view_doctor_attentions_form')
		view_id = data_obj.browse(cr, uid, result).res_id
		# Return view with attentiont created
		_logger.info(doctor_appointment.type_id.name)
		return {
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'doctor.attentions',
			'res_id': attentiont_id,
			'view_id': [view_id],
			'type': 'ir.actions.act_window',
			'context' : context,
			'nodestroy': True,
			'target' : 'current',
		}

doctor_appointment()


class doctor_appointment_procedures(osv.osv):
	_name = "doctor.appointment.procedures"
	_rec_name = 'procedures_id'
	_columns = {
		'appointment_id': fields.many2one('doctor.appointment', 'Appointment'),
		'professional_id': fields.many2one('doctor.professional', 'Doctor'),
		'procedures_id': fields.many2one('product.product', 'Health Procedures', required=True, ondelete='restrict'),
		'quantity': fields.integer('Quantity', required=True),
		'additional_description': fields.char('Add. description', size=30,
											  help='Additional description that will be added to the product description on orders.'),
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
		'quantity': 1,
	}


doctor_appointment_procedures()
