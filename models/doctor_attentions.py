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
from dateutil.relativedelta import *
from datetime import datetime, date
from odoo import models, fields, api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)



class doctor_attentions(models.Model):
    _name = "doctor.attentions"
    _rec_name = 'number'
    _order = "date_attention desc"

    """
    def create(self,vals):
        # Set appointment number if empty
        if not vals.get('number'):
            vals['number'] = self.pool.get('ir.sequence').get('attention.sequence')
        return super(doctor_attentions, self).create(vals, context=context)

    def button_closed(self, cr, uid, ids, context=None):
        ids_attention_past = self.pool.get('doctor.attentions.past').search(cr, uid, [('attentiont_id', '=', ids), ('past', '=', False)], context=context)
        self.pool.get('doctor.attentions.past').unlink(cr, uid, ids_attention_past, context)
        
        ids_review_system = self.pool.get('doctor.review.systems').search(cr, uid, [('attentiont_id', '=', ids), ('review_systems', '=', False)], context=context)
        self.pool.get('doctor.review.systems').unlink(cr, uid, ids_review_system, context)
        
        ids_examen_fisico = self.pool.get('doctor.attentions.exam').search(cr, uid, [('attentiont_id', '=', ids), ('exam', '=', False)], context=context)
        self.pool.get('doctor.attentions.exam').unlink(cr, uid, ids_examen_fisico, context)
        return super(doctor_attentions, self).write(cr, uid, ids, {'state':'closed'}, context=context)

   
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
    """
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

    """
    def _get_professional_id(self, cr, uid, user_id):
        try:
            professional_id= self.pool.get('doctor.professional').browse(cr, uid, self.pool.get('doctor.professional').search(cr, uid, [( 'user_id',  '=', uid)]))[0].id
            return professional_id
        except:
            return False
    """
    patient_id = fields.Many2one('doctor.patient', 'Patient', ondelete='restrict', readonly=True,
                                 default=lambda self, cr, uid, context: context.get('patient_id', False),)
    """
    patient_photo = fields.related('patient_id', 'photo', type="binary", relation="doctor.patient", readonly=True)
    """
    date_attention = fields.Datetime('Date of attention', required=True, readonly=True,
                                     default=lambda *a: datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"))
    number = fields.Char('Attention number', select=1, size=32, readonly=True,
                          help="Number of attention. Keep empty to get the number assigned by a sequence.")
    origin = fields.Char('Source Document', size=64,
                          help="Reference of the document that produced this attentiont.", readonly=True)
    age_attention = fields.Integer('Current age', readonly=True),
    age_unit = fields.Selection([('1', 'Years'), ('2', 'Months'), ('3', 'Days'), ], 'Unit of measure of age',
                                 readonly=True)
    age_patient_ymd = fields.Char('Age in Years, months and days', size=30, readonly=True)
    """
    professional_id = fields.Many2one('doctor.professional', 'Doctor', required=True, readonly=True,
                                      default= _get_professional_id if _get_professional_id != False else False)
    
    speciality = fields.related('professional_id', 'speciality_id', type="many2one", relation="doctor.speciality",
                                 string='Speciality', required=False, store=True,
                                 states={'closed': [('readonly', True)]})"""
    """
    professional_photo = fields.related('professional_id', 'photo', type="binary", relation="doctor.professional",
                                         readonly=True, store=False)"""
    """
    reason_consultation = fields.Many2many('doctor.diseases', id1='attention_id', id2='reason_consultation',
                                            string='Reason for consultation', required=False, ondelete='restrict',
                                            states={'closed': [('readonly', True)]})
                                            """
    actual_disease = fields.Text('Current disease', required=False, states={'closed': [('readonly', True)]})
    """
    review_systems_id = fields.One2many('doctor.review.systems', 'attentiont_id', 'Review of systems',
                                         ondelete='restrict', states={'closed': [('readonly', True)]})
    attentions_past_ids = fields.One2many('doctor.attentions.past', 'attentiont_id', 'Past', ondelete='restrict',
                                           states={'closed': [('readonly', True)]})
    past_ids = fields.Char(compute='_get_past', relation="doctor.attentions.past", type="one2many", store=False,
                            readonly=True, method=True, string="Old Past")
    pathological_past = fields.One2many('doctor.diseases.past', 'attentiont_id', 'Pathological past',
                                         ondelete='restrict', states={'closed': [('readonly', True)]})
    pathological_past_ids = fields.Char(compute='_get_pathological_past', relation="doctor.diseases.past",
                                         type="one2many", store=False, readonly=True, method=True,
                                         string="Old Pathological Past")
    drugs_past = fields.One2many('doctor.atc.past', 'attentiont_id', 'Drugs past', ondelete='restrict',
                                  states={'closed': [('readonly', True)]})
    
    drugs_past_ids = fields.Char(compute='_get_drugs_past', relation="doctor.atc.past", type="one2many", store=False,
                                  readonly=True, method=True, string="Old drugs Past")
    """
    weight = fields.Float('Weight (kg)', states={'closed': [('readonly', True)]})
    height = fields.Float('Height (cm)', states={'closed': [('readonly', True)]})
    body_mass_index = fields.Float('Body Mass Index', states={'closed': [('readonly', True)]})

    heart_rate = fields.Integer('Heart Rate', help="Heart rate expressed in beats per minute",
                                 states={'closed': [('readonly', True)]})
    respiratory_rate = fields.Integer('Respiratory Rate', help="Respiratory rate expressed in breaths per minute",
                                       states={'closed': [('readonly', True)]})
    systolic = fields.Integer('Systolic Pressure', states={'closed': [('readonly', True)]})
    diastolic = fields.Integer('Diastolic Pressure', states={'closed': [('readonly', True)]})
    temperature = fields.Float('Temperature (celsius)', states={'closed': [('readonly', True)]})
    pulsioximetry = fields.Integer('Oxygen Saturation', help="Oxygen Saturation (arterial).",
                                    states={'closed': [('readonly', True)]})
    """
    attentions_exam_ids = fields.One2many('doctor.attentions.exam', 'attentiont_id', 'Exam', ondelete='restrict',
                                           states={'closed': [('readonly', True)]})
    analysis = fields.Text('Analysis', required=False, states={'closed': [('readonly', True)]})
    conduct = fields.Text('Conduct', required=False, states={'closed': [('readonly', True)]})
    diseases_ids = fields.One2many('doctor.attentions.diseases', 'attentiont_id', 'Diseases', ondelete='restrict',
                                    states={'closed': [('readonly', True)]})
    drugs_ids = fields.One2many('doctor.prescription', 'attentiont_id', 'Drugs prescription', ondelete='restrict',
                                 states={'closed': [('readonly', True)]})
    diagnostic_images_ids = fields.One2many('doctor.attentions.procedures', 'attentiont_id', 'Diagnostic Images',
                                             ondelete='restrict', states={'closed': [('readonly', True)]},
                                             domain=[('procedures_id.procedure_type', '=', 3)])
    clinical_laboratory_ids = fields.One2many('doctor.attentions.procedures', 'attentiont_id',
                                               'Clinical Laboratory', ondelete='restrict',
                                               states={'closed': [('readonly', True)]},
                                               domain=[('procedures_id.procedure_type', '=', 4)])
    surgical_procedure_ids = fields.One2many('doctor.attentions.procedures', 'attentiont_id', 'Surgical Procedure',
                                              ondelete='restrict', states={'closed': [('readonly', True)]},
                                              domain=[('procedures_id.procedure_type', '=', 2)])
    therapeutic_procedure_ids = fields.One2many('doctor.attentions.procedures', 'attentiont_id',
                                                'Therapeutic Procedure', ondelete='restrict',
                                                 states={'closed': [('readonly', True)]},
                                                 domain=[('procedures_id.procedure_type', '=', 5)])
    other_procedure_ids = fields.One2many('doctor.attentions.procedures', 'attentiont_id', 'Other Procedure',
                                           ondelete='restrict', states={'closed': [('readonly', True)]},
                                           domain=['|', ('procedures_id.procedure_type', '=', 1), '|',
                                                   ('procedures_id.procedure_type', '=', 6),
                                                   ('procedures_id.procedure_type', '=', 7)])
    referral_ids = fields.One2many('doctor.attentions.referral', 'attentiont_id', 'Referral', ondelete='restrict',
                                    states={'closed': [('readonly', True)]})
                                    """
    disability_ids = fields.One2many('doctor.attentions.disability', 'attentiont_id', 'Disability',
                                      ondelete='restrict', states={'closed': [('readonly', True)]})

    state = fields.Selection([('open', 'Open'), ('closed', 'Closed')], 'Status', readonly=True, required=True, default='open')
    tipo_historia = fields.Char('tipo_historia', required=True, default='hc_general')


    '''
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
        if professional_data.speciality_id.id:
            professional_speciality = professional_data.speciality_id.id
            values.update({
                'speciality': professional_speciality,
            })

        values.update({
            'professional_photo': professional_img,
        })
        _logger.info(values)
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

        values.update({
            'patient_photo': photo_patient,
            'past_ids': past,
            'pathological_past_ids': phatological_past,
            'drugs_past_ids': drugs_past,
        })
        return {'value': values}

    '''
    def calcular_edad(self,fecha_nacimiento):
        current_date = datetime.today()
        st_birth_date = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
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

        elif age >= 365:
            age = int((current_date.year-st_birth_date.year-1) + (1 if (current_date.month, current_date.day) >= (st_birth_date.month, st_birth_date.day) else 0))
            age_attention = age,
            age_unit = '1'
        
        return age

    #it allows to return the patient's age in years, months, days e.g  24 years, 8 months, 3 days. -C
    def calcular_edad_ymd(self,fecha_nacimiento):
        today = date.today()
        age = relativedelta(today, datetime.strptime(fecha_nacimiento, '%Y-%m-%d'))
        age_ymd= str(age.years)+' Años, '+str(age.months)+' Meses,'+str(age.days)+' Días'
        return age_ymd

    def calcular_age_unit(self,fecha_nacimiento):
        current_date = datetime.today()
        st_birth_date = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        re = current_date - st_birth_date
        dif_days = re.days
        age = dif_days
        age_unit = ''
        if age < 30:
            age_unit = '3'
        elif age > 30 and age < 365:
            age_unit = '2'

        elif age >= 365:
            age_unit = '1'

        return age_unit


    def default_get(self, cr, uid, fields, context=None):
        res = super(doctor_attentions,self).default_get(cr, uid, fields, context=context)

        modelo_permisos = self.pool.get('res.groups')
        nombre_permisos = []
        cr.execute("SELECT gid FROM res_groups_users_rel WHERE uid = %s" %(uid))

        for i in cr.fetchall():
            grupo_id = modelo_permisos.browse(cr, uid, i[0], context=context).name
            nombre_permisos.append(grupo_id)


        if context.get('active_model') == "doctor.patient":
            id_paciente = context.get('default_patient_id')
        else:
            id_paciente = context.get('patient_id')

        if id_paciente:    
            fecha_nacimiento = self.pool.get('doctor.patient').browse(cr,uid,id_paciente,context=context).birth_date
            res['age_patient_ymd'] = self.calcular_edad_ymd(fecha_nacimiento)
            res['age_attention'] = self.calcular_edad(fecha_nacimiento)
            res['age_unit'] = self.calcular_age_unit(fecha_nacimiento)

        return res




doctor_attentions()


class doctor_attentions_past(models.Model):
    _name = "doctor.attentions.past"
    _rec_name = 'attentiont_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention', ondelete='restrict')
    patient_id = fields.Many2one('doctor.patient', 'Patient', ondelete='restrict',
                                  default=lambda self, cr, uid, context: context.get('patient_id', False) )
    past_category = fields.Many2one('doctor.past.category', 'Past category', required=True, ondelete='restrict')
    past = fields.Text('Past', required=True)

    '''
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'attentiont_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res
    '''

