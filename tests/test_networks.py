# -*- coding: utf-8 -*-

""" Test functions in networks.py.
"""

"""License:
    Copyright 2020 The Cytoscape Consortium

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
    documentation files (the "Software"), to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
    and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or substantial portions
    of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
    WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
    OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import unittest
import math
import pandas as df
import time
import re
import os

from test_utils import *


class NetworkTests(unittest.TestCase):
    def setUp(self):
        try:
            close_session(False)
#            delete_all_networks()
        except:
            pass

    def tearDown(self):
        pass

    
    @print_entry_exit
    def test_set_current_network(self):
        # Initialization
        load_test_session()
        load_test_network('data/yeastHighQuality.sif', make_current=False)

        # Verify that flavors of bad titles are caught
        self.assertRaises(CyError, set_current_network, 'bad title')
        self.assertRaises(CyError, set_current_network, 500)  # bad SUID

        def set_and_check(new_network_name, new_network_suid):
            res = set_current_network(new_network_name)
            self.assertSequenceEqual(res, {})
            self.assertEqual(get_network_suid(), new_network_suid)
            res = set_current_network()
            self.assertSequenceEqual(res, {})
            self.assertEqual(get_network_suid(), new_network_suid)

        # Assume there are two networks: galFiltered.sif and BINDhuman.sif
        gal_suid = get_network_suid('galFiltered.sif')
        yeast_suid = get_network_suid('yeastHighQuality.sif')

        # Verify that different networks can be selected
        set_and_check('yeastHighQuality.sif', yeast_suid)
        set_and_check('galFiltered.sif', gal_suid)

    @unittest.skip('test_rename_network: Renaming non-current network needs fixing in Cytoscape')
    @print_entry_exit
    def test_rename_network(self):
        # Initialization
        load_test_session()
        load_test_network('data/yeastHighQuality.sif', make_current=False)

        def rename_and_check(new_title, network_suid, network=None):
            res = rename_network(new_title, network)
            self.assertEqual(res['network'], network_suid)
            self.assertEqual(res['title'], new_title)

            new_suid = get_network_suid(new_title)
            self.assertEqual(new_suid, network_suid)

        self.assertRaises(CyError, rename_network, 'junk', 'doesnt exist')

        yeast_suid = get_network_suid('yeastHighQuality.sif')
        gal_suid = get_network_suid('galFiltered.sif')

        # Verify that networks are properly renamed
        set_current_network('galFiltered.sif')
        rename_and_check('newcurrent', gal_suid)
        rename_and_check('newcurrent1', gal_suid, 'newcurrent')
        rename_and_check('newsuid', gal_suid, gal_suid)

        # This fails because of a Cytoscape error ... should be able to rename
        # non-current network, but Cytoscape fails on this
        rename_and_check('newyeast', yeast_suid, 'yeastHighQuality.sif')

    
    @print_entry_exit
    def test_get_network_count(self):
        def check(count):
            res = get_network_count()
            self.assertIsInstance(res, int)
            self.assertEqual(res, count)

        check(0)

        # Initialization
        load_test_session()
        check(1)

    
    @print_entry_exit
    def test_get_network_suid(self):
        self.assertRaises(CyError, get_network_suid, '')

        # Initialization
        load_test_session()

        # Verify that various flavors of bad network titles are caught
        self.assertRaises(CyError, get_network_suid, 'bad title')
        self.assertRaises(CyError, get_network_suid, 500)  # bad SUID

        # Verify that aliases for the same network produce the same SUID
        res = get_network_suid()
        self.assertIsInstance(res, int)

        self.assertEqual(get_network_suid('current'), res)
        self.assertEqual(get_network_suid('galFiltered.sif'), res)
        self.assertEqual(get_network_suid(res), res)

    
    @print_entry_exit
    def test_get_network_name(self):
        self.assertRaises(CyError, get_network_name, '')

        # Initialization
        load_test_session()
        self.assertRaises(CyError, get_network_name, 'bad title')
        self.assertRaises(IndexError, get_network_name, 500)  # bad SUID

        res = get_network_name()
        self.assertIsInstance(res, str)

        # Verify that aliases for the same network produce the same name
        self.assertEqual(get_network_name('current'), res)
        self.assertEqual(get_network_name('galFiltered.sif'), res)
        self.assertEqual(get_network_name(res), res)

    
    @print_entry_exit
    def test_get_network_list(self):
        # Initialization
        load_test_session()
        load_test_network('data/yeastHighQuality.sif', make_current=False)

        # Verify that all networks are present (in any order)
        self.assertSetEqual(set(get_network_list()), set(['yeastHighQuality.sif', 'galFiltered.sif']))

        # Verify that when there are no networks, no networks are returned
        delete_all_networks()
        self.assertListEqual(get_network_list(), [])

    @unittest.skipIf(skip_for_ui(), 'Avoiding test that requires user response')
    @print_entry_exit
    def test_export_network(self):
        # Initialization
        load_test_session()
        load_test_network('data/yeastHighQuality.sif', make_current=False)

        def check(res):
            self.assertIsNotNone(res['file'])

        input('On the following tests, allow Cytoscape to overwrite network')

        # For these SIF tests, always answer Cytoscape verification message to allow overwrite
        gal_filename = 'galFiltered.sif'
        if os.path.exists(gal_filename):
            os.remove(gal_filename)
        check(export_network())
        self.assertTrue(os.path.exists(gal_filename))
        check(export_network(filename=gal_filename, network='yeastHighQuality.sif', type='sif'))
        self.assertTrue(os.path.exists(gal_filename))

        # For these CYS tests, always answer Cytoscape verification message to allow overwrite
        net_name = get_network_name()
        full_file_name = net_name + '.cys'
        if os.path.exists(full_file_name):
            os.remove(full_file_name)
        self.assertDictEqual(export_network(type='cys'), {})
        self.assertTrue(os.path.exists(full_file_name))
        self.assertDictEqual(export_network(filename=net_name, network='yeastHighQuality.sif', type='cys'), {})
        self.assertTrue(os.path.exists(full_file_name))
        os.remove(full_file_name)

        # Verify that bad network is caught
        self.assertRaises(CyError, export_network, filename='test', network='totallybogus', type='sif')

        # For this test, answer Cytoscape verification message to DISALLOW overwrite
        input('On on the following test, DISALLOW network overwrite')
        self.assertRaises(CyError, export_network)
        os.remove('galFiltered.sif')

    @print_entry_exit
    def test_delete_network(self):
        # Initialization
        load_test_session()
        load_test_network('data/yeastHighQuality.sif', make_current=False)

        # Verify that deleting a network actually deletes it
        self.assertEqual(delete_network('yeastHighQuality.sif'), '')
        self.assertListEqual(get_network_list(), ['galFiltered.sif'])
        self.assertRaises(CyError, delete_network, 'yeastHighQuality.sif')

    
    @print_entry_exit
    def test_delete_all_networks(self):
        # Initialization
        load_test_session()
        load_test_network('data/yeastHighQuality.sif', make_current=False)

        # Verify that when all networks are deleted, there are none left
        self.assertEqual(get_network_count(), 2)
        self.assertEqual(delete_all_networks(), '')
        self.assertEqual(get_network_count(), 0)

        # Verify that deleting no networks succeeds
        self.assertEqual(delete_all_networks(), '')

    
    @print_entry_exit
    def test_get_first_neighbors(self):
        # Initialization
        load_test_session()
        df_all_nodes = get_table_columns(columns='name')
        suid_YBR020W = df_all_nodes[df_all_nodes['name'] == 'YBR020W'].index[0]
        suid_YGL035C = df_all_nodes[df_all_nodes['name'] == 'YGL035C'].index[0]

        test_select_nodes(['MIG1', 'GAL1'])
        self.assertSetEqual(set(get_first_neighbors(node_names=None, as_nested_list=False)), set(
            ['YGL035C', 'YOL051W', 'YPL248C', 'YML051W', 'YLR044C', 'YLR377C', 'YIL162W', 'YBR019C', 'YBR020W',
             'YKL109W', 'YKL074C', 'YDR009W', 'YDR146C']))

        # Verify that the two nested lists are equivalent
        nested_neighbor_list = get_first_neighbors(node_names=None, as_nested_list=True)
        expected_list = [['YBR020W', ['YGL035C', 'YOL051W', 'YPL248C', 'YML051W']], ['YGL035C',
                                                                                     ['YLR044C', 'YLR377C', 'YIL162W',
                                                                                      'YBR019C', 'YBR020W', 'YPL248C',
                                                                                      'YKL109W', 'YKL074C', 'YDR009W',
                                                                                      'YDR146C']]]
        for nested_list in nested_neighbor_list:
            found = [nested_list[0] == expected[0] and set(nested_list[1]) == set(expected[1]) for expected in
                     expected_list]
            self.assertIn(True, found)

        # Verify that when no nodes are passed in, the selected nodes are used
        test_select_nodes([])
        self.assertIsNone(get_first_neighbors())

        # Verify that regardless of selection, when a node list is passed in, it's used
        self.assertSetEqual(set(get_first_neighbors(['YBR020W', 'YGL035C'], as_nested_list=False)), set(
            ['YGL035C', 'YOL051W', 'YPL248C', 'YML051W', 'YLR044C', 'YLR377C', 'YIL162W', 'YBR019C', 'YBR020W',
             'YKL109W', 'YKL074C', 'YDR009W', 'YDR146C']))

        # Verify that regardless of selection, when a node string list is passed in, it's used
        self.assertSetEqual(set(get_first_neighbors('YBR020W, YGL035C', as_nested_list=False)), set(
            ['YGL035C', 'YOL051W', 'YPL248C', 'YML051W', 'YLR044C', 'YLR377C', 'YIL162W', 'YBR019C', 'YBR020W',
             'YKL109W', 'YKL074C', 'YDR009W', 'YDR146C']))

        # Verify that regardless of selection, when a single node string is passed in, it's used
        self.assertSetEqual(set(get_first_neighbors('YBR020W', as_nested_list=False)),
                            set(['YGL035C', 'YOL051W', 'YPL248C', 'YML051W']))

        # Verify that regardless of selection, when a SUID list is passed in, it's used
        self.assertSetEqual(set(get_first_neighbors([suid_YBR020W, suid_YGL035C], as_nested_list=False)), set(
            ['YGL035C', 'YOL051W', 'YPL248C', 'YML051W', 'YLR044C', 'YLR377C', 'YIL162W', 'YBR019C', 'YBR020W',
             'YKL109W', 'YKL074C', 'YDR009W', 'YDR146C']))

        # Verify that regardless of selection, when a SUID string list is passed in, it's used
        self.assertSetEqual(set(get_first_neighbors(str([suid_YBR020W, suid_YGL035C])[1:-1], as_nested_list=False)), set(
            ['YGL035C', 'YOL051W', 'YPL248C', 'YML051W', 'YLR044C', 'YLR377C', 'YIL162W', 'YBR019C', 'YBR020W',
             'YKL109W', 'YKL074C', 'YDR009W', 'YDR146C']))

        # Verify that regardless of selection, when a single SUID is passed in, it's used
        self.assertSetEqual(set(get_first_neighbors(suid_YBR020W, as_nested_list=False)),
                            set(['YGL035C', 'YOL051W', 'YPL248C', 'YML051W']))

        self.assertIsNone(get_first_neighbors([], as_nested_list=False))

        # TODO: test case of node_names being a single (str) node

    
    @print_entry_exit
    def test_get_node_count(self):
        # Initialization
        load_test_session()

        # Verify that the network reports expected node count
        self.assertEqual(get_node_count(), 330)

    
    @print_entry_exit
    def test_get_all_nodes(self):
        # Initialization
        load_test_session()

        # Verif that the network reports expected nodes
        self.assertSetEqual(set(get_all_nodes()), set(
            ['YDL194W', 'YDR277C', 'YBR043C', 'YPR145W', 'YER054C', 'YBR045C', 'YBL079W', 'YLR345W', 'YIL052C',
             'YER056CA', 'YNL069C', 'YDL075W', 'YFR014C', 'YGR136W', 'YDL023C', 'YBR170C', 'YGR074W', 'YGL202W',
             'YLR197W', 'YDL088C', 'YOR215C', 'YPR010C', 'YMR117C', 'YML114C', 'YNL036W', 'YOR212W', 'YDR070C',
             'YNL164C', 'YGR046W', 'YLR153C', 'YIL070C', 'YPR113W', 'YER081W', 'YGR088W', 'YDR395W', 'YGR085C',
             'YER124C', 'YMR005W', 'YDL030W', 'YER079W', 'YDL215C', 'YIL045W', 'YPR041W', 'YOR120W', 'YIL074C',
             'YDR299W', 'YHR005C', 'YLR452C', 'YMR255W', 'YBR274W', 'YHR084W', 'YBL050W', 'YBL026W', 'YJL194W',
             'YLR258W', 'YGL134W', 'YHR055C', 'YHR053C', 'YPR124W', 'YNL135C', 'YER052C', 'YLR284C', 'YHR198C',
             'YPL240C', 'YPR102C', 'YLR075W', 'YKL161C', 'YAR007C', 'YIL160C', 'YDL078C', 'YDR142C', 'YDR244W',
             'YLR432W', 'YDR167W', 'YLR175W', 'YNL117W', 'YOR089C', 'YPR167C', 'YNL214W', 'YBR135W', 'YML007W',
             'YER110C', 'YGL153W', 'YLR191W', 'YOL149W', 'YMR044W', 'YOR362C', 'YER102W', 'YOL059W', 'YBR190W',
             'YER103W', 'YPR110C', 'YNL113W', 'YDR354W', 'YER090W', 'YKL211C', 'YDR146C', 'YER111C', 'YOR039W',
             'YML024W', 'YIL113W', 'YLL019C', 'YDR009W', 'YML051W', 'YHR071W', 'YPL031C', 'YML123C', 'YER145C',
             'YMR058W', 'YJL190C', 'YML074C', 'YOR355W', 'YFL038C', 'YIL162W', 'YBR050C', 'YMR311C', 'YOR315W',
             'YOR178C', 'YER133W', 'YOR290C', 'YFR037C', 'YFR034C', 'YAL040C', 'YPL222W', 'YGR048W', 'YMR291W',
             'YGR009C', 'YMR183C', 'YDR100W', 'YGL161C', 'YPL131W', 'YDL063C', 'YNL167C', 'YHR115C', 'YEL041W',
             'YDL113C', 'YJL036W', 'YBR109C', 'YOL016C', 'YKL001C', 'YNL311C', 'YLR319C', 'YPR062W', 'YPL111W',
             'YDL236W', 'YNL189W', 'YBL069W', 'YGL073W', 'YBR072W', 'YLR321C', 'YPR048W', 'YNL199C', 'YPL075W',
             'YHR179W', 'YCL040W', 'YFL039C', 'YDL130W', 'YDR382W', 'YJR066W', 'YKL204W', 'YNL154C', 'YNL047C',
             'YNL116W', 'YHR135C', 'YML064C', 'YKL074C', 'YLR340W', 'YDL081C', 'YGL166W', 'YLL028W', 'YDR174W',
             'YDR335W', 'YLR214W', 'YMR021C', 'YLR377C', 'YER065C', 'YJL089W', 'YHR030C', 'YPL089C', 'YGL208W',
             'YGL115W', 'YLR310C', 'YNL098C', 'YGR019W', 'YPR035W', 'YER040W', 'YGL008C', 'YOR036W', 'YDR323C',
             'YBL005W', 'YBR160W', 'YKL101W', 'YOL156W', 'YJL219W', 'YLL021W', 'YOL136C', 'YJL203W', 'YNR007C',
             'YFL026W', 'YJL157C', 'YNL145W', 'YDR461W', 'YGR108W', 'YKR097W', 'YJL159W', 'YIL015W', 'YMR043W',
             'YKL109W', 'YBR217W', 'YHR171W', 'YPL149W', 'YKL028W', 'YDR311W', 'YBL021C', 'YGL237C', 'YEL039C',
             'YJR048W', 'YML054C', 'YLR256W', 'YOR303W', 'YJR109C', 'YGR058W', 'YLR229C', 'YDR309C', 'YOR264W',
             'YLR116W', 'YNL312W', 'YML032C', 'YKL012W', 'YNL236W', 'YNL091W', 'YDR184C', 'YIL143C', 'YKR099W',
             'YIR009W', 'YBR018C', 'YPL248C', 'YLR081W', 'YBR020W', 'YGL035C', 'YOL051W', 'YBR019C', 'YJR060W',
             'YDR103W', 'YLR362W', 'YDR032C', 'YCL032W', 'YLR109W', 'YHR141C', 'YMR138W', 'YMR300C', 'YOL058W',
             'YBR248C', 'YOR202W', 'YMR108W', 'YEL009C', 'YBR155W', 'YMR186W', 'YGL106W', 'YOR326W', 'YMR309C',
             'YOR361C', 'YIL105C', 'YLR134W', 'YER179W', 'YOR310C', 'YDL014W', 'YPR119W', 'YLR117C', 'YGL013C',
             'YCR086W', 'YDR412W', 'YPL201C', 'YER062C', 'YOR327C', 'YER143W', 'YAL030W', 'YOL086C', 'YDR050C',
             'YOL127W', 'YIL069C', 'YER074W', 'YBR093C', 'YDR171W', 'YCL030C', 'YNL301C', 'YOL120C', 'YLR044C',
             'YIL133C', 'YHR174W', 'YGR254W', 'YCR012W', 'YNL216W', 'YAL038W', 'YNL307C', 'YDL013W', 'YER116C',
             'YNR053C', 'YLR264W', 'YEL015W', 'YNL050C', 'YNR050C', 'YJR022W', 'YOR167C', 'YER112W', 'YCL067C',
             'YBR112C', 'YCR084C', 'YIL061C', 'YGR203W', 'YJL013C', 'YGL229C', 'YJL030W', 'YGR014W', 'YPL211W',
             'YGL044C', 'YOL123W', 'YAL003W', 'YFL017C', 'YDR429C', 'YMR146C', 'YLR293C', 'YBR118W', 'YPR080W',
             'YLR249W', 'YOR204W', 'YGL097W', 'YGR218W', 'YGL122C', 'YKR026C']))

    
    @print_entry_exit
    def test_add_cy_nodes(self):
        # Initialization
        load_test_session()
        start_node_count = get_node_count()

        # Verify that two nodes are actually added
        res12 = add_cy_nodes(['newnode1', 'newnode2'], skip_duplicate_names=False)
        self.assertEqual(len(res12), 2)
        self.assertEqual(res12[0]['name'], 'newnode1')
        self.assertEqual(res12[1]['name'], 'newnode2')
        self.assertEqual(get_node_count(), start_node_count + 2)

        # Verify that adding a duplicate node is ignored, but adding a new node works
        res23 = add_cy_nodes(['newnode2', 'newnode3'], skip_duplicate_names=True)
        self.assertEqual(len(res23), 1)
        self.assertEqual(res23[0]['name'], 'newnode3')
        self.assertEqual(get_node_count(), start_node_count + 3)

        # Verify that adding only duplicate nodes is ignored, too
        res23x = add_cy_nodes(['newnode2', 'newnode3'], skip_duplicate_names=True)
        self.assertEqual(len(res23x), 0)
        self.assertEqual(get_node_count(), start_node_count + 3)

        # Re-initialize to try non-list node lists
        load_test_session()

        # Verify that one node is actually added
        res1 = add_cy_nodes('newnode1', skip_duplicate_names=False)
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0]['name'], 'newnode1')
        self.assertEqual(get_node_count(), start_node_count + 1)

        # Verify that two nodes are actually added
        res23 = add_cy_nodes('newnode2, newnode3', skip_duplicate_names=False)
        self.assertEqual(len(res23), 2)
        self.assertEqual(res23[0]['name'], 'newnode2')
        self.assertEqual(res23[1]['name'], 'newnode3')
        self.assertEqual(get_node_count(), start_node_count + 3)


    
    @print_entry_exit
    def test_add_cy_edges(self):
        # Initialization
        load_test_session()
        start_edge_count = get_edge_count()
        df = get_table_columns('node', ['name'], 'default')

        def check_edge(edge, source_name, target_name):
            self.assertIsInstance(edge, dict)
            source_suid = df[df.name.eq(source_name)].index[0]
            target_suid = df[df.name.eq(target_name)].index[0]
            self.assertEqual(edge['source'], source_suid)
            self.assertEqual(edge['target'], target_suid)
            self.assertIsNotNone(edge['SUID'])

        # Verify that a single edge is added
        res = add_cy_edges(['YLR075W', 'YKL028W'])
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        check_edge(res[0], 'YLR075W', 'YKL028W')
        self.assertEqual(get_edge_count(), start_edge_count + 1)

        # Verify that three more edges are added
        res = add_cy_edges([['YKL028W', 'YJR066W'], ['YJR066W', 'YLR452C'], ['YGR046W', 'YLR452C']])
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 3)
        check_edge(res[0], 'YKL028W', 'YJR066W')
        check_edge(res[1], 'YJR066W', 'YLR452C')
        check_edge(res[2], 'YGR046W', 'YLR452C')
        self.assertEqual(get_edge_count(), start_edge_count + 4)

    
    @print_entry_exit
    def test_get_edge_count(self):
        # Initialization
        load_test_session()

        # Verify the expected edge count
        self.assertEqual(get_edge_count(), 359)

    
    @print_entry_exit
    def test_get_edge_info(self):
        # Initialization
        load_test_session()

        def check_single_edge_info(edge_info, source_name, target_name, edge_name, betweenness):
            source_suid = node_name_to_node_suid(source_name)[0]
            target_suid = node_name_to_node_suid(target_name)[0]
            edge_suid = edge_name_to_edge_suid(edge_name)[0]
            self.assertIsInstance(edge_info, dict)
            self.assertEqual(edge_info['source'], source_suid)
            self.assertEqual(edge_info['target'], target_suid)
            self.assertEqual(edge_info['SUID'], edge_suid)
            self.assertEqual(edge_info['shared name'], edge_name)
            self.assertEqual(edge_info['shared interaction'], 'pp')
            self.assertEqual(edge_info['name'], edge_name)
            self.assertEqual(edge_info['selected'], False)
            self.assertEqual(edge_info['interaction'], 'pp')
            self.assertEqual(edge_info['EdgeBetweenness'], betweenness)

        def check_list_edge_info(edge_list, expected_edge_list):
            # Check edge list ... edges can be either names or SUIDs
            res = get_edge_info(edge_list)
            self.assertIsInstance(res, list)
            self.assertEqual(len(res), len(expected_edge_list))
            suid_list = []
            for edge_info, expected_edge in zip(res, expected_edge_list):
                check_single_edge_info(edge_info, expected_edge['source_name'], expected_edge['target_name'],
                                       expected_edge['edge_name'], expected_edge['betweenness'])
                suid_list.append(edge_info['SUID'])
            return suid_list

        def check_named_edge_info(edge_list, expected_edge_list):
            # Check edge list ... assume it's edge names
            suid_list = check_list_edge_info(edge_list, expected_edge_list)

            # Check edge list ... use SUIDs for edges
            check_list_edge_info(suid_list, expected_edge_list)

            # Check edge list as a string instead of a named list
            edge_list_str = edge_list[0]
            for x in range(1, len(edge_list)):
                edge_list_str += ',' + edge_list[x]
            suid_list = check_list_edge_info(edge_list_str, expected_edge_list)

            # Check edge list as a string of SUIDs instead of a named list
            edge_list_suid_str = str(suid_list)[1:-1]
            check_list_edge_info(edge_list_suid_str, expected_edge_list)

        # Verify that a list containing an edge in a list returns valid edge information
        check_named_edge_info(['YDR277C (pp) YDL194W'], [{'source_name': 'YDR277C', 'target_name': 'YDL194W', 'edge_name': 'YDR277C (pp) YDL194W', 'betweenness': 496.0}])

        # Verify that a list containing multiple edges in a list returns valid edge information
        check_named_edge_info(['YDR277C (pp) YDL194W', 'YDR277C (pp) YJR022W'],
                              [{'source_name': 'YDR277C', 'target_name': 'YDL194W', 'edge_name': 'YDR277C (pp) YDL194W', 'betweenness': 496.0},
                               {'source_name': 'YDR277C', 'target_name': 'YJR022W', 'edge_name': 'YDR277C (pp) YJR022W', 'betweenness': 988.0}])

        # Verify the error when a bad edge is requested
        self.assertRaises(CyError, get_edge_info, 'junk')
        self.assertRaises(CyError, get_edge_info, -1)

    @print_entry_exit
    def test_get_all_edges(self):
        # Initialization
        load_test_session()

        # Verify that the expected number of edges is returned
        res = get_all_edges()
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 359)

    
    @print_entry_exit
    def test_clone_network(self):
        # Initialization
        load_test_session()
        start_suid = get_network_suid()

        # Verify that a network clone is plausible
        self._check_cloned_network(clone_network(), start_suid, get_network_name(start_suid),
                                   get_node_count(start_suid), get_edge_count(start_suid))

    
    @print_entry_exit
    def test_create_subnet(self):
        # Initialization
        load_test_session()
        base_suid = get_network_suid()
        base_name = get_network_name(base_suid)
        node_common_list_4 = ['RAP1', 'HIS4', 'PDC1', 'RPL18A']
        node_common_str_4 = ', '.join(node_common_list_4)
        node_name_str_4 = 'YCL030C,YOL120C,YNL216W,YLR044C'
        node_suid_list_4 = node_name_to_node_suid(node_name_str_4)
        node_suid_str_4 = str(node_suid_list_4)[1:-1]

        # Verify that a creating a subnet containing all nodes produces a plausible copy
        self._check_cloned_network(create_subnetwork(nodes='all', network=base_suid), base_suid, base_name,
                                   get_node_count(base_suid), get_edge_count(base_suid))

        # Verify that creating a subset subnet via list of common node names produces a plausible copy
        self._check_cloned_network(
            create_subnetwork(nodes=node_common_list_4, nodes_by_col='COMMON',
                              subnetwork_name=base_name + 'xx', network=base_suid), base_suid, base_name, 4, 3)

        # Verify that creating a subset subnet via string list of common node names produces a plausible copy
        self._check_cloned_network(
            create_subnetwork(nodes=node_common_str_4, nodes_by_col='COMMON',
                              subnetwork_name=base_name + 'yy', network=base_suid), base_suid, base_name, 4, 3)

        # Verify that creating a subset subnet via string list of node names produces a plausible copy
        self._check_cloned_network(
            create_subnetwork(nodes=node_name_str_4, nodes_by_col='name',
                              subnetwork_name=base_name + 'qq', network=base_suid), base_suid, base_name, 4, 3)

        # Verify that creating a subset subnet via single common node name produces a plausible copy
        self._check_cloned_network(
            create_subnetwork(nodes='RAP1', nodes_by_col='COMMON',
                              subnetwork_name=base_name + 'zz', network=base_suid), base_suid, base_name, 1, 0)

        # Verify that creating a subset subnet via list of node SUIDs produces a plausible copy
        self._check_cloned_network(
            create_subnetwork(nodes=node_suid_list_4,
                              subnetwork_name=base_name + 'aa', network=base_suid), base_suid, base_name, 4, 3)

        # Verify that creating a subset subnet via string list of node SUIDs produces a plausible copy
        self._check_cloned_network(
            create_subnetwork(nodes=node_suid_str_4,
                              subnetwork_name=base_name + 'bb', network=base_suid), base_suid, base_name, 4, 3)

        # Verify that creating a subset subnet via single node SUID produces a plausible copy
        self._check_cloned_network(
            create_subnetwork(nodes=node_suid_list_4[0],
                              subnetwork_name=base_name + 'cc', network=base_suid), base_suid, base_name, 1, 0)

        # TODO: Add tests that create subnet by specifying edges


    
    @print_entry_exit
    def test_create_network_from_data_frames(self):
        node_data = {'id': ["node 0", "node 1", "node 2", "node 3"],
                     'group': ["A", "A", "B", "B"],
                     'score': [20, 10, 15, 5]}
        nodes = df.DataFrame(data=node_data, columns=['id', 'group', 'score'])
        edge_data = {'source': ["node 0", "node 0", "node 0", "node 2"],
                     'target': ["node 1", "node 2", "node 3", "node 3"],
                     'interaction': ["inhibits", "interacts", "activates", "interacts"],
                     'weight': [5.1, 3.0, 5.2, 9.9]}
        edges = df.DataFrame(data=edge_data, columns=['source', 'target', 'interaction', 'weight'])

        # Verify that a network can be created containing dataframe encoding both nodes and edges
        res = create_network_from_data_frames(nodes, edges, title='From node & edge dataframe')
        suid_1 = res['networkSUID']
        self.assertEqual(get_network_name(suid_1), 'From node & edge dataframe')
        self.assertEqual(get_node_count(suid_1), 4)
        self.assertEqual(get_edge_count(suid_1), 4)
        self.assertSetEqual(set(get_all_nodes(suid_1)), set(['node 0', 'node 1', 'node 2', 'node 3']))
        self.assertSetEqual(set(get_all_edges(suid_1)), set(
            ['node 0 (inhibits) node 1', 'node 0 (interacts) node 2', 'node 0 (activates) node 3',
             'node 2 (interacts) node 3']))
        self.assertSetEqual(set(get_table_column_names('node', network=suid_1)),
                            set(['SUID', 'shared name', 'id', 'score', 'group', 'name', 'selected']))
        self.assertSetEqual(set(get_table_column_names('edge', network=suid_1)), set(
            ['SUID', 'shared name', 'shared interaction', 'source', 'target', 'data.key.column', 'weight', 'name',
             'selected', 'interaction']))
        self.assertDictEqual(get_table_column_types('node', network=suid_1),
                             {'SUID': 'Long', 'shared name': 'String', 'id': 'String', 'score': 'Integer',
                              'group': 'String', 'name': 'String', 'selected': 'Boolean'})
        self.assertDictEqual(get_table_column_types('edge', network=suid_1),
                             {'SUID': 'Long', 'shared name': 'String', 'shared interaction': 'String',
                              'source': 'String', 'target': 'String', 'data.key.column': 'Integer', 'weight': 'Double',
                              'name': 'String', 'selected': 'Boolean', 'interaction': 'String'})

        # Verify that a network can be created from a dataframe containing just edges
        res = create_network_from_data_frames(edges=edges, collection='Another collection',
                                                           title='From just edge dataframe')
        suid_2 = res['networkSUID']
        self.assertEqual(get_network_name(suid_2), 'From just edge dataframe')
        self.assertEqual(get_node_count(suid_2), 4)
        self.assertEqual(get_edge_count(suid_2), 4)
        self.assertSetEqual(set(get_all_nodes(suid_2)), set(['node 0', 'node 1', 'node 2', 'node 3']))
        self.assertSetEqual(set(get_all_edges(suid_2)), set(
            ['node 0 (inhibits) node 1', 'node 0 (interacts) node 2', 'node 0 (activates) node 3',
             'node 2 (interacts) node 3']))
        self.assertSetEqual(set(get_table_column_names('node', network=suid_2)),
                            set(['SUID', 'shared name', 'id', 'name', 'selected']))
        self.assertSetEqual(set(get_table_column_names('edge', network=suid_2)), set(
            ['SUID', 'shared name', 'shared interaction', 'source', 'target', 'data.key.column', 'weight', 'name',
             'selected', 'interaction']))
        self.assertDictEqual(get_table_column_types('node', network=suid_2),
                             {'SUID': 'Long', 'shared name': 'String', 'id': 'String', 'name': 'String',
                              'selected': 'Boolean'})
        self.assertDictEqual(get_table_column_types('edge', network=suid_2),
                             {'SUID': 'Long', 'shared name': 'String', 'shared interaction': 'String',
                              'source': 'String', 'target': 'String', 'data.key.column': 'Integer', 'weight': 'Double',
                              'name': 'String', 'selected': 'Boolean', 'interaction': 'String'})

        # Verify that a disconnected network can be created from a dataframe containing just nodes
        res = create_network_from_data_frames(nodes=nodes, collection='A third collection',
                                                           title='From just nodes dataframe')
        suid_3 = res['networkSUID']
        self.assertEqual(get_network_name(suid_3), 'From just nodes dataframe')
        self.assertEqual(get_node_count(suid_3), 4)
        self.assertEqual(get_edge_count(suid_3), 0)
        self.assertSetEqual(set(get_all_nodes(suid_3)), set(['node 0', 'node 1', 'node 2', 'node 3']))
        self.assertIsNone(get_all_edges(suid_3))
        self.assertSetEqual(set(get_table_column_names('node', network=suid_3)),
                            set(['SUID', 'shared name', 'id', 'score', 'group', 'name', 'selected']))
        # TODO: Verify that this list of edge columns should be created ... why not source, target?
        self.assertSetEqual(set(get_table_column_names('edge', network=suid_3)),
                            set(['SUID', 'shared name', 'shared interaction', 'name', 'selected', 'interaction']))
        self.assertDictEqual(get_table_column_types('node', network=suid_3),
                             {'SUID': 'Long', 'shared name': 'String', 'id': 'String', 'score': 'Integer',
                              'group': 'String', 'name': 'String', 'selected': 'Boolean'})
        self.assertDictEqual(get_table_column_types('edge', network=suid_3),
                             {'SUID': 'Long', 'shared name': 'String', 'shared interaction': 'String', 'name': 'String',
                              'selected': 'Boolean', 'interaction': 'String'})

        # Verify that when no edges or nodes are passed in, an error occurs
        self.assertRaises(CyError, create_network_from_data_frames)
    
    @print_entry_exit
    def test_import_network_from_file(self):

        # Verify that test network loads from test data directory
        res = import_network_from_file('data/galFiltered.sif')
        self.assertIsInstance(res['networks'], list)
        self.assertEqual(len(res['networks']), 1)
        self.assertIsInstance(res['views'], list)
        self.assertEqual(len(res['views']), 1)

        # Verify that default network loads
        res = import_network_from_file()
        self.assertIsInstance(res['networks'], list)
        self.assertEqual(len(res['networks']), 1)
        self.assertIsInstance(res['views'], list)
        self.assertEqual(len(res['views']), 1)

        self.assertRaises(CyError, import_network_from_file, 'bogus')

    
    @print_entry_exit
    def test_create_igraph_from_network(self):
        # Initialization
        load_test_session()
        all_nodes = get_all_nodes()
        all_edges = get_all_edges()

        i = create_igraph_from_network()

        # verify that all nodes are present
        self.assertEqual(len(i.vs), len(all_nodes))
        self.assertNotIn(False, [v['name'] in all_nodes for v in i.vs])

        # verify that all edges are present
        self.assertEqual(len(i.es), len(all_edges))
        i_edges = [[x['source'], x['target']] for x in i.es]
        self.assertNotIn(False, [re.split("\ \\(.*\\)\ ", x) in i_edges for x in all_edges])

    @print_entry_exit
    def test_create_networkx_from_network(self):
        # Initialization
        load_test_session()
        cyedge_table = tables.get_table_columns('edge')
        cynode_table = tables.get_table_columns('node')
        cynode_table.set_index('name', inplace=True) # Index by 'name' instead of SUID ... drop 'name' from attributes

        # Verify that the networkx returns the right number of rows and columns
        netx = create_networkx_from_network()
        self.assertEqual(netx.number_of_nodes(), len(cynode_table.index))
        self.assertEqual(netx.number_of_edges(), len(cyedge_table.index))

        # Verify that all edges are present, and all of their attributes are correct
        # Note that edge SUIDs are carried to distinguish multiple edges that connect the same nodes
        netx_out_edges = netx.out_edges(data=True, keys=True)
        for src_node, targ_node, edge_suid, edge_attrs in netx_out_edges:
            self.assertDictEqual(edge_attrs, dict(cyedge_table.loc[edge_suid]))

        # Verify that all nodes are present, and all attributes are correct. Note that node YER056CA has 'nan' values,
        # so this verifies that nan is carried into the networkx.
        netx_nodes = netx.nodes(data=True)
        for node_name, node_attrs in netx_nodes:
            self.assertDictEqual(node_attrs, dict(cynode_table.loc[node_name]))

        # Verify that invalid network is caught
        self.assertRaises(CyError, create_networkx_from_network, network='BogusNetwork')

    @print_entry_exit
    def test_create_network_from_networkx(self):
        # Initialization
        load_test_session()
        cyedge_table = tables.get_table_columns('edge')
        cyedge_table.set_index('name', inplace=True) # Index by 'name' instead of SUID ... drop 'name' from attributes
        cyedge_table.sort_index(inplace=True)
        cynode_table = tables.get_table_columns('node')
        cynode_table.set_index('name', inplace=True) # Index by 'name' instead of SUID ... drop 'name' from attributes
        cynode_table.sort_index(inplace=True)

        def compare_table(orig_table, table_name, network):
            # Compare nodes in new Cytoscape network created from NetworkX to those in the original Cytoscape network
            # Start by lining up the dataframe rows for each
            netx_table = tables.get_table_columns(table_name, network=network)
            netx_table.set_index('name', inplace=True)  # Index by 'name' to match up with orig_table
            netx_table.sort_index(inplace=True)

            # Verify that the new network has at least the columns of the original. There may be a few more if they were
            # created for reference.
            orig_table_cols = set(orig_table.columns)
            netx_table_cols = set(netx_table.columns)
            self.assertTrue(orig_table_cols <= netx_table_cols)

            # Create a vector showing which new columns are the same as the original columns. Use .equals() to compare 'nan' properly.
            s = [orig_table[col].equals(netx_table[col]) for col in orig_table_cols - {'SUID'}]
            self.assertFalse(False in s)

        # Get the NetworkX for a known good network galFiltered.sif and send it to Cytoscape as a new network
        netx = create_networkx_from_network()
        netx_suid = create_network_from_networkx(netx)['networkSUID']
        self.assertEqual(netx_suid, get_network_suid()) # Verify that the new network is the selected network

        compare_table(cynode_table, 'node', netx)
        compare_table(cyedge_table, 'edge', netx)

    #   @skip
    @print_entry_exit
    def test_create_network_from_igraph(self):
        # Initialization
        load_test_session()

        # TODO: Consider allowing creation of a network from an empty igraph
        # This will fail but probably should not ... create_network_from_igraph requires nodes and edges, but shouldn't
        #        g = ig.Graph()
        #        create_network_from_igraph(g)

        cur_igraph = create_igraph_from_network()

        new_SUID = create_network_from_igraph(cur_igraph)
        new_igraph = create_igraph_from_network(new_SUID)

        self.assertEqual(get_network_name(new_SUID), 'From igraph')

        # Verify that all nodes in the new network are present along with their attributes. This doesn't test
        # whether there are extra attributes on the nodes ... there well may be because of the extra ``id`` attribute
        # added by ``create_network_from_igraph()``.
        self._check_igraph_attributes(cur_igraph.vs, new_igraph.vs)

        # Verify that all edges in the new network are present along with their attributes. This doesn't test
        # whether there are extra attributes on the edges ... there well may be because of the extra ``data.key`` attribute
        # added by ``create_network_from_igraph()``.
        self._check_igraph_attributes(cur_igraph.es, new_igraph.es)

        # With the nodes and edges verified, see whether they're all connected the same
# Commented out because sometimes isomorphic() never returns (inside joke: the halting problem?)
#        print('calling isomorphic')
#        self.assertTrue(cur_igraph.isomorphic(new_igraph))
#        print('returning from isomorphic')

    # @print_entry_exit
    # def test_choke_memory(self):
    #     # This is to show whether a memory leak occurs ... not part of the API tests
    #     trial = 1
    #     while True:
    #         start = time.clock()
    #         close_session(False)
    #         closed_time = time.clock()
    #         open_session()
    #         print('trial: %5d, close_session seconds: %6.2f, open_session seconds: %6.2f' % (
    #         trial, (closed_time - start), (time.clock() - closed_time)))
    #         trial += 1

    def _check_igraph_attributes(self, original_collection, new_collection):
        def vals_eq(name, e_cur_key, val1, val2):
            eq = type(val1) is type(val2) and \
                 ((val1 == val2) or \
                  (type(val1) is float and math.isnan(val1) and math.isnan(val2)))
            if not eq:
                print('For ' + name + ', key ' + e_cur_key + ': ' + str(val1) + ' != ' + str(val2))
            return eq

        for orig in original_collection:
            new = new_collection.find(name=orig['name'])
            self.assertFalse(
                False in [vals_eq(orig['name'], e_cur_key, orig[e_cur_key], new[e_cur_key]) for e_cur_key in
                          orig.attributes().keys()])

    def _check_cloned_network(self, subnet_suid, base_suid, base_name, base_nodes, base_edges):
        self.assertIsInstance(subnet_suid, int)
        self.assertNotEqual(base_suid, subnet_suid)
        self.assertEqual(get_node_count(subnet_suid), base_nodes)
        self.assertEqual(get_edge_count(subnet_suid), base_edges)
        self.assertIn(base_name, get_network_name(subnet_suid))


if __name__ == '__main__':
    unittest.main()
