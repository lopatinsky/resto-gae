# coding=utf-8
from ..base import BaseHandler
import logging
from models.iiko import Customer, PaymentType, Venue
from models.specials import Share, SharedGift
from methods import branch_io
from config import config


class GetInvitationUrlsHandler(BaseHandler):

    @staticmethod
    def get_general_shared_dict():
        TEXT_ID = 1
        return TEXT_ID, {
            'text': '1231',
        }

    def get(self):
        venue_id = self.request.get('venue_id')
        if not venue_id in config.INVITATION_BRANCH_VENUES:
            self.abort(403)
        customer_id = self.request.get('customer_id')
        customer = Customer.customer_by_customer_id(customer_id)
        if not customer:
            self.abort(400)
        share = Share(share_type=branch_io.SHARE, sender=customer.key)
        share.put()

        text_id, values = GetInvitationUrlsHandler.get_general_shared_dict()

        if 'iOS' in self.request.headers["User-Agent"]:
            user_agent = 'ios'
        elif 'Android' in self.request.headers["User-Agent"]:
            user_agent = 'android'
        else:
            user_agent = 'unknown'
        urls = [{
            'url': branch_io.create_url(venue_id, share.key.id(), branch_io.INVITATION, channel, user_agent,
                                        custom_tags={"text_id": text_id}),
            'channel': channel
        } for channel in branch_io.CHANNELS]
        share.urls = [url['url'] for url in urls]
        share.put()

        values['urls'] = urls

        self.render_json(values)


class GetGiftUrlsHandler(BaseHandler):
    BONUS_SUM = 350

    def send_error(self, error):
        logging.info(error)

        self.response.set_status(400)
        self.render_json({
            'success': False,
            'description': error
        })

    def success(self, venue, sender, gift, name=None, phone=None):
        share = Share(share_type=branch_io.GIFT, sender=sender.key)
        share.put()
        if 'iOS' in self.request.headers["User-Agent"]:
            user_agent = 'ios'
        elif 'Android' in self.request.headers["User-Agent"]:
            user_agent = 'android'
        else:
            user_agent = 'unknown'
        recipient = {
            'name': name,
            'phone': phone
        }
        url = branch_io.create_url(venue.venue_id, share.key.id(), branch_io.GIFT, branch_io.SMS, user_agent, recipient=recipient)
        share.urls = [url]
        share.put()
        gift.share_id = share.key.id()
        gift.put()
        self.render_json({
            'success': True,
            'text': (u'%s, разреши угостить тебя чашкой кофе. '
                     u'Чтобы получить ее, пройди по ссылке %s, установи приложение Даблби. '
                     u'Закажи в любой кофейне из списка любой напиток и расплатись подарочной кружкой.') %
                    (name, url)
        })

    def post(self):
        venue_id = self.request.get('venue_id')
        venue = Venue.venue_by_id(venue_id)
        if not venue:
            self.abort(400)
        if not venue.venue_id in config.GIFT_BRANCH_VENUES:
            self.abort(403)
        customer_id = self.request.get('customer_id')
        customer = Customer.customer_by_customer_id(customer_id)
        if not customer:
            self.abort(400)
        recipient_phone = "".join(c for c in self.request.get('recipient_phone') if '0' <= c <= '9')
        recipient_name = self.request.get('recipient_name')
        payment_type_id = self.request.get('payment_type_id')
        payment_type = venue.get_payment_type(payment_type_id)
        if payment_type.available:
            if payment_type.type_id == int(PaymentType.CARD):
                alpha_client_id = self.request.get('alpha_client_id')
                binding_id = self.request.get('binding_id')
                return_url = self.request.get('return_url')

                #order_id = "gift_%s_%s" % (client_id, int(time.time()))
                #success, result = alfa_bank.create_simple(self.BONUS_SUM, order_id, return_url, alpha_client_id)
                #if success:
                #    success, error = alfa_bank.hold_and_check(result, binding_id)
                #else:
                #    error = result
                #if not success:
                #    self.send_error(error)
                #else:
                #    gift = SharedGift(client_id=client_id, total_sum=self.BONUS_SUM, order_id=order_id,
                #                      payment_type_id=payment_type_id, payment_id=result)
                #    self.success(customer, gift=gift, name=recipient_name, phone=recipient_phone)
            elif payment_type.type_id == int(PaymentType.CASH):  # TODO: order id? payment_id?
                gift = SharedGift(customer=customer.key, total_sum=self.BONUS_SUM, payment_type_id=payment_type_id)
                self.success(venue, customer, gift=gift, name=recipient_name, phone=recipient_phone)
            else:
                self.send_error(u'Данный вид оплаты не поддерживается')
        else:
            self.send_error(u'Данный вид оплаты недоступен')