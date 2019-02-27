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

from odoo import models, fields, api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class doctor_speciality(models.Model):
	_name = "doctor.speciality"
	code = fields.Char('Code', size=3, required=True)
	name = fields.Char('Speciality', size=64, required=True)


	_sql_constraints = [('code_uniq', 'unique (code)', 'The Medical Speciality code must be unique')]

doctor_speciality()


class doctor_insurer(models.Model):
	_name = "doctor.insurer"
	_rec_name = 'insurer'
	insurer = fields.Many2one('res.partner', 'Insurer', help='Insurer')
	code = fields.Char('Code', size=6, required=True)

	@api.multi
	def name_get(self):
		res = []

		for record in self:
			aseguradora= ''
			try:
				aseguradora = record.insurer.name
			except:
				_logger.info("---Hubo un error en name_get de iniciativas")

			res.append((record.id, aseguradora))
		return res

	
	_sql_constraints = [('code_uniq', 'unique (code)', 'The insurer code must be unique')]

doctor_insurer()


class doctor_pharmaceutical_form(models.Model):
	_name = "doctor.pharmaceutical.form"

	code = fields.Char('Code', size=10, required=True)
	name = fields.Char('Pharmaceutical form', size=128, required=True)


	_sql_constraints = [('code_uniq', 'unique (code)', 'The Pharmaceutical Form code must be unique')]


doctor_pharmaceutical_form()


class doctor_dose_unit(models.Model):
	_name = "doctor.dose.unit"

	code = fields.Char('Abbreviation', size=10, required=True)
	name = fields.Char('Dosage unit', size=128, required=True)


	_sql_constraints = [('code_uniq', 'unique (code)', 'The Dose code must be unique')]



	@api.multi
	def name_get(self):
		res = []
		for record in self:
			name = record.name
			if record.code:
				name = record.code + ' - ' + name
			res.append((record.id, name))
		return res



doctor_dose_unit()


class doctor_administration_route(models.Model):
	_name = "doctor.administration.route"

	code = fields.Char('Code', size=10, required=True)
	name = fields.Char('Administration route', size=128, required=True)


	_sql_constraints = [('code_uniq', 'unique (code)', 'The Administration Route code must be unique')]


doctor_administration_route()


class doctor_measuring_unit(models.Model):
	_name = "doctor.measuring.unit"

	code = fields.Char('Code', size=10, required=True)
	name = fields.Char('Measuring unit', size=128, required=True)


	_sql_constraints = [('code_uniq', 'unique (code)', 'The Measuring unit code must be unique')]


doctor_measuring_unit()


class doctor_drugs(models.Model):
	_name = "doctor.drugs"
	_rec_name = 'atc_id'

	code = fields.Char('Code', size=10, required=True)
	atc_id = fields.Many2one('doctor.atc', 'ATC', required=True, ondelete='restrict')
	pharmaceutical_form = fields.Many2one('doctor.pharmaceutical.form', 'Pharmaceutical form', required=True,
										   ondelete='restrict')
	drugs_concentration = fields.Char('Drugs concentration', size=64, required=True)
	administration_route = fields.Many2one('doctor.administration.route', 'Administration route', required=True,
											ondelete='restrict')
	indication_drug = fields.Text('Indicaciones', size=300, help='Agregar indicaciones al medicamento')



	"""
	def name_get(self):
		if not len(ids):
			return []
		reads = self.read(self._ids,
						  ['atc_id', 'pharmaceutical_form', 'drugs_concentration', 'administration_route'], context)
		res = []
		for record in reads:
			name = record['atc_id'][1]
			if record['pharmaceutical_form'] and record['drugs_concentration'] and record['administration_route']:
				name = name + ' (' + record['drugs_concentration'] + ' - ' + record['pharmaceutical_form'][1] + ' - ' + \
					   record['administration_route'][1] + ')'
			res.append((record['id'], name))
		return res
	"""

doctor_drugs()


class doctor_atc(models.Model):
	_name = "doctor.atc"

	code = fields.Char('Code', size=7, required=True)
	name = fields.Char('Description', size=512, required=True)



	@api.multi
	def name_get(self):
		res = []
		for record in self:
			name = record.name
			if record.code:
				name = record.code + ' - ' + name
			res.append((record.id, name))
		return res

	"""
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
	"""

doctor_atc()


class doctor_diseases(models.Model):
	_name = "doctor.diseases"

	code = fields.Char('Code', size=4, required=True)
	name = fields.Char('Disease', size=256, required=True)

	_sql_constraints = [('code_uniq', 'unique (code)', 'The Medical Diseases code must be unique')]

	@api.multi
	def name_get(self):
		res = []

		for record in self:
			name = record.name
			if record.code:
				name = record.code + ' - ' + name
			res.append((record.id, name))
		return res

	"""
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
	"""

doctor_diseases()




