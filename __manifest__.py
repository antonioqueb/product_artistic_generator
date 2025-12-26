{
    'name': 'Generador Artístico de Productos Pro',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Interfaz dinámica para creación de productos con lógica de ramificación',
    'author': 'Odoo Expert UI/UX',
    'depends': ['base', 'stock', 'purchase', 'product'],
    'data': [
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
