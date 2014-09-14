.. image:: https://travis-ci.org/ropez/pytest-describe.svg?branch=master
    :target: https://travis-ci.org/ropez/pytest-describe

Describe-style plugin for py.test
=================================

pytest-describe is a plugin for py.test that allows tests to be written in
arbitrary nested describe-blocks, similar to RSpec (Ruby) and Jasmine
(JavaScript).

The main inspiration for this was a `video
<https://www.youtube.com/watch?v=JJle8L8FRy0>`_ by Gary Bernhardt.

Example
-------

.. code-block:: python

    def describe_list():

        @pytest.fixture
        def list():
            return []

        def describe_append():

            def adds_to_end_of_list(list):
                list.append('foo')
                list.append('bar')
                assert list == ['foo', 'bar']

        def describe_remove():

            @pytest.fixture
            def list():
                return ['foo', 'bar']

            def removes_item_from_list(list):
                list.remove('foo')
                assert list == ['bar']
