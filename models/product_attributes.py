import re

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GeneratorAttributeMixin(models.AbstractModel):
    """Comportamiento común de los atributos del generador.

    - Regla de oro: el nombre SIEMPRE se guarda en MAYÚSCULAS, sin importar
      desde dónde se cree (vista de configuración o alta rápida del generador).
    - Alta rápida (quick_create_from_generator): crea el registro desde la
      interfaz del generador y lo devuelve listo para quedar seleccionado, sin
      necesidad de refrescar.
    """
    _name = 'generator.attribute.mixin'
    _description = 'Atributo del Generador (mayúsculas + alta rápida)'

    @api.model
    def _normalize_name(self, name):
        """Normaliza el nombre. Por defecto: mayúsculas y sin espacios extra."""
        return ' '.join((name or '').upper().split())

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = self._normalize_name(vals['name'])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = self._normalize_name(vals['name'])
        return super().write(vals)

    @api.model
    def quick_create_from_generator(self, name):
        """Crea (o reutiliza) un atributo desde el generador y lo devuelve.

        Devuelve {'id', 'name'} con el nombre ya normalizado para que el
        front-end lo deje seleccionado de inmediato.
        """
        if not self.env.user.has_group('product_artistic_generator.group_product_generator'):
            raise UserError(_("No tiene permisos para crear atributos."))

        normalized = self._normalize_name(name)
        if not normalized:
            raise UserError(_("El valor no puede estar vacío."))

        # Reutilizar si ya existe (sin distinguir mayúsculas) para no duplicar.
        record = self.sudo().search([('name', '=ilike', normalized)], limit=1)
        if not record:
            record = self.sudo().create({'name': normalized})
        return {'id': record.id, 'name': record.name}


class ProductFinish(models.Model):
    _name = 'product.finish'
    _inherit = 'generator.attribute.mixin'
    _description = 'Acabado de Producto'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre del Acabado', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductThickness(models.Model):
    _name = 'product.thickness'
    _inherit = 'generator.attribute.mixin'
    _description = 'Espesor de Producto'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre del Espesor', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductDimension(models.Model):
    _name = 'product.dimension'
    _inherit = 'generator.attribute.mixin'
    _description = 'Dimensión de Producto'
    _order = 'sequence, name'

    name = fields.Char(string='Dimensión', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)

    @api.model
    def _normalize_name(self, name):
        """Normaliza la dimensión al formato 'MEDIDA X MEDIDA X':

        - Mayúsculas y sin espacios extra.
        - Cada separador entre medidas queda como ' X ' (con espacios), aunque
          el usuario lo escriba pegado: '10x20' -> '10 X 20 X'.
        - Siempre termina en ' X' (espacio + X), sin duplicar el sufijo.

        Ejemplos:
            '10x20'      -> '10 X 20 X'
            '10 X 20 X'  -> '10 X 20 X'   (se respeta)
            '1.20x2.40'  -> '1.20 X 2.40 X'
            '60'         -> '60 X'
        """
        s = ' '.join((name or '').upper().split())
        if not s:
            return s
        # Compactar cada separador 'X' (con o sin espacios) a una sola 'X'.
        s = re.sub(r'\s*X\s*', 'X', s)
        # Quitar las 'X' finales: el sufijo se re-agrega al final.
        s = s.rstrip('X')
        partes = [p for p in s.split('X') if p]
        if not partes:
            return 'X'
        return ' X '.join(partes) + ' X'


