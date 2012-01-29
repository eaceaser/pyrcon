import unittest
import proxy
from mock import patch

class ProxyTest(unittest.TestCase):
  @patch('control.Control')
  def test_proxy(self, MockControl):
    p = proxy.Proxy(MockControl())


if __name__ == '__main__':
  unittest.main()