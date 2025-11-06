# -*- coding: utf-8 -*-
"""This file defines the Medical Diagnosis model."""

from odoo import models, fields, api
from odoo.exceptions import UserError


class MedicalDiagnosis(models.Model):
    """Model for storing medical diagnoses linked to a patient visit."""
    _name = 'medical.diagnosis'
    _description = 'Medical Diagnosis'
    _rec_name = 'disease_id'

    visit_id = fields.Many2one(
        comodel_name='hr.hospital.patient.visit',
        string='Patient Visit',
        ondelete='restrict',
        domain="["
               "('status', '=', 'completed'),"
               "('visit_date', '>=', (context_today() - "
               "relativedelta(days=30)).strftime('%Y-%m-%d 00:00:00'))"
               "]",
        help="Показує лише завершені візити за останні 30 днів."
    )
    disease_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Disease',
        domain="[('is_contagious', '=', True), ('danger_level', 'in', ['high', 'critical'])]"
    )
    description = fields.Text(string='Diagnosis Description')
    treatment = fields.Html(string='Assigned Treatment')
    is_approved = fields.Boolean(default=False)
    approving_doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Approved by Doctor',
        readonly=True
    )
    approval_date = fields.Datetime(readonly=True)
    severity = fields.Selection(
        selection=[
            ('low', 'Легкий'),
            ('medium', 'Середній'),
            ('high', 'Високий'),
            ('severe', 'Тяжкий'),
            ('critical', 'Критичний')
        ],
        default='medium'
    )

    # Поля для Pivot/Graph
    disease_type_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Disease Type',
        related='disease_id.parent_id',
        store=True
    )
    visit_date = fields.Datetime(
        string='Visit Date',
        related='visit_id.visit_date',
        store=True
    )

    @api.constrains('approval_date', 'visit_id.visit_date')
    def _check_approval_date(self):
        """Validator: Approval date cannot be earlier than the visit date."""
        for record in self:
            if record.approval_date and record.visit_id.visit_date and \
                    record.approval_date < record.visit_id.visit_date:
                raise UserError(self.env._("Approval date cannot be earlier than "
                                  "the visit date."))

    def action_approve_diagnosis(self):
        """Business Logic: Approves the diagnosis."""
        current_doctor = self.env['hr.hospital.doctor'].search([
            ('user_id', '=', self.env.uid)
        ], limit=1)

        if not current_doctor:
            raise UserError(self.env._("Ви не можете затверджувати діагнози, "
                              "оскільки ваш користувач не прив'язаний до профілю лікаря."))

        for record in self:
            if not record.visit_id:
                raise UserError(self.env._("Неможливо затвердити діагноз без візиту."))

            intern_doctor = record.visit_id.doctor_id

            if intern_doctor and intern_doctor.is_intern:

                if intern_doctor.mentor_id != current_doctor:
                    raise UserError(self.env._("Тільки призначений ментор (%s) "
                                      "може затвердити цей діагноз інтерна.",
                                      intern_doctor.mentor_id.full_name))

            record.write({
                'is_approved': True,
                'approving_doctor_id': current_doctor.id,
                'approval_date': fields.Datetime.now(),
            })
        return True
