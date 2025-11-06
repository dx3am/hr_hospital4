# -*- coding: utf-8 -*-
"""This file defines the Patient model."""

from odoo import models, fields, api


class Patient(models.Model):
    """Model for storing patient records."""
    _name = 'hr.hospital.patient'
    _inherit = ['abstract.person']  # Наслідування абстрактної моделі
    _description = 'Patient'
    _rec_name = 'full_name'

    personal_doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Attending Doctor'
    )
    passport_data = fields.Char(size=10)
    contact_person_id = fields.Many2one(
        comodel_name='contact.person',
        string='Contact Person'
    )
    blood_type = fields.Selection(
        selection=[
            ('o_neg', 'O(I) Rh-'), ('o_pos', 'O(I) Rh+'),
            ('a_neg', 'A(II) Rh-'), ('a_pos', 'A(II) Rh+'),
            ('b_neg', 'B(III) Rh-'), ('b_pos', 'B(III) Rh+'),
            ('ab_neg', 'AB(IV) Rh-'), ('ab_pos', 'AB(IV) Rh+')
        ]
    )
    allergies = fields.Text()
    insurance_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Insurance Company',
        domain="[('is_company', '=', True)]"  # Домен (фільтр)
    )
    insurance_policy_number = fields.Char()

    history_ids = fields.One2many(  # Зв'язок One2many
        comodel_name='patient.doctor.history',
        inverse_name='patient_id',
        string='Doctor History'
    )

    visit_ids = fields.One2many(
        comodel_name='hr.hospital.patient.visit',
        inverse_name='patient_id',
    )
    visit_count = fields.Integer(
        compute='_compute_visit_count',
    )
    diagnosis_ids = fields.One2many(
        comodel_name='medical.diagnosis',
        compute='_compute_diagnosis_ids',
        string='All Diagnoses',
        readonly=True
    )

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        """Computes the number of visits."""
        for patient in self:
            patient.visit_count = len(patient.visit_ids)

    @api.depends('visit_ids.diagnosis_ids')
    def _compute_diagnosis_ids(self):
        """Gathers all diagnoses from all visits."""
        for patient in self:
            # Mapped() збирає всі diagnosis_ids з усіх візитів
            patient.diagnosis_ids = patient.visit_ids.mapped('diagnosis_ids')

    def action_open_patient_visits(self):
        """Smart button action to open patient's visits."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Patient Visits'),
            'res_model': 'hr.hospital.patient.visit',
            'view_mode': 'tree,form,calendar',
            'domain': [('patient_id', '=', self.id)],
            'context': {
                'default_patient_id': self.id
            }
        }

    def action_create_new_visit(self):
        """Button action to create a new visit."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('New Visit'),
            'res_model': 'hr.hospital.patient.visit',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_id': self.id,
                'default_doctor_id': self.personal_doctor_id.id,
            }
        }

    @api.onchange('allergies')  # Onchange
    def _onchange_allergies_warning(self):
        """Shows a warning if allergies are noted."""
        if self.allergies:
            return {
                'warning': {
                    'title': self.env._("Allergy Alert"),
                    'message': self.env._(
                        "This patient has known allergies: %s",
                        self.allergies
                    ),
                }
            }
        return {}

    @api.model_create_multi  # Override
    def create(self, vals_list):
        """Overrides create to automatically create a doctor history record."""
        records = super().create(vals_list)
        history_env = self.env['patient.doctor.history']
        for record in records:
            if record.personal_doctor_id:
                history_env.create({
                    'patient_id': record.id,
                    'doctor_id': record.personal_doctor_id.id,
                    'change_reason': self.env._('Initial assignment.'),
                })
        return records

    def write(self, vals):  # Override
        """Overrides write to create history when personal_doctor_id changes."""
        if 'personal_doctor_id' in vals:
            history_vals_list = []
            for record in self:
                # Перевірка, чи ID дійсно змінюється
                if record.personal_doctor_id.id != vals['personal_doctor_id']:
                    history_vals_list.append({
                        'patient_id': record.id,
                        'doctor_id': vals['personal_doctor_id'],
                        'change_reason': self.env._('Doctor changed by user.'),
                    })

        result = super().write(vals)

        if 'personal_doctor_id' in vals and history_vals_list:
            self.env['patient.doctor.history'].create(
                history_vals_list
            )

        return result
