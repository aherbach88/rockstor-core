"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
This file is part of RockStor.

RockStor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

RockStor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""


from rest_framework import status
from rest_framework.test import APITestCase
from system.services import systemctl
from storageadmin.models import SambaShare
import mock
from mock import patch
from storageadmin.tests.test_api import APITestMixin

class SambaTests(APITestMixin, APITestCase):
    fixtures = ['fix2.json']
    BASE_URL = '/api/samba'

    @classmethod
    def setUpClass(cls):
        super(SambaTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_share = patch('storageadmin.views.samba.mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()
        cls.mock_mount_share.return_value = 'foo'

        cls.patch_is_share_mounted = patch('storageadmin.views.samba.is_share_mounted')
        cls.mock_is_share_mounted = cls.patch_is_share_mounted.start()
        cls.mock_is_share_mounted.return_value = False

        cls.patch_status = patch('storageadmin.views.samba.status')
        cls.mock_status = cls.patch_status.start()
        cls.mock_status.return_value = 'sts'

        cls.patch_restart_samba = patch('storageadmin.views.samba.restart_samba')
        cls.mock_status = cls.patch_restart_samba.start()

        cls.patch_refresh_smb_config = patch('storageadmin.views.samba.refresh_smb_config')
        cls.mock_refresh_smb_config = cls.patch_refresh_smb_config.start()
        cls.mock_refresh_smb_config.return_value = 'smbconfig'


    @classmethod
    def tearDownClass(cls):
        super(SambaTests, cls).tearDownClass()


    def test_get(self):
        """
        Test GET request
        1. Get base URL
        """
        self.get_base(self.BASE_URL)

    @mock.patch('storageadmin.views.samba.User')
    @mock.patch('storageadmin.views.samba.Disk')
    def test_post_requests(self, mock_disk,  mock_user):
        """
        invalid samba api operations
        1. Create a samba without providing share names
        2. Create a samba export for the share that is already been exported
        """

        # create samba export with no share names
        data = {'browsable': 'yes','guest_ok': 'yes','read_only': 'yes', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)

        e_msg = ('Must provide share names')
        self.assertEqual(response.data['detail'], e_msg)


        # create samba export
        # we use 'share2' which is available from the fixture, fix2.json
        data = {'shares': ('share2', ), 'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes', 'admin_users':'usr'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # @todo: create samba exports for multiple(3) shares at once

        # create samba export with the share that is already been exported above
        data = {'shares': ('share2', ), 'browsable': 'no', 'guest_ok': 'yes', 'read_only': 'yes'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ('Share(share2) is already exported via Samba')
        self.assertEqual(response.data['detail'], e_msg)

    @mock.patch('storageadmin.views.samba.User')
    @mock.patch('storageadmin.views.samba.Disk')
    def test_put_requests(self, mock_disk, mock_user):
        """
        1. Edit samba that does not exists
        2. Edit samba
        """
        # edit samba that does not exist
        smb_id = 3
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes', 'admin_users':'usr'}
        response = self.client.put('%s/%d' % (self.BASE_URL, smb_id), data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ('Samba export for the id(3) does not exist')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes', 'admin_users':'usr'}
        response = self.client.put('%s/1' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)



    @mock.patch('storageadmin.views.samba.SambaCustomConfig')
    @mock.patch('storageadmin.views.samba.SambaShare')
    def test_delete_requests(self, mock_samba, mock_sambaCustomConfig):

        """
        1. Delete samba that does not exist
        2. Delete samba
        """
        # Delete samba that does nor exists
        smb_id = 3
        mock_samba.objects.get.side_effect = SambaShare.DoesNotExist
        response = self.client.delete('%s/%d' % (self.BASE_URL, smb_id))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ('Samba export for the id(3) does not exist')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        mock_samba.objects.get.side_effect = None
        mock_sambaCustomConfig.objects.filter.side_effect = None
        response = self.client.delete('%s/4' % (self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
