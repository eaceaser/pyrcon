import unittest
import proxy
from control import Control
from server import TestServer
from bfserver import BFServer
from proxy import Proxy

class ProxyTest(unittest.TestCase):
  server = TestServer()
  client = BFServer("localhost", 28260, "test")
  control = Control(client, "test", None, None)
#  proxy = self.Proxy(control)

  def test_version(self):
    self.assertEqual(self.client.version().get(), "TestServer 1")

  def test_serverinfo(self):
    dict = self.client.info().get()
    self.assertDictEqual(dict, {
      'punkbuster_version': '1.0',
      'current_round': 1,
      'has_password': 'False',
      'game_mode': 'testmode0',
      'has_punkbuster': 'True',
      'join_queue_enabled': 'False',
      'ping_site': 'SF',
      'target_scores': 200,
      'server_name': 'testServer',
      'team_scores': [200,200],
      'server_uptime': 1234,
      'is_ranked': 'True',
      'join_address': '',
      'round_time': 200,
      'online_state': '',
      'max_players': 16,
      'num_teams': 2,
      'player_count': 1,
      'country': 'US',
      'region': 'US',
      'total_rounds': '2',
      'map_name': 'MP_Test'
    })

  def test_next_round(self):
    self.client.next_round().get()
    self.assertEqual(self.server.last_command, "next_round")

  def test_restart_round(self):
    self.client.restart_round().get()
    self.assertEqual(self.server.last_command, "restart_round")

  def test_end_round(self):
    self.client.end_round(1).get()
    self.assertEqual(self.server.last_command, "end_round 1")

  def test_list_maps(self):
    maps = self.client.list_maps().get()
    self.assertDictEqual(maps, {
      'maps': [{'num_rounds': '2', 'name': 'MP_Test1', 'mode': 'TestMode0'}, {'name': 'MP_Test2', 'mode': 'TestMode1', 'num_rounds': '5'}]
    })

  def test_get_map_indices(self):
    idx = self.client.get_map_indices().get()
    self.assertListEqual(idx, ["0", "1"])

  def test_add_map(self):
    self.client.add_map("MP_Test3", "TestMode2", 3).get()
    self.assertEqual(self.server.last_command, "add_map MP_Test3 TestMode2 3")

  def test_set_next_map(self):
    self.client.set_next_map(3).get()
    self.assertEqual(self.server.last_command, "set_next_map 3")

  def test_clear_map_list(self):
    self.client.clear_map_list().get()
    self.assertEqual(self.server.last_command, "clear_map_list")

  def test_save_map_list(self):
    self.client.save_map_list().get()
    self.assertEqual(self.server.last_command, "save_map_list")

  def test_remove_map(self):
    self.client.remove_map(10).get()
    self.assertEqual(self.server.last_command, "remove_map 10")

  def test_list_all_players(self):
    plist = self.client.list_all_players().get()
    self.assertDictEqual(plist, {
      'fields': ['field1', 'field2', 'field3'],
      'players': [['what', 'the', 'crap']]
    })

  def test_kick_player(self):
    self.client.kick_player("testplayer", "no reason").get()
    self.assertEqual(self.server.last_command, "kick_player testplayer no reason")

  def test_kill_player(self):
    self.client.kill_player("testplayer").get()
    self.assertEqual(self.server.last_command, "kill_player testplayer")

  def test_add_ban(self):
    self.client.add_ban("guid", "abcd-efg", "5", "no good reason").get()
    self.assertEqual(self.server.last_command, "add_ban guid abcd-efg 5 no good reason")

  def test_list_bans(self):
    bans = self.client.list_bans().get()
    self.assertListEqual(bans, [{
      'reason': 'no reason', 'time': '100', 'id_type': 'guid', 'ban_type':'forever', 'id': 'random-id'
    }])

  def test_say_all(self):
    self.client.say_all("grrr").get()
    self.assertEqual(self.server.last_command, "say all grrr")

if __name__ == '__main__':
  unittest.main()