doctor_attentions_past()


class doctor_attentions_exam(models.Model):
    _name = "doctor.attentions.exam"
    _rec_name = 'attentiont_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention')
    exam_category = fields.Many2one('doctor.exam.category', 'Exam category', required=True, ondelete='restrict')
    exam = fields.Text('Exam', required=True)

    '''
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'attentiont_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res
    '''

doctor_attentions_exam()


class doctor_attentions_diseases(models.Model):
    _name = "doctor.attentions.diseases"
    _rec_name = 'diseases_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention')
    diseases_id = fields.Many2one('doctor.diseases', 'Disease', required=True, ondelete='restrict')
    status = fields.Selection([
        ('presumptive', 'Presumptive'),
        ('confirm', 'Confirmed'),
        ('recurrent', 'Recurrent')],
        'Status', required=True, default='presumptive')
    diseases_type = fields.Selection([
        ('main', 'Main'),
        ('related', 'Related')],
        'Type', required=True,default='main')

    '''
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'diseases_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res
    '''

doctor_attentions_diseases()


class doctor_attentions_procedures(models.Model):
    _name = "doctor.attentions.procedures"
    _rec_name = 'procedures_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention')
    procedures_id = fields.Many2one('product.product', 'Health Procedures', required=True, ondelete='restrict')
    quantity = fields.Integer('Quantity', required=True, default=1)
    indications = fields.Char('Indications', size=256)

    '''
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'procedures_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res
    '''


