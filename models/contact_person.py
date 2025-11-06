# -*- coding: utf-8 -*-
"""This file defines the Contact Person model."""

from odoo import models, fields


class ContactPerson(models.Model):
    """Model for storing patient contact persons."""
    _name = 'contact.person'
    _inherit = ['abstract.person']  # Наслідування абстрактної моделі
    _description = 'Contact Person'
    _rec_name = 'full_name'

    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Related Patient (with Allergies)',
        domain="[('allergies', '!=', False)]",
        help="Показує лише пацієнтів із заповненим полем 'Алергії'."
    )