class ProductBrand(models.Model):
    _name = 'product.brand'
    _inherit = 'generator.attribute.mixin'
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
        Forzando: Mayúsculas, Seguimiento por Lote y Tipo Almacenable.
        UdM y x_unidad_del_producto según tipo.
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

        # PROCEDENCIA OBLIGATORIA: nacional (país México por defecto) o
        # importado (país a elegir, SIN IVA de compra).
        procedencia = (vals.get('procedencia') or '').strip().lower()
        origin_country_id = vals.get('origin_country_id')
        if procedencia not in ('nacional', 'importado'):
            raise UserError(_(
                "Debe indicar si el producto es NACIONAL o IMPORTADO."))
        if procedencia == 'nacional' and not origin_country_id:
            mx = self.env.ref('base.mx', raise_if_not_found=False)
            origin_country_id = mx.id if mx else False
        if procedencia == 'importado' and not origin_country_id:
            raise UserError(_(
                "Producto importado: debe elegir el país de origen."))

        # Construir nombre según tipo
        if product_type == 'pieza':
            # Pieza: solo NOMBRE_COMERCIAL - MARCA (sin palabra de tipo)
            full_name = commercial_name.upper()
        else:
            # Placas y formatos: NOMBRE_COMERCIAL ACABADO DIMENSION [PLACA] ESPESOR
            parts = [commercial_name, finish]
            if dimension:
                parts.append(dimension)
            # Solo las placas llevan la palabra "PLACA" en el nombre, justo
            # antes del grosor. Los formatos no añaden palabra de tipo.
            if product_type in ('placa_natural', 'placa_sintetica'):
                parts.append('PLACA')
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

        # Determinar UdM según tipo
        if product_type == 'pieza':
            uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
            if not uom:
                uom = self.env['uom.uom'].search([('name', 'ilike', 'Unidades')], limit=1)
            if not uom:
                raise UserError(_("No se encontró la unidad de medida 'Unidades' en el sistema."))
        else:
            uom = self.env.ref('uom.product_uom_m2', raise_if_not_found=False)
            if not uom:
                uom = self.env['uom.uom'].search([('name', 'ilike', 'm²')], limit=1)
            if not uom:
                raise UserError(_("No se encontró la unidad de medida 'm²' en el sistema."))

        # Determinar x_unidad_del_producto
        unidad_map = {
            'placa_natural': 'Placa',
            'placa_sintetica': 'Placa',
            'formato': 'Formato',
            'pieza': 'Pieza',
        }

        product_vals = {
            'name': full_name,
            'is_storable': True,
            'tracking': 'lot',
            'categ_id': vals.get('category_id'),
            'uom_id': uom.id,
            'purchase_method': 'purchase',
            'list_price': 0.0,
            'sale_ok': True,
            'purchase_ok': True,
        }

        # IMPORTADO: sin IVA de compra (los impuestos de importación se
        # manejan por pedimento, no en la factura del proveedor extranjero).
        # NACIONAL conserva el IVA de compra default de la compañía.
        if procedencia == 'importado':
            product_vals['supplier_taxes_id'] = [(5, 0, 0)]

        # Propagar los atributos a los campos de product.template definidos en
        # el módulo stock_lot_dimensions (pestaña "Atributos"). Cada campo se
        # escribe solo si existe en el modelo, para no romper si ese módulo no
        # estuviera instalado.
        tmpl_fields = self.env['product.template']._fields

        # País de Origen: México en nacional (default) o el elegido en
        # importado. Solo si el campo existe (stock_lot_dimensions).
        if origin_country_id and 'x_origin_country_id' in tmpl_fields:
            product_vals['x_origin_country_id'] = int(origin_country_id)

        # Unidad del Producto: SIEMPRE se llena según el tipo
        # (Placa / Formato / Pieza).
        unidad_valor = unidad_map.get(product_type, '')
        if unidad_valor and 'x_unidad_del_producto' in tmpl_fields:
            product_vals['x_unidad_del_producto'] = unidad_valor

        # Color Estándar (no aplica a pieza)
        if color and product_type != 'pieza' and 'x_color' in tmpl_fields:
            product_vals['x_color'] = color.upper()

        # Marca Comercial
        if marca and 'x_marca' in tmpl_fields:
            product_vals['x_marca'] = marca.upper()

        # Acabado Superficial (no aplica a pieza)
        if finish and product_type != 'pieza' and 'x_acabado' in tmpl_fields:
            product_vals['x_acabado'] = finish.upper()

        # Grosor Nominal (no aplica a pieza)
        if thickness and product_type != 'pieza' and 'x_grosor' in tmpl_fields:
            product_vals['x_grosor'] = thickness.upper()

        # Dimensiones = dimensión + grosor (no aplica a pieza)
        if product_type != 'pieza' and 'x_dimensiones' in tmpl_fields:
            dim_parts = [p for p in (dimension, thickness) if p]
            if dim_parts:
                product_vals['x_dimensiones'] = ' '.join(dim_parts).upper()

        product_template = self.env['product.template'].sudo().create(product_vals)

        # Empaques estándar definidos desde el generador: se propagan al
        # listado de standard.pack (módulo standard_pack_som). Múltiples
        # líneas permitidas; exactamente UNA queda como default.
        standard_packs = vals.get('standard_packs') or []
        if standard_packs and 'standard.pack' in self.env:
            Pack = self.env['standard.pack'].sudo()
            valid = [
                p for p in standard_packs
                if p.get('pack_type_id') and float(p.get('qty_per_pack') or 0) > 0
            ]
            if valid and not any(p.get('is_default') for p in valid):
                valid[0]['is_default'] = True
            seq = 10
            for p in valid:
                Pack.create({
                    'product_tmpl_id': product_template.id,
                    'pack_type_id': int(p['pack_type_id']),
                    'qty_per_pack': float(p['qty_per_pack']),
                    'is_default': bool(p.get('is_default')),
                    'sequence': seq,
                })
                seq += 10

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