doctor_attentions_procedures()


class doctor_attentions_referral(models.Model):
    _name = "doctor.attentions.referral"
    _rec_name = 'referral_ids'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention')
    referral_ids = fields.Selection([
        ('consult', 'Consultation'),
        ('urgency', 'Urgency'),
        ('hospital', 'Hospitalization'), ],
        'Service', required=True)
    speciality_id = fields.Many2one('doctor.speciality', 'Speciality', required=True, ondelete='restrict')
    interconsultation = fields.Boolean('Is interconsultation?')
    cause = fields.Text('Referral cause', required=True)
    '''
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'referral_ids'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res
    '''

doctor_attentions_referral()


class doctor_attentions_disability(models.Model):
    _name = "doctor.attentions.disability"
    _rec_name = 'disability_ids'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention')
    disability_ids = fields.Date('Start date', required=True, ondelete='restrict')
    duration = fields.Integer('Duration', required=True)
    '''

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        rec_name = 'disability_ids'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(cr, uid, ids, [rec_name], context)]
        return res
    '''
doctor_attentions_disability()


# datos de doctor.py

class doctor_review_systems(models.Model):
    _name = "doctor.review.systems"
    _rec_name = 'attentiont_id'

    attentiont_id = fields.Many2one('doctor.attentions', 'Attention')
    system_category = fields.Many2one('doctor.systems.category', 'Systems category', required=True,
                                      ondelete='restrict')
    review_systems = fields.Text('Review systems', required=True)

    @api.multi
    def name_get(self):
        if not len(self._ids):
            return []
        rec_name = 'attentiont_id'
        res = [(r['id'], r[rec_name][1])
               for r in self.read(self._cr, self._uid, self._ids, [rec_name], context)]
        return res


