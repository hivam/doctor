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
from odoo import models, fields, api

from odoo.tools.translate import _
import time
import unicodedata

class doctor_professional(models.Model):
	_name = "doctor.professional"
	_description = "Information about the healthcare professional"
	_rec_name = 'username'


	@api.multi
	def write(self, vals):
		datos = {'lastname': '', 'surname': '', 'firstname': '', 'middlename': ''}
		nombre = ''


		if 'lastname' in vals:
			datos['lastname'] = vals['lastname'] or ' '

		if 'surname' in vals:
			datos['surname'] = vals['surname'] or ' '

		if 'firstname' in vals:
			datos['firstname'] = vals['firstname']	or ' '

		if 	'middlename' in vals:
			datos['middlename'] = vals['middlename'] or ' '

		nombre = "%s %s %s %s" % (datos['lastname'] or self.lastname, datos['surname'] or self.surname or '',
				 datos['firstname'] or self.firtsname , datos['middlename'] or self.middlename or '')

		vals['nombreUsuario'] = nombre.upper()
		return super(doctor_professional, self).write(vals)

	professional = fields.Many2one('res.partner', 'Healthcare Professional', ondelete='cascade',
									domain=[('is_company', '=', False)])
	username = fields.Char('Username', size=64, required=True)
	photo = fields.Binary('patient')
	speciality_id = fields.Many2one('doctor.speciality', 'Speciality', required=True)
	professional_card = fields.Char('Professional card', size=64, required=True)
	authority = fields.Char('Authority', size=64, required=True)
	work_phone = fields.Char('Work Phone', size=64)
	work_mobile = fields.Char('Work Mobile', size=64)
	work_email = fields.Char('Work Email', size=240)
	user_id = fields.Many2one('res.users', 'User', help='Related user name', required=False, ondelete='cascade')
	active = fields.Boolean('Active', default=lambda *a: 1)
	procedures_ids = fields.Many2many('product.product', id1='professional_ids', id2='procedures_ids',
									   string='My health procedures', required=False, ondelete='restrict')


	def name_get(self):
		if not len(self._ids):
			return []
		rec_name = 'professional'
		res = [(r['id'], r[rec_name][1])
			for r in self.read([rec_name])]
		return res

	"""
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
	"""
	@api.model
	@api.onchange('username')
	def onchange_username(self):

		if self.env['res.users'].search([('login', '=', self.username)]):
			return {'value': {'username': False,}, 'warning': {'title': 'The username exists', 'message': "Please change the username"}}

		#self.user_id = usuarioid



doctor_professional()


class doctor_patient(models.Model):
	_name = "doctor.patient"
	_description = "Information about the patient"
	"""
	def write(self, cr, uid, ids, vals, context=None):
		datos = {'lastname': '', 'surname': '', 'firstname': '', 'middlename': ''}
		nombre = ''
		u = {}
		if context is None:
			context = {}
		for patient in self.browse(cr, uid, ids, context=context):
			partner_id = patient.patient
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

			if (('lastname' in vals) or ('surname' in vals) or ('firstname' in vals) or ('middlename' in vals)):


				nombre = "%s %s %s %s" % (datos['lastname'] or patient.lastname, datos['surname'] or patient.surname or '',
						 datos['firstname'] or patient.firstname , datos['middlename'] or patient.middlename or '')

				firstname = vals['firstname'] if 'firstname' in vals else partner_id.firtsname
				lastname = vals['lastname'] if 'lastname' in vals else partner_id.lastname
				surname = vals['surname'] if 'surname' in vals else partner_id.surname
				middlename = vals['middlename'] if 'middlename' in vals else partner_id.middlename

				u['name'] = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').upper()
				u['display_name'] = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').upper()
			

				vals['nombre'] = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').upper()


				if 'ref' in vals:

					u['ref'] = vals['ref']

				if 'firstname' in vals:
					if(type(firstname) is unicode):
						u['firtsname'] =  unicodedata.normalize('NFKD', firstname).encode('ASCII', 'ignore').upper()
					elif(type(firstname) is str):
						u['firtsname'] =  firstname.upper()
					else:
						u['firtsname'] =  ' '

				if 'lastname' in vals:
					if(type(lastname) is unicode):	
						u['lastname'] = unicodedata.normalize('NFKD', lastname).encode('ASCII', 'ignore').upper()
					elif(type(lastname) is str):
						u['lastname'] = lastname.upper()
					else:
						u['lastname'] = ' ' 

				if 'surname' in vals:		
					if(type(surname) is unicode):	
						u['surname'] = unicodedata.normalize('NFKD', surname).encode('ASCII', 'ignore').upper()
					elif(type(surname) is str) :
						u['surname'] = surname.upper()
					else:
						u['surname'] = ' '

				if 	'middlename' in vals:		
					if(type(middlename) is unicode):	
						u['middlename'] = unicodedata.normalize('NFKD', middlename).encode('ASCII', 'ignore').upper()
					elif(type(middlename) is str):
						u['middlename'] = middlename.upper()
					else:
						u['middlename'] = ' '

		if 'nombre' in vals:
			id_partner = self.search(cr, uid, [('id', '=', ids[0])], context=context)
			if id_partner:
				for partner in self.browse(cr, uid, id_partner, context=context):
					id_partner = partner.patient.id
			self.pool.get('res.partner').write(cr, uid, id_partner, u, context=context)

		return super(doctor_patient, self).write(cr, uid, ids, vals, context=context)


	
	"""

	@api.multi
	def _get_profesional_id(self):
		res = {}
		for datos in self.browse(cr, uid, ids):
			doctor_id = self.pool.get('doctor.professional').search(cr,uid,[('user_id','=',uid)],context=context)
			if doctor_id:
				res[datos.id] = doctor_id[0]
			else:
				res[datos.id] = False	
		return res

	patient = fields.Many2one('res.partner', 'Paciente', ondelete='cascade',
								   domain=[('is_company', '=', False)])
	firstname = fields.Char('Primer Nombre', size=15)
	middlename = fields.Char('Segundo Nombre', size=15)
	lastname = fields.Char('Primer Apellido', size=15)
	surname = fields.Char('Segundo Apellido', size=15)
	photo = fields.Binary('patient')
	birth_date = fields.Date('Date of Birth', required=True)
	sex = fields.Selection([('m', 'Male'), ('f', 'Female'), ], 'Sex', select=True, required=True)
	blood_type = fields.Selection([('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O'), ], 'Blood Type')
	rh = fields.Selection([('+', '+'), ('-', '-'), ], 'Rh')
	insurer = fields.Many2one('doctor.insurer', 'Insurer', required=False, help='Insurer')
	deceased = fields.Boolean('Deceased', help="Mark if the patient has died")
	death_date = fields.Date('Date of Death')
	death_cause = fields.Many2one('doctor.diseases', 'Cause of Death')
	attentions_ids = fields.One2many('doctor.attentions', 'patient_id', 'Attentions')
	#appointments_ids = fields.One2many('doctor.appointment', 'patient_id', 'Attentions')
	#get_professional_id = fields.Integer(compute='_get_profesional_id', type="integer", store= False,
	#						readonly=True, method=True)
	"""
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
	"""

doctor_patient()
