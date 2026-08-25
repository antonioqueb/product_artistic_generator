# -*- coding: utf-8 -*-
"""Crear y duplicar productos: SOLO administración.

Regla de negocio: los productos nacen por el Generador (nomenclatura,
atributos y escalera controlados). El 'Duplicar' del engrane creaba
copias fuera de ese carril — con folios "(copia)", escaleras y flags
heredados a ciegas. Se bloquea en el SERVIDOR (el menú del engrane no
puede ocultarse por grupo sin JS frágil): cualquier duplicado, por UI o
por RPC, exige Administración/Ajustes o Características técnicas.
"""
from odoo import api, models, _
from odoo.exceptions import UserError

_DUPLICATE_BLOCK_MSG = (
    'Duplicar productos está deshabilitado.\n\n'
    'Los productos se dan de alta con el GENERADOR (nomenclatura y '
    'precios controlados). Solo usuarios con permiso de '
    'Administración/Ajustes o Características técnicas pueden duplicar.'
)

_CREATE_BLOCK_MSG = (
    'Crear productos a mano está deshabilitado.\n\n'
    'Los productos se dan de alta con el GENERADOR (nomenclatura y '
    'precios controlados). Solo usuarios con permiso de '
    'Administración/Ajustes o Características técnicas pueden crearlos '
    'directamente.'
)


def _som_assert_product_admin(env, message):
    user = env.user
    if user.has_group('base.group_system') \
            or user.has_group('base.group_no_one'):
        return
    raise UserError(_(message))


def _som_assert_can_duplicate(env):
    _som_assert_product_admin(env, _DUPLICATE_BLOCK_MSG)


class ProductTemplateNoDuplicate(models.Model):
    _inherit = 'product.template'

    def copy(self, default=None):
        _som_assert_can_duplicate(self.env)
        return super().copy(default=default)

    @api.model_create_multi
    def create(self, vals_list):
        # El GENERADOR crea con sudo() y pasa intacto (has_group bajo su
        # devuelve True); esto solo frena el botón Nuevo / RPC directo.
        _som_assert_product_admin(self.env, _CREATE_BLOCK_MSG)
        return super().create(vals_list)


class ProductProductNoDuplicate(models.Model):
    _inherit = 'product.product'

    def copy(self, default=None):
        _som_assert_can_duplicate(self.env)
        return super().copy(default=default)

    @api.model_create_multi
    def create(self, vals_list):
        _som_assert_product_admin(self.env, _CREATE_BLOCK_MSG)
        return super().create(vals_list)
