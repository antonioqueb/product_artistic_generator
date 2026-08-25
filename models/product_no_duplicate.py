# -*- coding: utf-8 -*-
"""Duplicar productos: SOLO administración.

Regla de negocio: los productos nacen por el Generador (nomenclatura,
atributos y escalera controlados). El 'Duplicar' del engrane creaba
copias fuera de ese carril — con folios "(copia)", escaleras y flags
heredados a ciegas. Se bloquea en el SERVIDOR (el menú del engrane no
puede ocultarse por grupo sin JS frágil): cualquier duplicado, por UI o
por RPC, exige Administración/Ajustes o Características técnicas.
"""
from odoo import models, _
from odoo.exceptions import UserError

_DUPLICATE_BLOCK_MSG = (
    'Duplicar productos está deshabilitado.\n\n'
    'Los productos se dan de alta con el GENERADOR (nomenclatura y '
    'precios controlados). Solo usuarios con permiso de '
    'Administración/Ajustes o Características técnicas pueden duplicar.'
)


def _som_assert_can_duplicate(env):
    user = env.user
    if user.has_group('base.group_system') \
            or user.has_group('base.group_no_one'):
        return
    raise UserError(_(_DUPLICATE_BLOCK_MSG))


class ProductTemplateNoDuplicate(models.Model):
    _inherit = 'product.template'

    def copy(self, default=None):
        _som_assert_can_duplicate(self.env)
        return super().copy(default=default)


class ProductProductNoDuplicate(models.Model):
    _inherit = 'product.product'

    def copy(self, default=None):
        _som_assert_can_duplicate(self.env)
        return super().copy(default=default)
