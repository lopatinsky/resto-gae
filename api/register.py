import json
from models.specials import Share, SharedBonus

__author__ = 'dvpermyakov'

from base import BaseHandler


class RegisterHandler(BaseHandler):
    def post(self):

        share_data = self.request.get('share_data')
        if share_data:
            share_data = json.loads(share_data)
            share_id = share_data.get('share_id')
            share = None
            if share_id:
                share = Share.get_by_id(share_id)
            if share:
                if share.share_type == Share.INVITATION:
                    if not request_client_id:
                        SharedBonus(sender=share.sender, recipient=client.key, share_id=share.key.id()).put()