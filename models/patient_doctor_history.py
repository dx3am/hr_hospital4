# -*- coding: utf-8 -*-
"""This file defines the Patient Doctor History model."""

from odoo import models, fields, api


class PatientDoctorHistory(models.Model):
    """Model for storing patient's doctor assignment history."""
    _name = 'patient.doctor.history'
    _description = 'Patient Doctor History'
    _order = 'assign_date desc'

    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
        required=True
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Doctor',
        required=True
    )
    assign_date = fields.Date(
        required=True,
        default=fields.Date.today  # Дефолт = сьогодні
    )
    end_date = fields.Date()
    change_reason = fields.Text()
    active = fields.Boolean(default=True)

    def action_archive_old_records(self):
        """
        Archives all other active history records for the patient(s).
        Called by 'patient.py' on write/create.
        """
        for record in self:
            # Знайти всі 'старі' активні записи, окрім 'цього'
            old_records = self.search([
                ('patient_id', '=', record.patient_id.id),
                ('active', '=', True),
                ('id', '!=', record.id),
            ])
            if old_records:
                old_records.write({
                    'active': False,
                    'end_date': fields.Date.today(),
                })

    @api.model_create_multi
    def create(self, vals_list):  # Override
        """On create, archive old active records."""
        records = super().create(vals_list)
        records.action_archive_old_records()
        return records
