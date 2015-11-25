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
import logging
_logger = logging.getLogger(__name__)
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time


class doctor_professional(osv.osv):
	_name = "doctor.professional"
	_description = "Information about the healthcare professional"
	_rec_name = 'username'

	def write(self, cr, uid, ids, vals, context=None):
		datos = {'lastname': '', 'surname': '', 'firstname': '', 'middlename': ''}
		nombre = ''
		if context is None:
			context = {}
		for professional in self.browse(cr, uid, ids, context=context):
			if 'lastname' in vals:
				datos['lastname'] = vals['lastname'] or ' '

			if 'surname' in vals:
				datos['surname'] = vals['surname'] or ' '
			
			if 'firstname' in vals:
				datos['firstname'] = vals['firstname']	or ' '

			if 	'middlename' in vals:
				datos['middlename'] = vals['middlename'] or ' '

			nombre = "%s %s %s %s" % (datos['lastname'] or professional.lastname, datos['surname'] or professional.surname or '',
					 datos['firstname'] or professional.firtsname , datos['middlename'] or professional.middlename or '')

		vals['nombreUsuario'] = nombre.upper()
		return super(doctor_professional, self).write(cr, uid, ids, vals, context=context)

	_columns = {
		'professional': fields.many2one('res.partner', 'Healthcare Professional', ondelete='cascade',
										domain=[('is_company', '=', False)]),
		'username': fields.char('Username', size=64, required=True),
		'photo': fields.binary('patient'),
		'speciality_id': fields.many2one('doctor.speciality', 'Speciality', required=True),
		'professional_card': fields.char('Professional card', size=64, required=True),
		'authority': fields.char('Authority', size=64, required=True),
		'work_phone': fields.char('Work Phone', size=64),
		'work_mobile': fields.char('Work Mobile', size=64),
		'work_email': fields.char('Work Email', size=240),
		'user_id': fields.many2one('res.users', 'User', help='Related user name', required=False, ondelete='cascade'),
		'active': fields.boolean('Active'),
		'procedures_ids': fields.many2many('product.product', id1='professional_ids', id2='procedures_ids',
										   string='My health procedures', required=False, ondelete='restrict'),
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
			'photo': professional_img,
		})
		return {'value': values}

	def onchange_user(self, cr, uid, ids, user_id, context=None):
		work_email = False
		if user_id:
			work_email = self.pool.get('res.users').browse(cr, uid, user_id, context=context).email
		return {'value': {'work_email': work_email}}

	def onchange_username(self, cr, uid, ids, username, context=None):
		if self.pool.get('res.users').search(cr, uid, [('login', '=', username),], context):
			return {'value': {'username': False,}, 'warning': {'title': 'The username exists', 'message': "Please change the username"}}
		else:
			user_id = self.pool.get('res.users').create(cr, uid, {'login': username, 'name': username})
			return {'value': {'user_id': user_id, },}

doctor_professional()


