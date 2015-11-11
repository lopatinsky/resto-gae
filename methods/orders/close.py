# coding=utf-8
import logging
from google.appengine.api.taskqueue import taskqueue
from methods.alfa_bank import pay_by_card
from methods.auto.request import close_order
from methods.parse_com import send_order_status_push
from methods.versions import supports_review
from models.iiko import CompanyNew, PaymentType
from models.iiko.order import AUTO_APP_SOURCE
from models.specials import SharedBonus

__author__ = 'dvpermyakov'


def close(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    if company.auto_token and order.source == AUTO_APP_SOURCE:
        close_order(order, company.auto_token)
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
    if company.review_enable and supports_review(company.iiko_org_id, order_user_agent):
        taskqueue.add(url='/single_task/push/review', params={
            'order_id': order.order_id
        }, countdown=60*30)

    send_order_status_push(order)
