{
    'name': 'Periodic Expense',
    'version': '1.0',
    'summary': 'Travel report with expense integration',
    'depends': ['hr_expense', 'base'],
    'category': 'Expenses',
    'data': [
        'security/ir.model.access.csv',
        'views/travel_report_views.xml',
        'views/periodic_expense_menu.xml',
        'views/inherited_expense_view.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
