from module import Module

class EventHandler(Module):
  def on_player_authenticated(self, name):
    pass

  def on_player_join(self, name, guid):
    pass

  def on_player_leave(self, name, info):
    pass

  def on_player_spawn(self, name, team):
    pass

  def on_player_kill(self, killer, killed, weapon, headshot):
    pass

  def on_player_chat(self, name, text):
    pass

  def on_player_squad_change(self, name, team, squad):
    pass

  def on_player_team_change(self, name, team, sqaud):
    pass

  def on_punkbuster_message(self, message):
    pass

  def on_level_loaded(self, name, gamemode, rounds_played, rounds_total):
    pass

  def on_round_over(self, winning_team):
    pass

  def on_round_over_team_scores(self, team_scores):
    pass