class doctor_patient(osv.osv):
	_name = "doctor.patient"
	_description = "Information about the patient"

	def write(self, cr, uid, ids, vals, context=None):
		datos = {'lastname': '', 'surname': '', 'firstname': '', 'middlename': ''}
		nombre = ''
		if context is None:
			context = {}
		for patient in self.browse(cr, uid, ids, context=context):
			if 'birth_date' in vals:
				birth_date = vals['birth_date']
				current_date = time.strftime('%Y-%m-%d')
				if birth_date > current_date:
					raise osv.except_osv(_('Warning !'), _("Birth Date Can not be a future date "))
		
			if 'lastname' in vals:
				datos['lastname'] = vals['lastname'] or ' '

			if 'surname' in vals:
				datos['surname'] = vals['surname'] or ' '
			
			if 'firstname' in vals:
				datos['firstname'] = vals['firstname']	or ' '

			if 	'middlename' in vals:
				datos['middlename'] = vals['middlename'] or ' '

			nombre = "%s %s %s %s" % (datos['lastname'] or patient.lastname, datos['surname'] or patient.surname or '',
					 datos['firstname'] or patient.firstname , datos['middlename'] or patient.middlename or '')

		vals['nombre'] = nombre.upper()

		return super(doctor_patient, self).write(cr, uid, ids, vals, context=context)


	def create(self, cr, uid, vals, context=None):
		if 'birth_date' in vals:
			birth_date = vals['birth_date']
			current_date = time.strftime('%Y-%m-%d')
			if birth_date > current_date:
				raise osv.except_osv(_('Warning !'), _("Birth Date Can not be a future date "))

		if vals['middlename']:
			vals.update({'middlename': vals['middlename'].upper() })
		if vals['surname']:
			vals.update({'surname': vals['surname'].upper() })
		vals.update({'lastname': vals['lastname'].upper() })
		vals.update({'firstname': vals['firstname'].upper() })
		vals.update({'name' : "%s %s %s %s" % (vals['lastname'] , vals['surname'] or '' , vals['firstname'] , vals['middlename'] or '')})
		vals.update({'nombre' : vals['name'].upper()})
		if not vals['es_profesionalsalud']:
			id_tercero = self.pool.get('res.partner').create(cr, uid, {'ref': vals['ref'], 'tdoc': vals['tdoc'], 'middlename' : vals['middlename'] or '', 'surname' : vals['surname'] or '',  'lastname': vals['lastname'], 'firtsname': vals['firstname'], 'name': vals['name'], 'image': vals['photo'], 'city_id': vals['city_id'], 'state_id': vals['state_id'], 'street': vals['street'], 'phone': vals['telefono'], 'mobile': vals['movil'], 'email': vals['email'],'es_paciente': True, 'es_profesional_salud': False}, context)
			vals.update({'patient' : id_tercero}) #una vez creamos el tercero podemos añadir el partner al campo patient.
		else:
			partner_id = self.pool.get('res.partner').search(cr, uid, [('ref','=', vals['ref'])])
			self.pool.get('res.partner').write(cr, uid, partner_id, {'es_paciente': True}, context=context)

		return super(doctor_patient, self).create(cr, uid, vals, context=context)

	_columns = {
		'patient': fields.many2one('res.partner', 'Paciente', ondelete='cascade',
								   domain=[('is_company', '=', False)]),
		'firstname' : fields.char('Primer Nombre', size=15, required=True),
		'middlename' : fields.char('Segundo Nombre', size=15),
		'lastname' : fields.char('Primer Apellido', size=15, required=True),
		'surname' : fields.char('Segundo Apellido', size=15),
		'photo': fields.binary('patient'),
		'birth_date': fields.date('Date of Birth', required=True),
		'sex': fields.selection([('m', 'Male'), ('f', 'Female'), ], 'Sex', select=True, required=True),
		'blood_type': fields.selection([('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O'), ], 'Blood Type'),
		'rh': fields.selection([('+', '+'), ('-', '-'), ], 'Rh'),
		'insurer': fields.many2one('doctor.insurer', 'Insurer', required=False, help='Insurer'),
		'deceased': fields.boolean('Deceased', help="Mark if the patient has died"),
		'death_date': fields.date('Date of Death'),
		'death_cause': fields.many2one('doctor.diseases', 'Cause of Death'),
		'attentions_ids': fields.one2many('doctor.attentions', 'patient_id', 'Attentions'),
		'appointments_ids': fields.one2many('doctor.appointment', 'patient_id', 'Attentions'),
	}

	def name_get(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		if not ids:
			return []
		if isinstance(ids,(long,int)):
			ids=[ids]
		res=[]

		for record in self.browse(cr,uid,ids):
			res.append((record['id'],record.nombre or ''))

		return res

	def onchange_patient_data(self, cr, uid, ids, patient, photo, context=None):
		values = {}
		if not patient:
			return values
		patient_data = self.pool.get('res.partner').browse(cr, uid, patient, context=context)
		patient_img = patient_data.image_medium
		values.update({
			'photo': patient_img,
		})
		return {'value': values}


doctor_patient()
