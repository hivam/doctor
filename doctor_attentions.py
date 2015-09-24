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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _


class doctor_attentions(osv.osv):
    _name = "doctor.attentions"
    _rec_name = 'number'
    _order = "date_attention desc"

    external_cause = [
        ('01','Accidente de trabajo'),
        ('02',u'Accidente de tránsito'),
        ('03',u'Accidente rábico'),
        ('04',u'Accidente ofídico'),
        ('05','Otro tipo de accidente'),
        ('06',u'Evento Catastrófico'),
        ('07',u'Lesión por agresión'),
        ('08',u'Lesión auto infligida'),
        ('09',u'Sospecha de maltrato físico'),
        ('10','Sospecha de abuso sexual'),
        ('11','Sospecha de violencia sexual'),
        ('12','Sospecha de maltrato emocional'),
        ('13','Enfermedad general'),
        ('14','Enfermedad profesional'),
        ('15','Otra'),
    ]

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
            condition.append(('attentiont_id', '<=', attentiont_id))
        if type_past == 'past':
            return self.pool.get('doctor.attentions.past').search(cr, uid, condition, order='id desc')
        if type_past == 'pathological':
            return self.pool.get('doctor.diseases.past').search(cr, uid, condition, order='id desc')
        if type_past == 'drugs':
            return self.pool.get('doctor.atc.past').search(cr, uid, condition, order='id desc')

    def _get_past(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for datos in self.browse(cr, uid, ids):
            res[datos.id] = self._previous(cr, uid, datos.patient_id, 'past', datos.id)
        return res

    def _get_pathological_past(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for datos in self.browse(cr, uid, ids):
            res[datos.id] = self._previous(cr, uid, datos.patient_id, 'pathological', datos.id)
        return res

    def _get_drugs_past(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for datos in self.browse(cr, uid, ids):
            res[datos.id] = self._previous(cr, uid, datos.patient_id, 'drugs', datos.id)
        return res

    _columns = {
        'patient_id': fields.many2one('doctor.patient', 'Patient', ondelete='restrict', readonly=True),
        'patient_photo': fields.related('patient_id', 'photo', type="binary", relation="doctor.patient", readonly=True),
        'date_attention': fields.datetime('Date of attention', required=True, readonly=True),
        'number': fields.char('Attention number', select=1, size=32, readonly=True,
                              help="Number of attention. Keep empty to get the number assigned by a sequence."),
        'origin': fields.char('Source Document', size=64,
                              help="Reference of the document that produced this attentiont.", readonly=True),
        'age_attention': fields.integer('Current age', readonly=True),
        'age_unit': fields.selection([('1', 'Years'), ('2', 'Months'), ('3', 'Days'), ], 'Unit of measure of age',
                                     readonly=True),
        'professional_id': fields.many2one('doctor.professional', 'Doctor', required=True, readonly=True),
        'speciality': fields.related('professional_id', 'speciality_id', type="many2one", relation="doctor.speciality",
                                     string='Speciality', required=True, store=True,
                                     states={'closed': [('readonly', True)]}),
        'professional_photo': fields.related('professional_id', 'photo', type="binary", relation="doctor.professional",
                                             readonly=True, store=False),
        'reason_consultation': fields.many2many('doctor.diseases', id1='attention_id', id2='reason_consultation',
                                                string='Reason for consultation', required=False, ondelete='restrict',
                                                states={'closed': [('readonly', True)]}),
        'actual_disease': fields.text('Current disease', required=False, states={'closed': [('readonly', True)]}),
        'review_systems_id': fields.one2many('doctor.review.systems', 'attentiont_id', 'Review of systems',
                                             ondelete='restrict', states={'closed': [('readonly', True)]}),
        'attentions_past_ids': fields.one2many('doctor.attentions.past', 'attentiont_id', 'Past', ondelete='restrict',
                                               states={'closed': [('readonly', True)]}),
        'past_ids': fields.function(_get_past, relation="doctor.attentions.past", type="one2many", store=False,
                                    readonly=True, method=True, string="Old Past"),
        'pathological_past': fields.one2many('doctor.diseases.past', 'attentiont_id', 'Pathological past',
                                             ondelete='restrict', states={'closed': [('readonly', True)]}),
        'pathological_past_ids': fields.function(_get_pathological_past, relation="doctor.diseases.past",
                                                 type="one2many", store=False, readonly=True, method=True,
                                                 string="Old Pathological Past"),
        'drugs_past': fields.one2many('doctor.atc.past', 'attentiont_id', 'Drugs past', ondelete='restrict',
                                      states={'closed': [('readonly', True)]}),
        'drugs_past_ids': fields.function(_get_drugs_past, relation="doctor.atc.past", type="one2many", store=False,
                                          readonly=True, method=True, string="Old drugs Past"),
        'weight': fields.float('Weight (kg)', states={'closed': [('readonly', True)]}),
        'height': fields.float('Height (cm)', states={'closed': [('readonly', True)]}),
        'body_mass_index': fields.float('Body Mass Index', states={'closed': [('readonly', True)]}),
        'heart_rate': fields.integer('Heart Rate', help="Heart rate expressed in beats per minute",
                                     states={'closed': [('readonly', True)]}),
        'respiratory_rate': fields.integer('Respiratory Rate', help="Respiratory rate expressed in breaths per minute",
                                           states={'closed': [('readonly', True)]}),
        'systolic': fields.integer('Systolic Pressure', states={'closed': [('readonly', True)]}),
        'diastolic': fields.integer('Diastolic Pressure', states={'closed': [('readonly', True)]}),
        'temperature': fields.float('Temperature (celsius)', states={'closed': [('readonly', True)]}),
        'pulsioximetry': fields.integer('Oxygen Saturation', help="Oxygen Saturation (arterial).",
                                        states={'closed': [('readonly', True)]}),
        'attentions_exam_ids': fields.one2many('doctor.attentions.exam', 'attentiont_id', 'Exam', ondelete='restrict',
                                               states={'closed': [('readonly', True)]}),
        'analysis': fields.text('Analysis', required=False, states={'closed': [('readonly', True)]}),
        'conduct': fields.text('Conduct', required=False, states={'closed': [('readonly', True)]}),
        'diseases_ids': fields.one2many('doctor.attentions.diseases', 'attentiont_id', 'Diseases', ondelete='restrict',
                                        states={'closed': [('readonly', True)]}),
        'drugs_ids': fields.one2many('doctor.prescription', 'attentiont_id', 'Drugs prescription', ondelete='restrict',
                                     states={'closed': [('readonly', True)]}),
        'diagnostic_images_ids': fields.one2many('doctor.attentions.procedures', 'attentiont_id', 'Diagnostic Images',
                                                 ondelete='restrict', states={'closed': [('readonly', True)]},
                                                 domain=[('procedures_id.procedure_type', '=', 3)]),
        'clinical_laboratory_ids': fields.one2many('doctor.attentions.procedures', 'attentiont_id',
                                                   'Clinical Laboratory', ondelete='restrict',
                                                   states={'closed': [('readonly', True)]},
                                                   domain=[('procedures_id.procedure_type', '=', 4)]),
        'surgical_procedure_ids': fields.one2many('doctor.attentions.procedures', 'attentiont_id', 'Surgical Procedure',
                                                  ondelete='restrict', states={'closed': [('readonly', True)]},
                                                  domain=[('procedures_id.procedure_type', '=', 2)]),
        'therapeutic_procedure_ids': fields.one2many('doctor.attentions.procedures', 'attentiont_id',
                                                     'Therapeutic Procedure', ondelete='restrict',
                                                     states={'closed': [('readonly', True)]},
                                                     domain=[('procedures_id.procedure_type', '=', 5)]),
        'other_procedure_ids': fields.one2many('doctor.attentions.procedures', 'attentiont_id', 'Other Procedure',
                                               ondelete='restrict', states={'closed': [('readonly', True)]},
                                               domain=['|', ('procedures_id.procedure_type', '=', 1), '|',
                                                       ('procedures_id.procedure_type', '=', 6),
                                                       ('procedures_id.procedure_type', '=', 7)]),
        'referral_ids': fields.one2many('doctor.attentions.referral', 'attentiont_id', 'Referral', ondelete='restrict',
                                        states={'closed': [('readonly', True)]}),
        'disability_ids': fields.one2many('doctor.attentions.disability', 'attentiont_id', 'Disability',
                                          ondelete='restrict', states={'closed': [('readonly', True)]}),
        'state': fields.selection([('open', 'Open'), ('closed', 'Closed')], 'Status', readonly=True, required=True),
        
   
        'external_cause': fields.selection(external_cause, 'Causa Externa'),

    }

    def action_next(self, cr, uid, ids, context=None):
        for record in self.browse(cr,uid,ids,context=context):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mail.compose.message',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(False, 'form')],
                'target': 'new',
                'context':  {
                        'default_patient_id' : record.patient_id.id,
                        'default_professional_id' : record.professional_id.id,
                    },
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
            'professional_photo': professional_img,
            'speciality': professional_speciality,
        })
        return {'value': values}

    def onchange_patient(self, cr, uid, ids, patient_id, context=None):
        values = {}
        if not patient_id:
            return values
        past = self.pool.get('doctor.attentions.past').search(cr, uid, [('patient_id', '=', patient_id)],
                                                              order='id asc')
        phatological_past = self.pool.get('doctor.diseases.past').search(cr, uid, [('patient_id', '=', patient_id)],
                                                                         order='id asc')
        drugs_past = self.pool.get('doctor.atc.past').search(cr, uid, [('patient_id', '=', patient_id)], order='id asc')
        patient_data = self.pool.get('doctor.patient').browse(cr, uid, patient_id, context=context)
        photo_patient = patient_data.photo
        patient_birth_date = patient_data.birth_date
        current_date = datetime.today()
        st_birth_date = datetime.strptime(patient_birth_date, '%Y-%m-%d')
        re = current_date - st_birth_date
        dif_days = re.days
        age = dif_days
        age_unit = ''
        if age < 30:
            age_attention = age,
            age_unit = '3'

        elif age > 30 and age < 365:
            age = age / 30
            age = int(age)
            age_attention = age,
            age_unit = '2'

        elif age > 365:
            age = age / 365
            age = int(age)
            age_attention = age,
            age_unit = '1'

        values.update({
            'patient_photo': photo_patient,
            'age_attention': age,
            'age_unit': age_unit,
            'past_ids': past,
            'pathological_past_ids': phatological_past,
            'drugs_past_ids': drugs_past,
        })
        return {'value': values}

    def _get_professional_id(self, cr, uid, user_id):
        try:
            professional_id= self.pool.get('doctor.professional').browse(cr, uid, self.pool.get('doctor.professional').search(cr, uid, [( 'user_id',  '=', uid)]))[0].id
        except Exception as e:
            raise osv.except_osv(_('Error!'),
                                 _('El usuario del sistema no es profesional de la salud.'))

    _defaults = {
        'patient_id': lambda self, cr, uid, context: context.get('patient_id', False),
        'date_attention': lambda *a: datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        'professional_id': _get_professional_id,
        'state': 'open',
    }


doctor_attentions()

class wizzard(osv.osv):

    _name = "mail.compose.message"

    _inherit = 'mail.compose.message'

    _columns = {
        'attentiont_id': fields.many2one('doctor.attentions', 'Attention', ondelete='restrict'),
        'patient_id': fields.many2one('doctor.patient', 'Patient', ondelete='restrict'),
        'professional_id': fields.many2one('doctor.professional', 'Doctor'),
    }


wizzard()

class doctor_attentions_past(osv.osv):
    _name = "doctor.attentions.past"
    _rec_name = 'attentiont_id'
    _columns = {
        'attentiont_id': fields.many2one('doctor.attentions', 'Attention', ondelete='restrict'),
        'patient_id': fields.many2one('doctor.patient', 'Patient', required=True, ondelete='restrict'),
        'past_category': fields.many2one('doctor.past.category', 'Past category', required=True, ondelete='restrict'),
        'past': fields.text('Past', required=True),
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


doctor_attentions_past()


class doctor_attentions_exam(osv.osv):
    _name = "doctor.attentions.exam"
    _rec_name = 'attentiont_id'
    _columns = {
        'attentiont_id': fields.many2one('doctor.attentions', 'Attention'),
        'exam_category': fields.many2one('doctor.exam.category', 'Exam category', required=True, ondelete='restrict'),
        'exam': fields.text('Exam', required=True),
    }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'attentiont_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res


doctor_attentions_exam()


class doctor_attentions_diseases(osv.osv):
    _name = "doctor.attentions.diseases"
    _rec_name = 'diseases_id'
    _columns = {
        'attentiont_id': fields.many2one('doctor.attentions', 'Attention'),
        'diseases_id': fields.many2one('doctor.diseases', 'Disease', required=True, ondelete='restrict'),
        'status': fields.selection([
                                       ('presumptive', 'Presumptive'),
                                       ('confirm', 'Confirmed'),
                                       ('recurrent', 'Recurrent')],
                                   'Status', required=True),
        'diseases_type': fields.selection([
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


doctor_attentions_diseases()


class doctor_attentions_procedures(osv.osv):
    _name = "doctor.attentions.procedures"
    _rec_name = 'procedures_id'
    _columns = {
        'attentiont_id': fields.many2one('doctor.attentions', 'Attention'),
        'procedures_id': fields.many2one('product.product', 'Health Procedures', required=True, ondelete='restrict'),
        'quantity': fields.integer('Quantity', required=True),
        'indications': fields.char('Indications', size=256),
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


doctor_attentions_procedures()


class doctor_attentions_referral(osv.osv):
    _name = "doctor.attentions.referral"
    _rec_name = 'referral_ids'
    _columns = {
        'attentiont_id': fields.many2one('doctor.attentions', 'Attention'),
        'referral_ids': fields.selection([
                                             ('consult', 'Consultation'),
                                             ('urgency', 'Urgency'),
                                             ('hospital', 'Hospitalization'), ],
                                         'Service', required=True),
        'speciality_id': fields.many2one('doctor.speciality', 'Speciality', required=True, ondelete='restrict'),
        'interconsultation': fields.boolean('Is interconsultation?'),
        'cause': fields.text('Referral cause', required=True),
    }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'referral_ids'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res


doctor_attentions_referral()


class doctor_attentions_disability(osv.osv):
    _name = "doctor.attentions.disability"
    _rec_name = 'disability_ids'
    _columns = {
        'attentiont_id': fields.many2one('doctor.attentions', 'Attention'),
        'disability_ids': fields.date('Start date', required=True, ondelete='restrict'),
        'duration': fields.integer('Duration', required=True),
    }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'disability_ids'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res


doctor_attentions_disability()
