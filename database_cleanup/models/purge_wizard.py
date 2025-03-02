# Copyright 2014-2016 Therp BV <http://therp.nl>
# Copyright 2021 Camptocamp <https://camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=consider-merging-classes-inherited

import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied


class CleanupPurgeLine(models.AbstractModel):
    """Abstract base class for the purge wizard lines"""

    _name = "cleanup.purge.line"
    _order = "name"
    _description = "Purge Column Abstract Wizard"

    name = fields.Char(readonly=True)
    purged = fields.Boolean(readonly=True)
    wizard_id = fields.Many2one("cleanup.purge.wizard")

    logger = logging.getLogger("odoo.addons.database_cleanup")

    def purge(self):
        raise NotImplementedError

    @api.model_create_multi
    def create(self, values):
        # make sure the user trying this is actually supposed to do it
        if self.env.ref("base.group_erp_manager") not in self.env.user.groups_id:
            raise AccessDenied
        return super().create(values)


class PurgeWizard(models.AbstractModel):
    """Abstract base class for the purge wizards"""

    _name = "cleanup.purge.wizard"
    _description = "Purge stuff"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "purge_line_ids" in fields_list:
            res["purge_line_ids"] = self.find()
        return res

    def find(self):
        raise NotImplementedError

    def purge_all(self):
        self.mapped("purge_line_ids").purge()
        return True

    @api.model
    def get_wizard_action(self):
        wizard = self.create({})
        return {
            "type": "ir.actions.act_window",
            "name": wizard.display_name,
            "views": [(False, "form")],
            "res_model": self._name,
            "res_id": wizard.id,
            "flags": {
                "action_buttons": False,
                "sidebar": False,
            },
        }

    def select_lines(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Select lines to purge"),
            "views": [(False, "list"), (False, "form")],
            "res_model": self._fields["purge_line_ids"].comodel_name,
            "domain": [("wizard_id", "in", self.ids)],
        }

    def _compute_display_name(self):
        for this in self:
            this.display_name = self._description

    @api.model_create_multi
    def create(self, values):
        # make sure the user trying this is actually supposed to do it
        if self.env.ref("base.group_erp_manager") not in self.env.user.groups_id:
            raise AccessDenied
        return super().create(values)

    purge_line_ids = fields.One2many("cleanup.purge.line", "wizard_id")
