# -*- coding: utf-8 -*-
"""Defines the Doctor Schedule Wizard."""

from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError


class DoctorScheduleWizard(models.TransientModel):
    """Wizard for mass-generating doctor schedule slots."""
    _name = 'doctor.schedule.wizard'
    _description = 'Doctor Schedule Wizard'

    doctor_id = fields.Many2one('hr.hospital.doctor', required=True,
                                domain="[('specialty_id', '!=', False)]")
    week_start_date = fields.Date(required=True,
                                  default=fields.Date.today)
    week_count = fields.Integer(default=1, required=True, string="Кількість тижнів")

    schedule_type = fields.Selection(
        selection=[
            ('standard', 'Стандартний (кожен тиждень)'),
            ('even', 'Парний тиждень'),
            ('odd', 'Непарний тиждень')
        ],
        default='standard', required=True, string="Тип розкладу"
    )

    day_mon = fields.Boolean(string="Понеділок", default=True)
    day_tue = fields.Boolean(string="Вівторок", default=True)
    day_wed = fields.Boolean(string="Середа", default=True)
    day_thu = fields.Boolean(string="Четвер", default=True)
    day_fri = fields.Boolean(string="П'ятниця", default=True)
    day_sat = fields.Boolean(string="Субота")
    day_sun = fields.Boolean(string="Неділя")

    start_time = fields.Float(required=True)
    end_time = fields.Float(required=True)

    break_start_time = fields.Float()
    break_end_time = fields.Float()

    @api.constrains('start_time', 'end_time',
                    'break_start_time', 'break_end_time')
    def _check_times(self):
        for record in self:
            if record.end_time <= record.start_time:
                raise UserError(self.env._("End time must be after start time."))
            if record.break_start_time and record.break_end_time:
                if record.break_end_time <= record.break_start_time:
                    raise UserError(self.env._("Break end time must be after break start time."))
                if not (record.start_time < record.break_start_time <
                        record.break_end_time < record.end_time):
                    raise UserError(self.env._("Break time must be within working hours."))

    def action_generate_schedule(self):
        """Generates schedule slots based on wizard parameters."""
        self.ensure_one()
        schedule_env = self.env['doctor.schedule']
        days_to_generate = [
            self.day_mon, self.day_tue, self.day_wed,
            self.day_thu, self.day_fri, self.day_sat, self.day_sun
        ]

        # Пакетне створення
        schedule_vals_list = []

        for week in range(self.week_count):
            current_week_date = self.week_start_date + timedelta(days=week * 7)

            # ISO
            week_number = current_week_date.isocalendar()[1]
            is_even_week = week_number % 2 == 0

            # Логіка парності/непарності
            if self.schedule_type == 'even' and not is_even_week:
                continue
            if self.schedule_type == 'odd' and is_even_week:
                continue

            # Якщо 'standard', або парність/непарність збігається:
            for day_index, is_work_day in enumerate(days_to_generate):
                if not is_work_day:
                    continue

                current_date = self.week_start_date + \
                               timedelta(days=(week * 7) + day_index)

                day_of_week_str = str(current_date.isoweekday())  # 1=Пн, 7=Нд

                # Базовий слот
                base_slot = {
                    'doctor_id': self.doctor_id.id,
                    'date': current_date,
                    'day_of_week': day_of_week_str,
                    'schedule_type': 'work',
                }

                if self.break_start_time and self.break_end_time:
                    # 2 слоти: до і після перерви
                    schedule_vals_list.append({
                        **base_slot,
                        'start_time': self.start_time,
                        'end_time': self.break_start_time,
                    })
                    schedule_vals_list.append({
                        **base_slot,
                        'start_time': self.break_end_time,
                        'end_time': self.end_time,
                    })
                else:
                    # 1 слот (без перерви)
                    schedule_vals_list.append({
                        **base_slot,
                        'start_time': self.start_time,
                        'end_time': self.end_time,
                    })

        if schedule_vals_list:
            schedule_env.create(schedule_vals_list)

        return {'type': 'ir.actions.act_window_close'}
