{
    'name': 'Generador de Productos',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Interfaz dinámica para creación de productos con lógica de ramificación',
    'description': """
Generador Artístico de Productos Pro
==========================================================================
Módulo avanzado para la creación dinámica de productos basados en atributos artísticos como acabado y espesor.
Características principales:
- Interfaz de usuario intuitiva para seleccionar atributos artísticos.
- Creación automática de productos con nombres formateados y configuraciones específicas.
- Gestión de inventario optimizada con seguimiento por lote y unidad de medida en metros cuadrados.
Ideal para empresas que requieren una gestión detallada de productos personalizados.
    """,
    'author': 'Alphaqueb Consulting',
    'website': 'https://www.alphaqueb.com',
    'license': 'AGPL-3',


    'depends': ['base', 'stock', 'purchase', 'product'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_attribute_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'product_artistic_generator/static/src/components/product_generator/product_generator.js',
            'product_artistic_generator/static/src/components/product_generator/product_generator.xml',
            'product_artistic_generator/static/src/components/product_generator/product_generator.scss',
        ],
    },
    'installable': True,
    'application': True,
}