doctor_review_systems()


class doctor_systems_category(models.Model):


    @api.multi
    @api.depends('name', 'parent_id')
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.parent_id:
                _logger.info('recordparent')
                _logger.info(record.parent_id)
                name = record.parent_id.name + ' /' + name
            res.append((record.id, name))
        return res

    """
    @api.multi
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if not self._context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            ids = self.search(self._cr, self._uid, [('name', operator, name)] + args, limit=limit, context=self._context)
        else:
            ids = self.search(self._cr, self._uid, limit=limit)
        return self.name_get(self._cr, self._uid, self._ids)
    """


    @api.depends('pagos_ids.quantity', 'precio_a_pagar_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            valor_cuota_paga = amount_tax = 0.0
            a_pagar = 0.00
            cuotas_pagas = 0.00
            cuotas_por_pagar = 0.00
            for line in order.pagos_ids:
                valor_cuota_paga += line.quantity
            a_pagar = order.precio_a_pagar_total - valor_cuota_paga
            cuotas_pagas = order.precio_a_pagar_total
            if cuotas_pagas != 0:
                cuotas_pagas = (valor_cuota_paga * order.cantidad_cuotas) / order.precio_a_pagar_total
                cuotas_por_pagar = order.cantidad_cuotas - cuotas_pagas

            # aqui pondremos las cuotas cuotas_pagas_al_dia
            numero = str(cuotas_pagas)
            arr = numero.split(".")
            entero = int(arr[0])
            decimal = arr[1]
            decimal_concat = '0.' + decimal
            decimal_float = float(decimal_concat)
            mas = int(valor_cuota_paga - (order.valor_cuota * entero))
            # mas = Math.floor(price_total - (valor_cuota * entero));
            if (mas > 0.0):
                cuotas_pagas_al_dia = str(entero) + ' + ' + str(mas)
            else:
                cuotas_pagas_al_dia = str(entero)

            # aqui pondremos las cuotas cuotas_porpagar_al_dia

            numero2 = str(cuotas_por_pagar)
            arr2 = numero2.split(".")
            entero2 = int(arr2[0])
            decimal2 = arr2[1]
            decimal_concat2 = '0.' + decimal2
            decimal_float = float(decimal_concat2)
            mas2 = int(a_pagar - (order.valor_cuota * entero2))
            if (mas2 > 0.0):
                cuotas_porpagar_al_dia = str(entero2) + ' + ' + str(mas2)
            else:
                cuotas_porpagar_al_dia = str(entero2)

            # termina

            order.update({
                'price_total': valor_cuota_paga,
                'por_pagar': a_pagar,
                'cuotas_pagas_total': cuotas_pagas,
                'cuotas_por_pagar_total': cuotas_por_pagar,
                'cuotas_pagas_al_dia': cuotas_pagas_al_dia,
                'cuotas_porpagar_al_dia': cuotas_porpagar_al_dia,
            })

    @api.one
    def _name_get_fnc(self):
        res = self.name_get()
        for datos in res:

                _logger.info('entro fnc')
                _logger.info('entro fnc')
                _logger.info('entro fnc')
                _logger.info('entro fnc')
                _logger.info(res)
                self.complete_name =datos[1]
        #return 'asdasd'

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

    _constraints = [
        (models.Model._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]

    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'


doctor_systems_category()


class doctor_past_category(models.Model):
    '''


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


    '''

    @api.multi
    @api.depends('name', 'parent_id')
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.parent_id:
                _logger.info('recordparent')
                _logger.info(record.parent_id)
                name = record.parent_id.name + ' /' + name
            res.append((record.id, name))
        return res


    @api.one
    def _name_get_fnc(self):
        res = self.name_get()
        for datos in res:
            _logger.info('entro fnc')
            _logger.info('entro fnc')
            _logger.info('entro fnc')
            _logger.info('entro fnc')
            _logger.info(res)
            self.complete_name = datos[1]
        # return 'asdasd'


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



    _constraints = [
        (models.Model._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]


    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'


doctor_past_category()



class doctor_exam_category(models.Model):
    '''


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

    '''

    @api.multi
    @api.depends('name', 'parent_id')
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.parent_id:
                _logger.info('recordparent')
                _logger.info(record.parent_id)
                name = record.parent_id.name + ' /' + name
            res.append((record.id, name))
        return res

    @api.one
    def _name_get_fnc(self):
        res = self.name_get()
        for datos in res:
            _logger.info('entro fnc')
            _logger.info('entro fnc')
            _logger.info('entro fnc')
            _logger.info('entro fnc')
            _logger.info(res)
            self.complete_name = datos[1]
        # return 'asdasd'



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


    _constraints = [
        (models.Model._check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]



    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'


doctor_exam_category()




class doctor_health_procedures(models.Model):
    _inherit = "product.product"


    """
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
    """
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


