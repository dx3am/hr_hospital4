# -*- coding: utf-8 -*-
"""This file defines the Doctor Schedule model."""

from odoo import models, fields, _


class DoctorSchedule(models.Model):
    """Model for storing doctor schedules."""
    _name = 'doctor.schedule'
    _description = 'Doctor Schedule'
    _rec_name = 'doctor_id'

    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        required=True,
        # Домен: тільки лікарі з заповненою спеціальністю
        domain="[('specialty_id', '!=', False)]"
    )
    day_of_week = fields.Selection(
        selection=[
            ('1', 'Понеділок'),
            ('2', 'Вівторок'),
            ('3', 'Середа'),
            ('4', 'Четвер'),
            ('5', "П'ятниця"),
            ('6', 'Субота'),
            ('7', 'Неділя')
        ]
    )
    date = fields.Date()
    start_time = fields.Float()
    end_time = fields.Float()
    schedule_type = fields.Selection(
        selection=[
            ('work', 'Робочий день'),
            ('vacation', 'Відпустка'),
            ('sick', 'Лікарняний'),
            ('conference', 'Конференція')
        ],
        default='work'
    )
    notes = fields.Char()

    _sql_constraints = [  # Валідатор SQL
        ('check_time',
         'CHECK(end_time > start_time)',
         # pylint: disable=translation-field
         _('End time must be after start time.'))
    ]
