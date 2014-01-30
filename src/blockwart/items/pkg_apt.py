# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from pipes import quote

from blockwart.exceptions import BundleError
from blockwart.items import Item, ItemStatus
from blockwart.utils.text import bold, green, red
from blockwart.utils.text import mark_for_translation as _


def pkg_install(node, pkgname):
    return node.run("apt-get -qy --no-install-recommends "
                    "install {}".format(quote(pkgname)))


def pkg_installed(node, pkgname):
    result = node.run(
        "dpkg -s {} | grep '^Status: '".format(quote(pkgname)),
        may_fail=True,
    )
    if result.return_code != 0 or " installed" not in result.stdout:
        return False
    else:
        return True


def pkg_remove(node, pkgname):
    return node.run("apt-get -qy purge {}".format(quote(pkgname)))


class AptPkg(Item):
    """
    A package installed by apt.
    """
    BUNDLE_ATTRIBUTE_NAME = "pkg_apt"
    DEPENDS_STATIC = []
    ITEM_ATTRIBUTES = {
        'installed': True,
    }
    ITEM_TYPE_NAME = "pkg_apt"
    PARALLEL_APPLY = False

    def __repr__(self):
        return "<AptPkg name:{} installed:{}>".format(
            self.name,
            self.attributes['installed'],
        )

    def ask(self, status):
        before = _("installed") if status.info['installed'] \
            else _("not installed")
        after = green(_("installed")) if self.attributes['installed'] \
            else red(_("not installed"))
        return "{} {} → {}\n".format(
            bold(_("status")),
            before,
            after,
        )

    def fix(self, status):
        if self.attributes['installed'] is False:
            pkg_remove(self.node, self.name)
        else:
            pkg_install(self.node, self.name)

    def get_status(self):
        install_status = pkg_installed(self.node, self.name)
        item_status = (install_status == self.attributes['installed'])
        return ItemStatus(
            correct=item_status,
            info={'installed': install_status},
        )

    def validate_attributes(self, attributes):
        if not isinstance(attributes.get('installed', True), bool):
            raise BundleError("expected boolean for 'installed' on {}".format(
                self.id,
            ))