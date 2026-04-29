# LogiFlow-AI Full Stack (Odoo 19)

This repository contains a full stack logistics app built on the latest Odoo major version (19.x), including:

- **Backend**: Odoo custom module (`logiflow_portal`) with shipment request model and admin views
- **Frontend**: Odoo website page + form for public shipment submission
- **Database**: PostgreSQL 16
- **Runtime**: Docker Compose

## Quick Start

```bash
docker compose up -d
```

Open: `http://localhost:8069`

## Install the custom module

1. Create or select your Odoo database from the web UI.
2. Go to **Apps**.
3. Enable developer mode and update apps list.
4. Search for **LogiFlow Portal** and install it.

## Usage

- Public form: `http://localhost:8069/logiflow`
- Internal management: **LogiFlow → Shipment Requests**

## Project Structure

- `docker-compose.yml`: Odoo + PostgreSQL stack
- `config/odoo.conf`: Odoo configuration
- `addons/logiflow_portal`: Full custom app (models, controllers, views, security)
