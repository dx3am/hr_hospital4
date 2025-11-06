# -*- coding: utf-8 -*-
"""Defines the Doctor Speciality model."""

from odoo import models, fields


class DoctorSpeciality(models.Model):
    """Model for storing doctor specialities."""
    _name = 'doctor.speciality'
    _description = 'Doctor Speciality'
    _rec_name = 'name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(size=10, required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)

    doctor_ids = fields.One2many(  # Зв'язок One2many
        comodel_name='hr.hospital.doctor',
        inverse_name='specialty_id',
        string='Doctors'
    )

    _sql_constraints = [  # Валідатор SQL
        ('code_uniq', 'unique(code)', 'Speciality code must be unique!')
    ]
