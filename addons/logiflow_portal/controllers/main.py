from odoo import http
from odoo.http import request


class LogiFlowPortalController(http.Controller):
    @http.route("/logiflow", type="http", auth="public", website=True)
    def logiflow_home(self, **kwargs):
        return request.render("logiflow_portal.portal_page", {})

    @http.route(
        "/logiflow/submit",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def submit_shipment(self, **post):
        payload = {
            "partner_name": (post.get("partner_name") or "").strip(),
            "partner_email": (post.get("partner_email") or "").strip(),
            "pickup_address": (post.get("pickup_address") or "").strip(),
            "delivery_address": (post.get("delivery_address") or "").strip(),
            "priority": post.get("priority", "normal"),
            "note": (post.get("note") or "").strip(),
            "status": "received",
        }

        try:
            payload["package_weight"] = float(post.get("package_weight", 0) or 0)
        except (TypeError, ValueError):
            payload["package_weight"] = 0

        required_fields = ["partner_name", "partner_email", "pickup_address", "delivery_address"]
        if any(not payload[field] for field in required_fields) or payload["package_weight"] <= 0:
            return request.redirect("/logiflow?error=1")

        request.env["logiflow.shipment.request"].sudo().create(payload)
        return request.redirect("/logiflow?success=1")
