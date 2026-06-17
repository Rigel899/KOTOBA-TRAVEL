import unittest

from src.core.app_state import GUEST_USERNAME, clear_user, get_current_user, set_user
from src.main import ROUTES, normalize_route, prepare_route_state, route_config_for


class RouterTests(unittest.TestCase):
    def test_normalize_route_treats_empty_values_as_login(self):
        self.assertEqual(normalize_route(""), "/")
        self.assertEqual(normalize_route("/"), "/")
        self.assertEqual(normalize_route(None), "/")
        self.assertEqual(normalize_route("dashboard"), "dashboard")

    def test_route_config_falls_back_to_dashboard_for_unknown_route(self):
        self.assertEqual(route_config_for("dashboard"), ROUTES["dashboard"])
        self.assertEqual(route_config_for("unknown"), ROUTES["dashboard"])
        with self.assertRaises(ValueError):
            route_config_for("/")

    def test_prepare_route_state_preserves_kwargs_for_app_routes(self):
        state = {"user": "utente"}

        route = prepare_route_state(state, "food", {"selected": "ramen"})

        self.assertEqual(route, "food")
        self.assertEqual(state["_route"], "food")
        self.assertEqual(state["selected"], "ramen")
        self.assertEqual(state["user"], "utente")

    def test_prepare_route_state_clears_session_for_login_route(self):
        state = {"user": "utente", "selected": "ramen"}
        set_user(state, "utente")

        route = prepare_route_state(state, "/", {"selected": "sushi"}, clear_session=clear_user)

        self.assertEqual(route, "/")
        self.assertEqual(state, {"_route": "/", "_app_window_ready": False})
        self.assertEqual(get_current_user(state), GUEST_USERNAME)


if __name__ == "__main__":
    unittest.main()
