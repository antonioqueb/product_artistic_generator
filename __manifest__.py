{
    'name': 'Generador de Productos',
    'version': '1.1',
    'category': 'Inventory',
    'summary': 'Interfaz dinámica para creación de productos con lógica de ramificación',
    'description': """
Generador de Productos
==========================================================================
Módulo avanzado para la creación dinámica de productos basados en atributos.
    """,
    'author': 'Alphaqueb Consulting',
    'website': 'https://www.alphaqueb.com',
    'license': 'AGPL-3',

    'depends': ['base', 'stock', 'purchase', 'product', 'product_origin_name'],
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