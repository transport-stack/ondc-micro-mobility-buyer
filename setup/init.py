import django

django.setup()


def set_up_database(testing=False):
    from setup.add_cities import add_cities
    from setup.add_superuser import create_superuser
    from setup.add_ticket_type import setup_ticket_types
    from setup.add_transaction_setup import setup_payment_gateways_and_modes
    from setup.add_transit import setup_transit_modes
    from setup.add_transit_providers import setup_transit_providers_and_options
    from setup.add_coupons import add_coupons
    from setup.add_celerytasks import add_celery_tasks
    from setup.add_dmrc_data import main as add_dmrc_data

    add_cities()
    create_superuser()
    setup_ticket_types()
    setup_payment_gateways_and_modes()
    setup_transit_modes()
    setup_transit_providers_and_options()
    add_coupons()
    if not testing:
        add_celery_tasks()
    # add_dmrc_data(testing)


if __name__ == "__main__":
    set_up_database()
