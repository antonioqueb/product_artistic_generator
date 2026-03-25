from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductFinish(models.Model):
    _name = 'product.finish'
    _description = 'Acabado de Producto'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre del Acabado', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductThickness(models.Model):
    _name = 'product.thickness'
    _description = 'Espesor de Producto'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre del Espesor', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductDimension(models.Model):
    _name = 'product.dimension'
    _description = 'Dimensión de Producto'
    _order = 'sequence, name'

    name = fields.Char(string='Dimensión', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Marca Comercial de Producto'
    _order = 'sequence, name'

    name = fields.Char(string='Marca', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create_artistic_product(self, vals):
        """
        Crea un producto basado en parámetros.
        Forzando: Mayúsculas, Unidad m2, Seguimiento por Lote y Tipo Almacenable.
        """
        if not self.env.user.has_group('product_artistic_generator.group_product_generator'):
            raise UserError(_("No tiene permisos para generar productos."))

        commercial_name = vals.get('commercial_name', '').strip()
        finish = vals.get('finish', '').strip()
        thickness = vals.get('thickness', '').strip()
        dimension = vals.get('dimension', '').strip()
        color = vals.get('color', '').strip()
        marca = vals.get('marca', '').strip()
        origin_name = vals.get('origin_name', '').strip()
        supplier_id = vals.get('supplier_id')
        product_type = vals.get('product_type', '')

        # Construir nombre: NOMBRE_COMERCIAL ACABADO DIMENSION ESPESOR - MARCA
        parts = [commercial_name, finish]
        if dimension:
            parts.append(dimension)
        parts.append(thickness)

        full_name = ' '.join(p for p in parts if p).upper()
        # Limpiar espacios múltiples
        full_name = ' '.join(full_name.split())

        # Agregar marca con separador guion
        if marca:
            full_name = f"{full_name} - {marca.upper()}"

        # Verificar que no exista un producto con el mismo nombre
        existing = self.env['product.template'].sudo().search([
            ('name', '=ilike', full_name)
        ], limit=1)
        if existing:
            raise UserError(_(
                "Ya existe un producto con el nombre '%(name)s' (ID: %(id)s). "
                "No se puede crear un producto duplicado.",
                name=full_name, id=existing.id
            ))

        uom_m2 = self.env.ref('uom.product_uom_m2', raise_if_not_found=False)
        if not uom_m2:
            uom_m2 = self.env['uom.uom'].search([('name', 'ilike', 'm²')], limit=1)

        if not uom_m2:
            raise UserError(_("No se encontró la unidad de medida 'm²' en el sistema."))

        product_vals = {
            'name': full_name,
            'is_storable': True,
            'tracking': 'lot',
            'categ_id': vals.get('category_id'),
            'uom_id': uom_m2.id,
            'purchase_method': 'purchase',
            'list_price': 0.0,
            'sale_ok': True,
            'purchase_ok': True,
        }

        # Escribir x_color si el campo existe y se proporcionó valor
        if color and 'x_color' in self.env['product.template']._fields:
            product_vals['x_color'] = color.upper()

        # Escribir x_marca si el campo existe y se proporcionó valor
        if marca and 'x_marca' in self.env['product.template']._fields:
            product_vals['x_marca'] = marca.upper()

        product_template = self.env['product.template'].sudo().create(product_vals)

        # Crear nombre de origen si se proporcionó y el modelo existe
        if origin_name and 'product.origin.name' in self.env:
            origin_vals = {
                'name': origin_name,
                'product_tmpl_id': product_template.id,
                'sequence': 10,
            }
            if supplier_id:
                origin_vals['partner_id'] = supplier_id
            self.env['product.origin.name'].sudo().create(origin_vals)

        return product_template.id