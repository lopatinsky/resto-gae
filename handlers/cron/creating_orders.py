# coding=utf-8
import datetime

from webapp2 import RequestHandler

from methods import alfa_bank
from methods.email import admin
from methods.iiko.order import order_info1
from models.iiko import Order
from models.iiko.company import CompanyNew, PaymentType
from models.iiko.delivery_terminal import DeliveryTerminal

MINUTES_INTERVAL = 5


class CheckCreatingOrdersHandler(RequestHandler):
    def get(self):
        now = datetime.datetime.now()
        delta = datetime.timedelta(minutes=MINUTES_INTERVAL)
        orders = Order.query(Order.status == Order.CREATING, Order.created <= now - delta).fetch()
        if orders:
            infos = []
            for order in orders:
                info = [
                    ("id", order.order_id),
                    ("payment type", order.payment_type),
                    ("payment id", order.alfa_order_id)
                ]
                to_delete = False

                iiko_order = order_info1(order.order_id, order.venue_id)
                if 'httpStatusCode' not in iiko_order:
                    info.append(('found', True))
                    order.load_from_object(iiko_order)
                else:
                    if order.payment_type == PaymentType.CARD:
                        try:
                            company = CompanyNew.get_by_iiko_id(order.venue_id)
                            delivery_terminal = DeliveryTerminal.get_by_id(order.delivery_terminal_id) \
                                if order.delivery_terminal_id else None
                            # check payment status
                            status = alfa_bank.check_extended_status(
                                company, delivery_terminal, order.alfa_order_id)["alfa_response"]
                            info.append(("status check result", status))

                            # if status check was successful:
                            if str(status.get("errorCode", '0')) == '0':
                                # money already deposited -- do not delete
                                if status['orderStatus'] == 2:
                                    info.append(("ERROR", "deposited"))
                                # money approved -- reverse
                                elif status['orderStatus'] == 1:
                                    reverse_result = alfa_bank.get_back_blocked_sum(
                                        company, delivery_terminal, order.alfa_order_id)
                                    info.append(("reverse result", reverse_result))
                                    if str(reverse_result.get('errorCode', '0')) == '0':
                                        to_delete = True
                                # any other status is OK to delete
                                else:
                                    to_delete = True
                        except Exception as e:
                            info.append(("exception", repr(e)))
                    else:
                        to_delete = True
                if to_delete:
                    order.key.delete()
                    info.append(("deleted", True))
                infos.append(info)
            mail_body = "Orders with creating status\n"
            mail_body += "List of orders:\n" + \
                         "\n\n".join("\n".join("%s: %s" % t for t in info) for info in infos)
            admin.send_error("order", "Orders crashed while creating", mail_body)
