import logging
from google.appengine.api.taskqueue import taskqueue
from methods.alfa_bank import pay_by_card
from methods.auto.request import close_order
from methods.parse_com import send_order_status_push
from models.auto import AutoVenue
from models.iiko import CompanyNew, DeliveryTerminal, PaymentType, Customer
from models.iiko.order import AUTO_APP_SOURCE
from models.specials import SharedBonus

__author__ = 'dvpermyakov'


def close(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    delivery_terminal = DeliveryTerminal.get_by_id(order.delivery_terminal_id)
    auto_venue = AutoVenue.query(AutoVenue.delivery_terminal == delivery_terminal.key).get()
    if auto_venue and order.source == AUTO_APP_SOURCE:
        close_order(order, auto_venue)
    if order.payment_type == PaymentType.CARD:
        pay_result = pay_by_card(company, order.alfa_order_id, 0)
        logging.info("pay result: %s" % str(pay_result))
        success = 'errorCode' not in pay_result.keys() or str(pay_result['errorCode']) == '0'
        if not success:
            logging.warning("pay failed")
            return
    if company.is_iiko_system:
        bonus = SharedBonus.query(SharedBonus.recipient == order.customer, SharedBonus.status == SharedBonus.READY).get()
        if bonus:
            taskqueue.add(url='/single_task/bonus/activate', params={
                'order_id': order.order_id
            })
    order_user_agent = order.customer.get().user_agent
    if company.review_enable and ('OrangeExpress/2.0.3' in order_user_agent or 'orangexpress/1.2.2' in order_user_agent):
        taskqueue.add(url='/single_task/push/review', params={
            'order_id': order.order_id
        }, countdown=60*45)

    send_order_status_push(order)
