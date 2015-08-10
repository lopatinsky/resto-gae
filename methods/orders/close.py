import logging
from google.appengine.api.taskqueue import taskqueue
from methods.alfa_bank import pay_by_card
from methods.auto.request import close_order
from methods.parse_com import send_order_status_push
from models.auto import AutoVenue
from models.iiko import CompanyNew, DeliveryTerminal
from models.specials import SharedBonus

__author__ = 'dvpermyakov'


def close(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    delivery_terminal = DeliveryTerminal.get_by_id(order.delivery_terminal_id)
    auto_venue = AutoVenue.query(AutoVenue.delivery_terminal == delivery_terminal.key).get()
    if auto_venue:
        close_order(order, auto_venue)
    else:
        pay_result = pay_by_card(company, order.alfa_order_id, 0)
        logging.info("pay result: %s" % str(pay_result))
        success = 'errorCode' not in pay_result.keys() or str(pay_result['errorCode']) == '0'
        if not success:
            logging.warning("pay failed")
            return

        bonus = SharedBonus.query(SharedBonus.recipient == order.customer, SharedBonus.status == SharedBonus.READY).get()
        if bonus:
            bonus.deactivate(company)

        taskqueue.add(url='/single_task/push/review', params={
            'order_id': order.key.id()
        }, countdown=40)

        send_order_status_push(order)
