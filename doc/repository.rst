####################
Repository reference
####################

.. toctree::
    :hidden:

A blockwart repository contains everything you need to contruct the configuration for your systems.

This page describes the various subdirectories and files than can exist inside a repo.

``nodes.py``
==============

This file tells blockwart what nodes (servers, VMs, ...) there are in your environment and lets you configure options such as hostnames and SSH usernames.

.. seealso:: :ref:`nodespy`

``groups.py``
==============

This file allows you to organize your nodes into groups.

.. seealso:: :ref:`groupspy`

``items/``
==========

This optional subdirectory contains the code for your custom item types.

.. seealso:: :ref:`dev_item`