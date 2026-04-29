from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LogiflowShipmentRequest(models.Model):
    _name = "logiflow.shipment.request"
    _description = "LogiFlow Shipment Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "requested_on desc, id desc"

    name = fields.Char(required=True, default="New", copy=False, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    partner_name = fields.Char(required=True, tracking=True)
    partner_email = fields.Char(required=True)
    pickup_address = fields.Text(required=True)
    delivery_address = fields.Text(required=True)
    package_weight = fields.Float(required=True)
    priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High")],
        default="normal",
        required=True,
        tracking=True,
    )
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("received", "Received"),
            ("in_transit", "In Transit"),
            ("delivered", "Delivered"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    requested_on = fields.Datetime(default=fields.Datetime.now)
    note = fields.Text()

    @api.constrains("package_weight")
    def _check_weight(self):
        for record in self:
            if record.package_weight <= 0:
                raise ValidationError("Package weight must be greater than zero.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "logiflow.shipment.request"
                ) or "New"

            email = vals.get("partner_email")
            name = vals.get("partner_name")
            if email and not vals.get("partner_id"):
                partner = self.env["res.partner"].search([("email", "=", email)], limit=1)
                if not partner:
                    partner = self.env["res.partner"].create(
                        {
                            "name": name,
                            "email": email,
                            "type": "contact",
                        }
                    )
                vals["partner_id"] = partner.id

        return super().create(vals_list)

    def action_mark_received(self):
        self.write({"status": "received"})

    def action_mark_in_transit(self):
        self.write({"status": "in_transit"})

    def action_mark_delivered(self):
        self.write({"status": "delivered"})

    def action_cancel(self):
        self.write({"status": "cancelled"})
