{
    "name": "LogiFlow Portal",
    "version": "19.0.1.0.0",
    "summary": "Shipment request portal and internal tracking",
    "category": "Operations",
    "author": "LogiFlow-AI",
    "license": "LGPL-3",
    "depends": ["base", "mail", "website"],
    "data": [
        "security/ir.model.access.csv",
        "views/shipment_views.xml",
        "views/portal_templates.xml",
        "views/menu.xml",
    ],
    "application": True,
    "installable": True,
}
