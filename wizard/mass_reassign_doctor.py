# -*- coding: utf-8 -*-
"""Defines the Mass Reassign Doctor Wizard."""

from odoo import models, fields, api


class MassReassignDoctor(models.TransientModel):
    """Wizard for mass re-assignment of patients to a new doctor."""
    _name = 'mass.reassign.doctor.wizard'
    _description = 'Mass Reassign Doctor Wizard'

    old_doctor_id = fields.Many2one('hr.hospital.doctor')
    new_doctor_id = fields.Many2one('hr.hospital.doctor', required=True)
    patient_ids = fields.Many2many(
        comodel_name='hr.hospital.patient',
        # Динамічний домен на пацієнтів старого лікаря
        domain="[('personal_doctor_id', '=', old_doctor_id)]"
    )
    change_date = fields.Date(default=fields.Date.today, required=True)
    change_reason = fields.Text(required=True)

    @api.onchange('old_doctor_id')
    def _onchange_old_doctor_id(self):
        """
        Applies a dynamic domain on patient_ids based on old_doctor_id.
        """
        # Спочатку очищення списку пацієнтів, якщо змінено лікаря
        self.patient_ids = [(5, 0, 0)]

        # Повернення нового домена для поля 'patient_ids'
        return {
            'domain': {
                'patient_ids': [
                    ('personal_doctor_id', '=', self.old_doctor_id.id)
                ]
            }
        }

    def action_reassign(self):
        """Performs the mass re-assignment."""
        self.ensure_one()

        self.patient_ids.write({
            'personal_doctor_id': self.new_doctor_id.id
        })

        return {'type': 'ir.actions.act_window_close'}
